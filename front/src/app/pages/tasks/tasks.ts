import {
  Component,
  OnInit,
  Input,
  OnChanges,
  SimpleChanges,
  signal,
  ChangeDetectorRef,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { TaskService } from '../../services/task';
import { SubtaskService } from '../../services/subtask';

interface TaskForm {
  title: string;
  description: string;
  priority: string;
  due_date: string;
  is_recurring: boolean;
  repeat_type: string;
}

@Component({
  selector: 'app-tasks',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './tasks.html',
  styleUrl: './tasks.css',
})
export class Tasks implements OnInit, OnChanges {
  @Input() workspaceIdInput: number | null = null;
  overdueAlertTasks = signal<any[]>([]);
  showOverdueAlert = signal(false);
  tasks = signal<any[]>([]);
  loading = signal(false);
  saving = signal(false);
  showForm = signal(false);
  editingTask = signal<any>(null);
  selectedTask = signal<any>(null);
  newSubtaskTitle = signal('');
  workspaceId: number | null = null;
  statusFilter = '';
  priorityFilter = '';

  form = signal<TaskForm>({
    title: '',
    description: '',
    priority: 'upcoming',
    due_date: '',
    is_recurring: false,
    repeat_type: 'daily',
  });

  constructor(
    private taskService: TaskService,
    private subtaskService: SubtaskService,
    private route: ActivatedRoute,
    private cdr: ChangeDetectorRef,
  ) {}

  ngOnInit() {
    if (this.workspaceIdInput) {
      this.workspaceId = this.workspaceIdInput;
      this.loadTasks();
    } else {
      this.route.queryParams.subscribe((params) => {
        this.statusFilter = params['status'] || '';
        this.priorityFilter = params['priority'] || '';
        this.loadTasks();
      });
    }
  }

  ngOnChanges(changes: SimpleChanges) {
    if (changes['workspaceIdInput'] && !changes['workspaceIdInput'].firstChange) {
      this.workspaceId = this.workspaceIdInput;
      this.showForm.set(false);
      this.editingTask.set(null);
      this.loadTasks();
    }
  }

  loadTasks() {
    this.loading.set(true);
    this.taskService.getTasks(this.workspaceId || undefined).subscribe({
      next: (data: any[]) => {
        let result = data;
        if (this.statusFilter) result = result.filter((t: any) => t.status === this.statusFilter);
        if (this.priorityFilter)
          result = result.filter((t: any) => t.priority === this.priorityFilter);
        this.tasks.set([...result]);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const overdue = result.filter((t: any) => {
          if (t.status === 'done') return false;
          if (!t.due_date) return false;
          const due = new Date(t.due_date);
          due.setHours(0, 0, 0, 0);
          return due < today;
        });

        if (overdue.length > 0) {
          this.overdueAlertTasks.set(overdue);
          this.showOverdueAlert.set(true);
        }
        const sel = this.selectedTask();
        if (sel) this.selectedTask.set(data.find((t: any) => t.id === sel.id) || null);
        const editing = this.editingTask();
        if (editing) this.editingTask.set(data.find((t: any) => t.id === editing.id) || null);
        this.loading.set(false);
        this.cdr.markForCheck();
      },
      error: () => {
        this.loading.set(false);
        this.cdr.markForCheck();
      },
    });
  }
  closeOverdueAlert() {
    this.showOverdueAlert.set(false);
  }
  openForm(task?: any) {
    if (task) {
      this.editingTask.set(task);
      this.selectedTask.set(task);
      this.form.set({
        title: task.title,
        description: task.description || '',
        priority: task.priority,
        due_date: task.due_date || '',
        is_recurring: task.is_recurring,
        repeat_type: task.repeat_type || 'daily',
      });
    } else {
      this.editingTask.set(null);
      this.selectedTask.set(null);
      this.form.set({
        title: '',
        description: '',
        priority: 'upcoming',
        due_date: '',
        is_recurring: false,
        repeat_type: 'daily',
      });
    }
    this.showForm.set(true);
  }

  updateTitle(v: string) {
    this.form.update((f) => ({ ...f, title: v }));
  }
  updateDescription(v: string) {
    this.form.update((f) => ({ ...f, description: v }));
  }
  updatePriority(v: string) {
    this.form.update((f) => ({ ...f, priority: v }));
  }
  updateDueDate(v: string) {
    this.form.update((f) => ({ ...f, due_date: v }));
  }
  updateIsRecurring(v: boolean) {
    this.form.update((f) => ({ ...f, is_recurring: v }));
  }
  updateRepeatType(v: string) {
    this.form.update((f) => ({ ...f, repeat_type: v }));
  }

  saveTask() {
    if (!this.form().title.trim() || this.saving()) return;
    this.saving.set(true);
    const data: any = { ...this.form() };
    if (!data.due_date) delete data.due_date;
    if (this.workspaceId) data.workspace = this.workspaceId;
    const req = this.editingTask()
      ? this.taskService.updateTask(this.editingTask().id, data)
      : this.taskService.createTask(data);
    req.subscribe({
      next: () => {
        this.showForm.set(false);
        this.saving.set(false);
        this.loadTasks();
      },
      error: (err: any) => {
        console.error(err);
        this.saving.set(false);
      },
    });
  }

  toggleStatus(task: any) {
    const newStatus = task.status === 'done' ? 'not_done' : 'done';
    this.taskService.updateTask(task.id, { status: newStatus }).subscribe({
      next: () => this.loadTasks(),
    });
  }

  deleteTask(id: number) {
    this.taskService.deleteTask(id).subscribe({
      next: () => {
        this.showForm.set(false);
        this.loadTasks();
      },
    });
  }

  addSubtask() {
    if (!this.newSubtaskTitle().trim() || !this.editingTask()) return;
    this.subtaskService
      .createSubtask({
        task: this.editingTask().id,
        title: this.newSubtaskTitle().trim(),
      })
      .subscribe({
        next: () => {
          this.newSubtaskTitle.set('');
          this.loadTasks();
        },
      });
  }

  toggleSubtask(subtask: any) {
    const newStatus = subtask.status === 'done' ? 'not_done' : 'done';
    this.subtaskService.updateSubtask(subtask.id, { status: newStatus }).subscribe({
      next: () => this.loadTasks(),
    });
  }

  deleteSubtask(id: number) {
    this.subtaskService.deleteSubtask(id).subscribe({
      next: () => this.loadTasks(),
    });
  }

  getTitle(): string {
    if (this.workspaceId) return 'Workspace Tasks';
    if (this.priorityFilter === 'today') return 'Today';
    if (this.priorityFilter === 'upcoming') return 'Upcoming';
    if (this.statusFilter === 'done') return 'Completed';
    if (this.statusFilter === 'overdue') return 'Overdue';
    return 'My Tasks';
  }

  doneSubtasks(task: any): number {
    return task.subtasks?.filter((s: any) => s.status === 'done').length || 0;
  }
}
