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


class Task(models.Model):
    STATUS_CHOICES = (
        ('not_done', 'Not done'),
        ('done', 'Done'),
        ('overdue', 'Overdue'),
    )

    PRIORITY_CHOICES = (
        ('today', 'Today'),
        ('upcoming', 'Upcoming'),
        ('recurring', 'Recurring'),
    )

    REPEAT_CHOICES = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_done')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='upcoming')
    due_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Повторяющиеся таски
    is_recurring = models.BooleanField(default=False)
    repeat_type = models.CharField(max_length=20, choices=REPEAT_CHOICES, null=True, blank=True)
    # для custom: юзер сам задаёт интервал в днях
    repeat_every_days = models.PositiveIntegerField(null=True, blank=True)
    # дата следующего повтора (автоматически вычисляется при выполнении)
    next_occurrence = models.DateField(null=True, blank=True)

    # NULL = личный таск, указан = таск в воркспейсе
    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='tasks', null=True, blank=True)

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


class TaskActivity(models.Model):
    ACTION_CHOICES = (
        ('task_created', 'Task created'),
        ('task_completed', 'Task completed'),
        ('subtask_completed', 'Subtask completed'),
        ('task_overdue', 'Task overdue'),
        ('member_added', 'Member added'),
    )

    workspace = models.ForeignKey(Workspace, on_delete=models.CASCADE, related_name='activities', null=True, blank=True)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    subtask = models.ForeignKey(SubTask, on_delete=models.CASCADE, null=True, blank=True, related_name='activities')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='task_activities')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message


class UserStats(models.Model):
    """
    Снапшот статистики юзера за произвольный период.
    Создаётся при каждом запросе статистики или по расписанию.
    """
    PERIOD_CHOICES = (
        ('3days', 'Last 3 days'),
        ('week', 'Last week'),
        ('month', 'Last month'),
        ('custom', 'Custom range'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stats')
    period = models.CharField(max_length=20, choices=PERIOD_CHOICES)
    # для custom период
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)

    total_tasks = models.PositiveIntegerField(default=0)
    completed_tasks = models.PositiveIntegerField(default=0)
    overdue_tasks = models.PositiveIntegerField(default=0)
    recurring_tasks = models.PositiveIntegerField(default=0)

    # сколько было создано задач в этот период
    created_tasks = models.PositiveIntegerField(default=0)

    calculated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-calculated_at']

    def __str__(self):
        return f'{self.user.username} stats ({self.period})'
