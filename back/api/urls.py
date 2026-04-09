from django.urls import path
from .views import (
    register_view,
    login_view,
    logout_view,
    profile_view,
    WorkspaceListAPIView,
    WorkspaceMemberListCreateAPIView,
    CategoryListCreateAPIView,
    CategoryDetailAPIView,
    TaskListCreateAPIView,
    TaskDetailAPIView,
    SubTaskListCreateAPIView,
    SubTaskDetailAPIView,
    CommentListCreateAPIView,
    ActivityListAPIView,
    StatisticsAPIView,
)

urlpatterns = [
    path('register/', register_view),
    path('login/', login_view),
    path('logout/', logout_view),
    path('profile/', profile_view),

    path('workspaces/', WorkspaceListAPIView.as_view()),
    path('workspaces/<int:workspace_id>/members/', WorkspaceMemberListCreateAPIView.as_view()),

    path('categories/', CategoryListCreateAPIView.as_view()),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view()),

    path('tasks/', TaskListCreateAPIView.as_view()),
    path('tasks/<int:pk>/', TaskDetailAPIView.as_view()),

    path('subtasks/', SubTaskListCreateAPIView.as_view()),
    path('subtasks/<int:pk>/', SubTaskDetailAPIView.as_view()),

    path('comments/', CommentListCreateAPIView.as_view()),

    path('activities/', ActivityListAPIView.as_view()),
    path('statistics/', StatisticsAPIView.as_view()),
]