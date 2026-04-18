import { Component, OnInit, signal, ChangeDetectionStrategy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ActivatedRoute } from '@angular/router';
import { WorkspaceService } from '../../services/workspace';
import { Tasks } from '../tasks/tasks';

@Component({
  selector: 'app-workspace',
  standalone: true,
  imports: [CommonModule, FormsModule, Tasks],
  templateUrl: './workspace.html',
  styleUrl: './workspace.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class Workspace implements OnInit {
  workspaceId = signal<number>(0);
  members = signal<any[]>([]);
  showAddMember = signal(false);
  newMemberUsername = signal('');
  newMemberRole = signal('member');
  tab = signal<'tasks' | 'members'>('tasks');

  constructor(
    private route: ActivatedRoute,
    private workspaceService: WorkspaceService,
  ) {}

  ngOnInit() {
    this.route.params.subscribe((params) => {
      const id = +params['id'];
      this.workspaceId.set(0); // сбрасываем чтобы @Input ngOnChanges сработал
      setTimeout(() => {
        this.workspaceId.set(id);
        this.tab.set('tasks');
        this.loadMembers();
      });
    });
  }

  loadMembers() {
    this.workspaceService.getMembers(this.workspaceId()).subscribe({
      next: (data) => this.members.set(data),
    });
  }

  addMember() {
    if (!this.newMemberUsername().trim()) return;
    this.workspaceService
      .addMember(this.workspaceId(), this.newMemberUsername(), this.newMemberRole())
      .subscribe({
        next: () => {
          this.showAddMember.set(false);
          this.newMemberUsername.set('');
          this.loadMembers();
        },
        error: (err: any) => alert(err.error?.error || 'Error adding member'),
      });
  }
}
