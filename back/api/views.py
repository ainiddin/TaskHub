from datetime import date, timedelta
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Workspace, WorkspaceMember, Task, SubTask, TaskActivity, UserStats
from .serializers import (
    RegisterSerializer, LoginSerializer,
    WorkspaceSerializer, WorkspaceMemberSerializer,
    TaskSerializer, SubTaskSerializer,
    TaskActivitySerializer, UserStatsSerializer,
)


def is_workspace_admin(user, workspace):
    return WorkspaceMember.objects.filter(workspace=workspace, user=user, role__in=['owner', 'admin']).exists()


def is_workspace_member(user, workspace):
    return WorkspaceMember.objects.filter(workspace=workspace, user=user).exists()


# ─── AUTH ─────────────────────────────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        workspace = Workspace.objects.create(
            name=f"{user.username}'s Workspace",
            description='Personal workspace',
            created_by=user
        )
        WorkspaceMember.objects.create(workspace=workspace, user=user, role='owner', added_by=user)
        return Response({
            'message': 'User created successfully',
            'username': user.username,
            'workspace_id': workspace.id
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username
        })
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    return Response({'message': 'Logout successful'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'workspace_count': WorkspaceMember.objects.filter(user=request.user).count()
    })


# ─── WORKSPACE ────────────────────────────────────────────────────────────────

class WorkspaceListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_ids = WorkspaceMember.objects.filter(user=self.request.user).values_list('workspace_id', flat=True)
        return Workspace.objects.filter(id__in=workspace_ids)

    def perform_create(self, serializer):
        workspace = serializer.save(created_by=self.request.user)
        WorkspaceMember.objects.create(workspace=workspace, user=self.request.user, role='owner', added_by=self.request.user)


class WorkspaceDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = WorkspaceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_ids = WorkspaceMember.objects.filter(user=self.request.user).values_list('workspace_id', flat=True)
        return Workspace.objects.filter(id__in=workspace_ids)

    def destroy(self, request, *args, **kwargs):
        workspace = self.get_object()
        if workspace.created_by != request.user:
            return Response({'error': 'Only owner can delete workspace'}, status=status.HTTP_403_FORBIDDEN)
        workspace.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class WorkspaceMemberListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = WorkspaceMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        workspace_id = self.kwargs['workspace_id']
        return WorkspaceMember.objects.filter(workspace_id=workspace_id)

    def create(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(pk=workspace_id)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)
        if not is_workspace_admin(request.user, workspace):
            return Response({'error': 'Only owner/admin can add members'}, status=status.HTTP_403_FORBIDDEN)
        username = request.data.get('username')
        role = request.data.get('role', 'member')
        try:
            user_to_add = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)
        if WorkspaceMember.objects.filter(workspace=workspace, user=user_to_add).exists():
            return Response({'error': 'User already in workspace'}, status=status.HTTP_400_BAD_REQUEST)
        member = WorkspaceMember.objects.create(workspace=workspace, user=user_to_add, role=role, added_by=request.user)
        TaskActivity.objects.create(
            workspace=workspace,
            user=request.user,
            action='member_added',
            message=f'{request.user.username} added {user_to_add.username} to workspace'
        )
        return Response(WorkspaceMemberSerializer(member).data, status=status.HTTP_201_CREATED)


# ─── TASK ─────────────────────────────────────────────────────────────────────

class TaskListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # сбрасываем recurring таски у которых пришло время
        Task.objects.filter(
            is_recurring=True,
            status='done',
            next_occurrence__lte=date.today()
        ).update(status='not_done')

        workspace_id = self.request.GET.get('workspace')
        if workspace_id is None or workspace_id == '':
            qs = Task.objects.filter(created_by=self.request.user, workspace__isnull=True)
        else:
            qs = Task.objects.filter(
                workspace_id=workspace_id,
                workspace__memberships__user=self.request.user
            ).distinct()

        status_filter = self.request.GET.get('status')
        priority_filter = self.request.GET.get('priority')
        search = self.request.GET.get('search')

        if status_filter:
            qs = qs.filter(status=status_filter)
        if priority_filter:
            qs = qs.filter(priority=priority_filter)
        if search:
            qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
        return qs

    def perform_create(self, serializer):
        workspace_id = self.request.data.get('workspace')
        workspace = None
        if workspace_id:
            try:
                workspace = Workspace.objects.get(pk=workspace_id)
            except Workspace.DoesNotExist:
                pass
        task = serializer.save(created_by=self.request.user)
        if task.workspace:
            TaskActivity.objects.create(
                workspace=task.workspace,
                task=task,
                user=self.request.user,
                action='task_created',
                message=f'{self.request.user.username} created task "{task.title}"'
            )


class TaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(
            Q(created_by=self.request.user, workspace__isnull=True) |
            Q(workspace__memberships__user=self.request.user)
        ).distinct()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        new_status = request.data.get('status')

        if new_status == 'done' and instance.subtasks.filter(status='not_done').exists():
            raise ValidationError('Finish all subtasks before completing the task')

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        updated_task = serializer.save()

        if updated_task.due_date and updated_task.due_date < date.today() and updated_task.status != 'done':
            updated_task.status = 'overdue'
            updated_task.save()

        if new_status == 'done':
            updated_task.completed_by = request.user
            updated_task.completed_at = timezone.now()
            if updated_task.is_recurring:
                if updated_task.repeat_type == 'daily':
                    updated_task.next_occurrence = date.today() + timedelta(days=1)
                elif updated_task.repeat_type == 'weekly':
                    updated_task.next_occurrence = date.today() + timedelta(weeks=1)
                elif updated_task.repeat_type == 'monthly':
                    updated_task.next_occurrence = date.today() + timedelta(days=30)
                elif updated_task.repeat_type == 'custom' and updated_task.repeat_every_days:
                    updated_task.next_occurrence = date.today() + timedelta(days=updated_task.repeat_every_days)
            updated_task.save()
            if updated_task.workspace:
                TaskActivity.objects.create(
                    workspace=updated_task.workspace,
                    task=updated_task,
                    user=request.user,
                    action='task_completed',
                    message=f'{request.user.username} completed task "{updated_task.title}"'
                )

        return Response(self.get_serializer(updated_task).data)

    def perform_update(self, serializer):
        serializer.save()


# ─── SUBTASK ──────────────────────────────────────────────────────────────────

class SubTaskListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = SubTask.objects.filter(
            Q(task__created_by=self.request.user, task__workspace__isnull=True) |
            Q(task__workspace__memberships__user=self.request.user)
        ).distinct()
        task_id = self.request.GET.get('task')
        if task_id:
            qs = qs.filter(task_id=task_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class SubTaskDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = SubTaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SubTask.objects.filter(
            Q(task__created_by=self.request.user, task__workspace__isnull=True) |
            Q(task__workspace__memberships__user=self.request.user)
        ).distinct()

    def perform_update(self, serializer):
        updated_subtask = serializer.save()
        if self.request.data.get('status') == 'done':
            updated_subtask.completed_by = self.request.user
            updated_subtask.completed_at = timezone.now()
            updated_subtask.save()
            if updated_subtask.task.workspace:
                TaskActivity.objects.create(
                    workspace=updated_subtask.task.workspace,
                    task=updated_subtask.task,
                    subtask=updated_subtask,
                    user=self.request.user,
                    action='subtask_completed',
                    message=f'{self.request.user.username} completed subtask "{updated_subtask.title}"'
                )


# ─── ACTIVITY ─────────────────────────────────────────────────────────────────

class ActivityListAPIView(generics.ListAPIView):
    serializer_class = TaskActivitySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = TaskActivity.objects.filter(workspace__memberships__user=self.request.user).distinct()
        workspace_id = self.request.GET.get('workspace')
        if workspace_id:
            qs = qs.filter(workspace_id=workspace_id)
        return qs.order_by('-created_at')


# ─── STATISTICS ───────────────────────────────────────────────────────────────

class StatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.GET.get('period', 'week')
        date_from_param = request.GET.get('date_from')
        date_to_param = request.GET.get('date_to')
        today = date.today()

        if period == '3days':
            date_from, date_to = today - timedelta(days=3), today
        elif period == 'week':
            date_from, date_to = today - timedelta(weeks=1), today
        elif period == 'month':
            date_from, date_to = today - timedelta(days=30), today
        elif period == 'custom' and date_from_param and date_to_param:
            date_from = date.fromisoformat(date_from_param)
            date_to = date.fromisoformat(date_to_param)
        else:
            date_from, date_to = today - timedelta(weeks=1), today

        all_tasks = Task.objects.filter(
            Q(created_by=request.user, workspace__isnull=True) |
            Q(workspace__memberships__user=request.user)
        ).distinct()

        period_tasks = all_tasks.filter(created_at__date__gte=date_from, created_at__date__lte=date_to)

        data = {
            'period': period,
            'date_from': str(date_from),
            'date_to': str(date_to),
            'total_tasks': period_tasks.count(),
            'completed_tasks': period_tasks.filter(status='done').count(),
            'overdue_tasks': period_tasks.filter(Q(status='overdue') | Q(due_date__lt=today, status='not_done')).count(),
            'recurring_tasks': period_tasks.filter(is_recurring=True).count(),
            'today_tasks': all_tasks.filter(priority='today').count(),
            'upcoming_tasks': all_tasks.filter(priority='upcoming').count(),
        }

        UserStats.objects.create(
            user=request.user,
            period=period if period in ['3days', 'week', 'month', 'custom'] else 'week',
            date_from=date_from,
            date_to=date_to,
            total_tasks=data['total_tasks'],
            completed_tasks=data['completed_tasks'],
            overdue_tasks=data['overdue_tasks'],
            recurring_tasks=data['recurring_tasks'],
            created_tasks=data['total_tasks'],
        )

        return Response(data)
