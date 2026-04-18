import { Component, OnInit, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { StatisticsService } from '../../services/statistics';

@Component({
  selector: 'app-statistics',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './statistics.html',
  styleUrl: './statistics.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Statistics implements OnInit {
  stats = signal<any>(null);
  loading = signal(false);
  period = signal('week');
  dateFrom = signal('');
  dateTo = signal('');

  constructor(private statsService: StatisticsService) {}

  ngOnInit() {
    this.load();
  }

  load() {
    this.loading.set(true);
    this.statsService.getStats(this.period(), this.dateFrom(), this.dateTo()).subscribe({
      next: (data) => {
        this.stats.set(data);
        this.loading.set(false);
      },
      error: () => this.loading.set(false),
    });
  }

  get completionRate(): number {
    const s = this.stats();
    if (!s?.total_tasks) return 0;
    return Math.round((s.completed_tasks / s.total_tasks) * 100);
  }
}
