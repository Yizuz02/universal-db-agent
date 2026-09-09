from collections import OrderedDict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.utils import timezone
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404

from .models import Conversation


class UserLoginView(LoginView):
    template_name = "chat/login.html"
    redirect_authenticated_user = True


class ChatView(LoginRequiredMixin, TemplateView):

    template_name = "chat/chat.html"

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        user = self.request.user

        conversation_id = self.kwargs.get("conversation_id")

        # -------------------------------------------------
        # Determine selected conversation
        # -------------------------------------------------

        if conversation_id is not None:

            selected = get_object_or_404(
                Conversation,
                id=conversation_id,
                user=user,
            )

            self.request.session["selected_conversation"] = selected.id

        else:

            selected_id = self.request.session.get("selected_conversation")

            if selected_id:

                try:

                    selected = Conversation.objects.get(
                        id=selected_id,
                        user=user,
                    )

                except Conversation.DoesNotExist:

                    selected = None

            else:

                selected = None

            if selected is None:

                selected = Conversation.objects.create(
                    user=user,
                    title="New Database Chat",
                )

                self.request.session["selected_conversation"] = selected.id

        # -------------------------------------------------
        # Sidebar conversations
        # -------------------------------------------------

        conversations = (
            Conversation.objects
            .filter(user=user)
            .order_by("-updated_at")
        )

        grouped = OrderedDict()

        today = timezone.localdate()

        for conversation in conversations:

            date = conversation.updated_at.date()

            if date == today:
                label = "Today"

            elif (today - date).days == 1:
                label = "Yesterday"

            elif (today - date).days < 7:
                label = "Last 7 Days"

            else:
                label = date.strftime("%B %Y")

            grouped.setdefault(label, []).append(conversation)

        context["conversation_groups"] = grouped

        context["selected_conversation"] = selected

        context["messages"] = (
            selected.messages
            .select_related()
            .prefetch_related("tool_calls")
            .order_by("created_at")
        )

        return context