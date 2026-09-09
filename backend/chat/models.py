from django.db import models
from django.contrib.auth.models import User

class Conversation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="conversations")
    title = models.CharField(max_length=255, default="New Database Chat")
    title_edited = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.user.username}"

class Message(models.Model):
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    has_tool_calls = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.role.upper()}: {self.content[:30]}..."

class MessageToolCall(models.Model):
    """
    Stores intermediate ReAct steps (Tool Calls & Observations) 
    for audit, UI visualization, and deep context reconstruction.
    """
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name="tool_calls")
    tool_name = models.CharField(max_length=100)
    tool_args = models.JSONField()     # Stores arguments sent by the LLM
    tool_output = models.TextField()   # Stores the string returned by Python
    tool_call_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Tool: {self.tool_name} for Message {self.message.id}"

class GeneratedFile(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='generated_files')
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='generated_files')
    filename = models.CharField(max_length=255)
    extension = models.CharField(max_length=10)
    file_path = models.CharField(max_length=500)
    size_bytes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.filename} ({self.extension})"