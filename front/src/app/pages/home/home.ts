import { Component, OnInit } from '@angular/core';
import { Router, RouterOutlet, RouterLink, RouterLinkActive } from '@angular/router';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuthService } from '../../services/auth';
import { WorkspaceService } from '../../services/workspace';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule, RouterOutlet, RouterLink, RouterLinkActive, FormsModule],
  templateUrl: './home.html',
  styleUrl: './home.css',
})
export class Home implements OnInit {
  workspaces: any[] = [];
  workspacesOpen = false;
  myTasksOpen = true;
  showCreateWorkspace = false;
  newWorkspaceName = '';
  newWorkspaceDesc = '';
  pendingDeleteId: number | null = null;

  constructor(
    public auth: AuthService,
    private workspaceService: WorkspaceService,
    private router: Router,
  ) {}

  ngOnInit() {
    this.loadWorkspaces();
  }

  loadWorkspaces() {
    this.workspaceService.getWorkspaces().subscribe({
      next: (data) => (this.workspaces = data),
      error: () => {},
    });
  }

  createWorkspace() {
    if (!this.newWorkspaceName.trim()) return;
    this.workspaceService
      .createWorkspace({
        name: this.newWorkspaceName,
        description: this.newWorkspaceDesc,
      })
      .subscribe({
        next: () => {
          this.showCreateWorkspace = false;
          this.newWorkspaceName = '';
          this.newWorkspaceDesc = '';
          this.loadWorkspaces();
        },
      });
  }

  deleteWorkspace(event: Event, id: number) {
    event.preventDefault();
    event.stopPropagation();
    this.pendingDeleteId = id;
  }

  confirmDelete(event: Event, id: number) {
    event.preventDefault();
    event.stopPropagation();
    this.workspaceService.deleteWorkspace(id).subscribe({
      next: () => {
        this.pendingDeleteId = null;
        this.router.navigate(['/home']);
        this.loadWorkspaces();
      },
      error: (err: any) => console.error(err),
    });
  }

  cancelDelete(event: Event) {
    event.preventDefault();
    event.stopPropagation();
    this.pendingDeleteId = null;
  }

  logout() {
    this.auth.logout();
  }
}
