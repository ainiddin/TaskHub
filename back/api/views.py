from datetime import date
from django.contrib.auth.models import User
from django.db.models import Count, Q
from django.utils import timezone

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    Workspace,
    WorkspaceMember,
    Category,
    Task,
    SubTask,
    Comment,
    TaskActivity,
)
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    WorkspaceSerializer,
    WorkspaceMemberSerializer,
    CategorySerializer,
    TaskSerializer,
    SubTaskSerializer,
    CommentSerializer,
    TaskActivitySerializer,
)


def is_workspace_admin(user, workspace):
    return WorkspaceMember.objects.filter(
        workspace=workspace,
        user=user,
        role__in=['owner', 'admin']
    ).exists()


def is_workspace_member(user, workspace):
    return WorkspaceMember.objects.filter(
        workspace=workspace,
        user=user
    ).exists()


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

        WorkspaceMember.objects.create(
            workspace=workspace,
            user=user,
            role='owner',
            added_by=user
        )

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
    return Response({'message': 'Logout successful'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    workspaces = WorkspaceMember.objects.filter(user=request.user)
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
        'workspace_count': workspaces.count()
    })


class WorkspaceListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        memberships = WorkspaceMember.objects.filter(user=request.user)
        workspace_ids = memberships.values_list('workspace_id', flat=True)
        workspaces = Workspace.objects.filter(id__in=workspace_ids)
        serializer = WorkspaceSerializer(workspaces, many=True)
        return Response(serializer.data)


class WorkspaceMemberListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        try:
            workspace = Workspace.objects.get(pk=workspace_id)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)

        if not is_workspace_member(request.user, workspace):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        members = WorkspaceMember.objects.filter(workspace=workspace)
        serializer = WorkspaceMemberSerializer(members, many=True)
        return Response(serializer.data)

    def post(self, request, workspace_id):
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

        member = WorkspaceMember.objects.create(
            workspace=workspace,
            user=user_to_add,
            role=role,
            added_by=request.user
        )

        TaskActivity.objects.create(
            workspace=workspace,
            user=request.user,
            action='member_added',
            message=f'{request.user.username} added {user_to_add.username} to workspace'
        )

        serializer = WorkspaceMemberSerializer(member)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class CategoryListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_id = request.GET.get('workspace')
        categories = Category.objects.filter(workspace__memberships__user=request.user).distinct()

        if workspace_id:
            categories = categories.filter(workspace_id=workspace_id)

        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    def post(self, request):
        workspace_id = request.data.get('workspace')

        try:
            workspace = Workspace.objects.get(pk=workspace_id)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)

        if not is_workspace_member(request.user, workspace):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Category.objects.get(pk=pk, workspace__memberships__user=user)
        except Category.DoesNotExist:
            return None

    def get(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category)
        return Response(serializer.data)

    def put(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=category.created_by)
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        category = self.get_object(pk, request.user)
        if not category:
            return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response({'message': 'Category deleted'}, status=status.HTTP_204_NO_CONTENT)


class TaskListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        tasks = Task.objects.filter(workspace__memberships__user=request.user).distinct()

        workspace_id = request.GET.get('workspace')
        category_id = request.GET.get('category')
        status_filter = request.GET.get('status')
        search = request.GET.get('search')

        if workspace_id:
            tasks = tasks.filter(workspace_id=workspace_id)

        if category_id:
            tasks = tasks.filter(category_id=category_id)

        if status_filter:
            tasks = tasks.filter(status=status_filter)

        if search:
            tasks = tasks.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        serializer = TaskSerializer(tasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        workspace_id = request.data.get('workspace')

        try:
            workspace = Workspace.objects.get(pk=workspace_id)
        except Workspace.DoesNotExist:
            return Response({'error': 'Workspace not found'}, status=status.HTTP_404_NOT_FOUND)

        if not is_workspace_member(request.user, workspace):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)

        serializer = TaskSerializer(data=request.data)
        if serializer.is_valid():
            task = serializer.save(created_by=request.user)

            TaskActivity.objects.create(
                workspace=workspace,
                task=task,
                user=request.user,
                action='task_created',
                message=f'{request.user.username} created task "{task.title}"'
            )

            return Response(TaskSerializer(task).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TaskDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return Task.objects.get(pk=pk, workspace__memberships__user=user)
        except Task.DoesNotExist:
            return None

    def get(self, request, pk):
        task = self.get_object(pk, request.user)
        if not task:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        if task.due_date and task.due_date < date.today() and task.status != 'done':
            task.status = 'overdue'
            task.save()

        serializer = TaskSerializer(task)
        return Response(serializer.data)

    def put(self, request, pk):
        task = self.get_object(pk, request.user)
        if not task:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')

        if new_status == 'done' and task.subtasks.filter(status='not_done').exists():
            return Response(
                {'error': 'Finish all subtasks before completing the task'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TaskSerializer(task, data=request.data)
        if serializer.is_valid():
            updated_task = serializer.save(created_by=task.created_by)

            if updated_task.status == 'done':
                updated_task.completed_by = request.user
                updated_task.completed_at = timezone.now()
                updated_task.save()

                TaskActivity.objects.create(
                    workspace=updated_task.workspace,
                    task=updated_task,
                    user=request.user,
                    action='task_completed',
                    message=f'{request.user.username} completed task "{updated_task.title}"'
                )

            return Response(TaskSerializer(updated_task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        task = self.get_object(pk, request.user)
        if not task:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)

        new_status = request.data.get('status')

        if new_status == 'done' and task.subtasks.filter(status='not_done').exists():
            return Response(
                {'error': 'Finish all subtasks before completing the task'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = TaskSerializer(task, data=request.data, partial=True)
        if serializer.is_valid():
            updated_task = serializer.save()

            if updated_task.due_date and updated_task.due_date < date.today() and updated_task.status != 'done':
                updated_task.status = 'overdue'
                updated_task.save()

            if new_status == 'done':
                updated_task.completed_by = request.user
                updated_task.completed_at = timezone.now()
                updated_task.save()

                TaskActivity.objects.create(
                    workspace=updated_task.workspace,
                    task=updated_task,
                    user=request.user,
                    action='task_completed',
                    message=f'{request.user.username} completed task "{updated_task.title}"'
                )

            return Response(TaskSerializer(updated_task).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        task = self.get_object(pk, request.user)
        if not task:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        task.delete()
        return Response({'message': 'Task deleted'}, status=status.HTTP_204_NO_CONTENT)


class SubTaskListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        task_id = request.GET.get('task')
        subtasks = SubTask.objects.filter(task__workspace__memberships__user=request.user).distinct()

        if task_id:
            subtasks = subtasks.filter(task_id=task_id)

        serializer = SubTaskSerializer(subtasks, many=True)
        return Response(serializer.data)

    def post(self, request):
        task_id = request.data.get('task')

        try:
            task = Task.objects.get(pk=task_id, workspace__memberships__user=request.user)
        except Task.DoesNotExist:
            return Response({'error': 'Task not found or access denied'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubTaskSerializer(data=request.data)
        if serializer.is_valid():
            subtask = serializer.save(created_by=request.user)
            return Response(SubTaskSerializer(subtask).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SubTaskDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            return SubTask.objects.get(pk=pk, task__workspace__memberships__user=user)
        except SubTask.DoesNotExist:
            return None

    def patch(self, request, pk):
        subtask = self.get_object(pk, request.user)
        if not subtask:
            return Response({'error': 'Subtask not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = SubTaskSerializer(subtask, data=request.data, partial=True)
        if serializer.is_valid():
            updated_subtask = serializer.save()

            if request.data.get('status') == 'done':
                updated_subtask.completed_by = request.user
                updated_subtask.completed_at = timezone.now()
                updated_subtask.save()

                TaskActivity.objects.create(
                    workspace=updated_subtask.task.workspace,
                    task=updated_subtask.task,
                    subtask=updated_subtask,
                    user=request.user,
                    action='subtask_completed',
                    message=f'{request.user.username} completed subtask "{updated_subtask.title}"'
                )

            return Response(SubTaskSerializer(updated_subtask).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentListCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        task_id = request.GET.get('task')
        comments = Comment.objects.filter(task__workspace__memberships__user=request.user).distinct()

        if task_id:
            comments = comments.filter(task_id=task_id)

        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = CommentSerializer(data=request.data)
        if serializer.is_valid():
            comment = serializer.save(author=request.user)
            return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ActivityListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_id = request.GET.get('workspace')
        activities = TaskActivity.objects.filter(workspace__memberships__user=request.user).distinct()

        if workspace_id:
            activities = activities.filter(workspace_id=workspace_id)

        serializer = TaskActivitySerializer(activities.order_by('-created_at'), many=True)
        return Response(serializer.data)


class StatisticsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        workspace_id = request.GET.get('workspace')

        tasks = Task.objects.filter(workspace__memberships__user=request.user).distinct()
        subtasks = SubTask.objects.filter(task__workspace__memberships__user=request.user).distinct()

        if workspace_id:
            tasks = tasks.filter(workspace_id=workspace_id)
            subtasks = subtasks.filter(task__workspace_id=workspace_id)

        data = {
            'total_tasks': tasks.count(),
            'done_tasks': tasks.filter(status='done').count(),
            'not_done_tasks': tasks.filter(status='not_done').count(),
            'overdue_tasks': tasks.filter(
                Q(status='overdue') | Q(due_date__lt=date.today(), status='not_done')
            ).count(),
            'total_subtasks': subtasks.count(),
            'done_subtasks': subtasks.filter(status='done').count(),
            'tasks_by_category': list(
                tasks.values('category__name').annotate(count=Count('id')).order_by('-count')
            )
        }
        return Response(data)