from django.db import models
from django.contrib.auth.models import User


class Workspace(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_workspaces')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class WorkspaceMember(models.Model):
    ROLE_CHOICES = (
        ('owner', 'Owner'),
        ('admin', 'Admin'),
        ('member', 'Member'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workspace_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='added_workspace_members')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('workspace', 'user')

    def __str__(self):
        return f'{self.user.username} in {self.workspace.name}'


class Category(models.Model):
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=30, default='gray')
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='categories')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_categories')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Task(models.Model):
    STATUS_CHOICES = (
        ('not_done', 'Not done'),
        ('done', 'Done'),
        ('overdue', 'Overdue'),
    )

    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_done')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tasks')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tasks')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_tasks')
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.title


class SubTask(models.Model):
    STATUS_CHOICES = (
        ('not_done', 'Not done'),
        ('done', 'Done'),
    )

    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_done')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_subtasks')
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='completed_subtasks')
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Comment(models.Model):
    text = models.TextField()
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Comment by {self.author.username}'


class TaskActivity(models.Model):
    ACTION_CHOICES = (
        ('task_created', 'Task created'),
        ('task_completed', 'Task completed'),
        ('subtask_completed', 'Subtask completed'),
        ('task_overdue', 'Task overdue'),
        ('member_added', 'Member added'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='activities')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    subtask = models.ForeignKey(SubTask, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message