from django.urls import path
from .views import (
    register_view, login_view, logout_view, profile_view,
    WorkspaceListCreateAPIView,
    WorkspaceDetailAPIView,
    WorkspaceMemberListCreateAPIView,
    TaskListCreateAPIView, TaskDetailAPIView,
    SubTaskListCreateAPIView, SubTaskDetailAPIView,
    ActivityListAPIView,
    StatisticsAPIView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('register/', register_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('profile/', profile_view),

    path('workspaces/', WorkspaceListCreateAPIView.as_view()),
    path('workspaces/<int:pk>/', WorkspaceDetailAPIView.as_view()),
    path('workspaces/<int:workspace_id>/members/', WorkspaceMemberListCreateAPIView.as_view()),

    path('tasks/', TaskListCreateAPIView.as_view()),
    path('tasks/<int:pk>/', TaskDetailAPIView.as_view()),

    path('subtasks/', SubTaskListCreateAPIView.as_view()),
    path('subtasks/<int:pk>/', SubTaskDetailAPIView.as_view()),

    path('activities/', ActivityListAPIView.as_view()),
    path('statistics/', StatisticsAPIView.as_view()),

    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),]
