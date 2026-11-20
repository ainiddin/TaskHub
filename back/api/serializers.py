from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from .models import Workspace, WorkspaceMember, Task, SubTask, TaskActivity, UserStats


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False,allow_blank=True)

    # R-03: a plain Serializer does not check uniqueness (-> HTTP 500) or the configured password validators
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(list(error.messages))
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data.get('email', '')
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError('Invalid username or password')
        attrs['user'] = user
        return attrs


class WorkspaceSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')

    class Meta:
        model = Workspace
        fields = '__all__'


class WorkspaceMemberSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    added_by_username = serializers.ReadOnlyField(source='added_by.username')

    class Meta:
        model = WorkspaceMember
        fields = '__all__'


class SubTaskSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    completed_by = serializers.ReadOnlyField(source='completed_by.username')

    class Meta:
        model = SubTask
        fields = '__all__'

    # R-01: a client-supplied `task` id must point to a task the requesting user can access
    def validate_task(self, task):
        user = self.context['request'].user
        if task.workspace_id is None:
            allowed = task.created_by_id == user.id
        else:
            allowed = WorkspaceMember.objects.filter(workspace_id=task.workspace_id, user=user).exists()
        if not allowed:
            raise serializers.ValidationError('You do not have access to this task.')
        return task


class TaskSerializer(serializers.ModelSerializer):
    created_by = serializers.ReadOnlyField(source='created_by.username')
    completed_by = serializers.ReadOnlyField(source='completed_by.username')
    subtasks = SubTaskSerializer(many=True, read_only=True)

    class Meta:
        model = Task
        fields = '__all__'

    # R-01: a client-supplied `workspace` id must be a workspace the requesting user belongs to
    def validate_workspace(self, workspace):
        if workspace is None:
            return workspace
        user = self.context['request'].user
        if not WorkspaceMember.objects.filter(workspace=workspace, user=user).exists():
            raise serializers.ValidationError('You are not a member of this workspace.')
        return workspace


class TaskActivitySerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = TaskActivity
        fields = '__all__'


class UserStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserStats
        fields = '__all__'
