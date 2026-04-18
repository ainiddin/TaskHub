import { Component, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TaskService } from '../../services/task';
import { Subject } from 'rxjs';
import { debounceTime, distinctUntilChanged } from 'rxjs/operators';

@Component({
  selector: 'app-search',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './search.html',
  styleUrl: './search.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Search {
  query = signal('');
  results = signal<any[]>([]);
  loading = signal(false);
  searched = signal(false);

  private search$ = new Subject<string>();

  constructor(private taskService: TaskService) {
    this.search$.pipe(debounceTime(350), distinctUntilChanged()).subscribe((q) => this.doSearch(q));
  }

  onInput() {
    if (!this.query().trim()) {
      this.results.set([]);
      this.searched.set(false);
      return;
    }
    this.search$.next(this.query().trim());
  }

  doSearch(q: string) {
    this.loading.set(true);
    this.taskService.searchTasks(q).subscribe({
      next: (data) => {
        this.results.set(data);
        this.loading.set(false);
        this.searched.set(true);
      },
      error: () => this.loading.set(false),
    });
  }

  toggleStatus(task: any) {
    const newStatus = task.status === 'done' ? 'not_done' : 'done';
    this.taskService.updateTask(task.id, { status: newStatus }).subscribe({
      next: () => {
        this.results.update((list) =>
          list.map((t) => (t.id === task.id ? { ...t, status: newStatus } : t)),
        );
      },
    });
  }
}
