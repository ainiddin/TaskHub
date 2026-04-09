from django.contrib import admin
from .models import Workspace, WorkspaceMember, Category, Task, SubTask, Comment, TaskActivity

admin.site.register(Workspace)
admin.site.register(WorkspaceMember)
admin.site.register(Category)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(Comment)
admin.site.register(TaskActivity)