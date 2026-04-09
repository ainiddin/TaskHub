import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';
import { TaskService } from '../../services/task';
import { AuthService } from '../../services/auth';
import { Task } from '../../models/task';

@Component({
  selector: 'app-tasks',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './tasks.html',
  styleUrl: './tasks.css',
})
export class Tasks implements OnInit {
  tasks: Task[] = [];
  error: string | null = null;
  loading = false;

  newTask: Task = {
    title: '',
    description: '',
    status: 'not_done',
    priority: 'medium',
    due_date: '',
    workspace: 1,
    category: 1
  };

  constructor(
    private taskService: TaskService,
    private auth: AuthService,
    private router: Router
  ) {}

  ngOnInit(): void {
    if (!this.auth.isLoggedIn()) {
      this.router.navigate(['/login']);
      return;
    }
    this.loadTasks();
  }

  loadTasks() {
    this.loading = true;
    this.taskService.getTasks(1).subscribe({
      next: (data) => {
        this.tasks = data;
        this.loading = false;
      },
      error: () => {
        this.error = 'Failed to load tasks';
        this.loading = false;
      }
    });
  }

  createTask() {
    this.taskService.createTask(this.newTask).subscribe({
      next: () => {
        this.newTask = {
          title: '',
          description: '',
          status: 'not_done',
          priority: 'medium',
          due_date: '',
          workspace: 1,
          category: 1
        };
        this.loadTasks();
      },
      error: () => {
        this.error = 'Failed to create task';
      }
    });
  }

  markDone(task: Task) {
    if (!task.id) return;
    this.taskService.updateTask(task.id, { status: 'done' }).subscribe({
      next: () => this.loadTasks(),
      error: () => this.error = 'Failed to update task'
    });
  }

  deleteTask(task: Task) {
    if (!task.id) return;
    this.taskService.deleteTask(task.id).subscribe({
      next: () => this.loadTasks(),
      error: () => this.error = 'Failed to delete task'
    });
  }

  logout() {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
