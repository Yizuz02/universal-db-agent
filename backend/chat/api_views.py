import csv
import os
from io import StringIO

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from django.http import FileResponse, Http404

from .models import Conversation, GeneratedFile
from .serializers import (
    ConversationSerializer,
    ConversationSummarySerializer,
    GeneratedFileSerializer,
    MessageInputSerializer,
    TitleUpdateSerializer,
)
from .services import execute_agent_and_save_workflow

REPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reports/markdown"))


class ConversationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        conversations = Conversation.objects.filter(user=request.user).order_by("-updated_at")
        return Response(ConversationSummarySerializer(conversations, many=True).data)

    def post(self, request):
        title = request.data.get("title") or "New Database Chat"
        conversation = Conversation.objects.create(user=request.user, title=title)
        return Response(
            ConversationSummarySerializer(conversation).data,
            status=status.HTTP_201_CREATED,
        )


class ConversationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def _get_conversation(self, conversation_id, user):
        try:
            return Conversation.objects.get(id=conversation_id, user=user)
        except Conversation.DoesNotExist:
            return None

    def get(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id, request.user)
        if conversation is None:
            return Response(
                {"error": "Conversation not found or unauthorized."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ConversationSerializer(conversation).data)

    def patch(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id, request.user)
        if conversation is None:
            return Response(
                {"error": "Conversation not found or unauthorized."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = TitleUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        conversation.title = serializer.validated_data['title']
        conversation.title_edited = True
        conversation.save(update_fields=['title', 'title_edited', 'updated_at'])
        return Response(ConversationSummarySerializer(conversation).data)

    def delete(self, request, conversation_id):
        conversation = self._get_conversation(conversation_id, request.user)
        if conversation is None:
            return Response(
                {"error": "Conversation not found or unauthorized."},
                status=status.HTTP_404_NOT_FOUND,
            )
        conversation.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProcessAgentMessageView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, conversation_id):
        # Ensure the conversation exists and belongs to the logged-in user
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response(
                {"error": "Conversation not found or unauthorized."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Validate incoming text input
        serializer = MessageInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_text = serializer.validated_data['content']

        # Delegate the orchestration to our robust service layer
        try:
            final_reply, new_title, file_ids = execute_agent_and_save_workflow(conversation, user_text)
            response_data = {"agent_response": final_reply}
            if new_title:
                response_data["title"] = new_title
            if file_ids:
                files_qs = GeneratedFile.objects.filter(id__in=file_ids)
                response_data["files"] = GeneratedFileSerializer(files_qs, many=True).data
            else:
                response_data["files"] = []
            return Response(response_data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Failed to execute agent: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ViewMarkdownReportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, filename):
        # 1. Clean the filename to remove any path injection attempts (e.g. ../../)
        safe_filename = os.path.basename(filename)
        
        # 2. Construct the absolute target path
        file_path = os.path.abspath(os.path.join(REPORTS_DIR, safe_filename))
        
        # 3. Security Guardrail: Check if the file is strictly inside the allowed directory
        if not file_path.startswith(REPORTS_DIR):
            raise Http404("Unauthorized file access attempt.")
            
        if os.path.exists(file_path) and file_path.endswith('.md'):
            # Returns the file so your frontend can read it and render it as text/html
            return FileResponse(open(file_path, 'rb'), content_type='text/markdown')
            
        raise Http404("Report file not found.")


CSV_EXPORTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../reports/csv"))


class ViewCSVExportView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, filename):
        safe_filename = os.path.basename(filename)
        file_path = os.path.abspath(os.path.join(CSV_EXPORTS_DIR, safe_filename))

        if not file_path.startswith(CSV_EXPORTS_DIR):
            raise Http404("Unauthorized file access attempt.")

        if os.path.exists(file_path) and file_path.endswith('.csv'):
            return FileResponse(open(file_path, 'rb'), content_type='text/csv')

        raise Http404("CSV export file not found or invalid extension.")


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            gf = GeneratedFile.objects.select_related('conversation').get(id=file_id)
        except GeneratedFile.DoesNotExist:
            raise Http404("File not found.")
        if gf.conversation.user != request.user:
            raise Http404("File not found.")
        if not os.path.exists(gf.file_path):
            raise Http404("File missing from disk.")
        return FileResponse(open(gf.file_path, 'rb'), as_attachment=True, filename=gf.filename)


class FilePreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        try:
            gf = GeneratedFile.objects.select_related('conversation').get(id=file_id)
        except GeneratedFile.DoesNotExist:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
        if gf.conversation.user != request.user:
            return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)

        ext = gf.extension.lower()

        if ext == 'md':
            try:
                with open(gf.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception:
                return Response({"error": "File missing from disk."}, status=status.HTTP_404_NOT_FOUND)
            return Response({"type": "markdown", "content": content})

        elif ext == 'csv':
            try:
                with open(gf.file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    rows = [row for row in reader]
                headers = rows[0] if rows else []
                data_rows = rows[1:] if len(rows) > 1 else []
                return Response({"type": "csv", "headers": headers, "rows": data_rows})
            except Exception:
                return Response({"error": "File missing from disk."}, status=status.HTTP_404_NOT_FOUND)

        elif ext == 'xlsx':
            import openpyxl
            from io import BytesIO
            try:
                with open(gf.file_path, 'rb') as f:
                    wb = openpyxl.load_workbook(BytesIO(f.read()), read_only=True)
                ws = wb.active
                all_rows = [[str(cell.value) if cell.value is not None else '' for cell in row] for row in ws.iter_rows()]
                wb.close()
                headers = all_rows[0] if all_rows else []
                data_rows = all_rows[1:] if len(all_rows) > 1 else []
                return Response({"type": "excel", "headers": headers, "rows": data_rows})
            except Exception:
                return Response({"error": "File missing from disk."}, status=status.HTTP_404_NOT_FOUND)

        else:
            return Response({"error": "Unsupported file type for preview."}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)
