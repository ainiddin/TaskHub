from django.contrib import admin
from .models import Workspace, WorkspaceMember, Task, SubTask, TaskActivity, UserStats

admin.site.register(Workspace)
admin.site.register(WorkspaceMember)
admin.site.register(Task)
admin.site.register(SubTask)
admin.site.register(TaskActivity)
admin.site.register(UserStats)
