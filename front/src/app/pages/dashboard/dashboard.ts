import { Component, OnInit, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';
import { StatisticsService } from '../../services/statistics';
import { TaskService } from '../../services/task';
import { AuthService } from '../../services/auth';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Dashboard implements OnInit {
  stats = signal<any>(null);
  recentTasks = signal<any[]>([]);
  loading = signal(false);

  constructor(
    private statsService: StatisticsService,
    private taskService: TaskService,
    public auth: AuthService,
  ) {}

  ngOnInit() {
    this.loading.set(true);
    this.statsService.getStats('week', '', '').subscribe({
      next: (data: any) => {
        this.stats.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
    this.taskService.getTasks().subscribe({
      next: (data: any[]) => {
        this.recentTasks.set(data.filter((t: any) => t.status !== 'done').slice(0, 5));
      },
    });
  }

  get completionRate(): number {
    const s = this.stats();
    if (!s?.total_tasks) return 0;
    return Math.round((s.completed_tasks / s.total_tasks) * 100);
  }

  getGreeting(): string {
    const h = new Date().getHours();
    if (h < 12) return 'Good morning';
    if (h < 18) return 'Good afternoon';
    return 'Good evening';
  }
}
