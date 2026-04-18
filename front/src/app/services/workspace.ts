import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class WorkspaceService {
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  getWorkspaces(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/workspaces/`);
  }

  createWorkspace(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/workspaces/`, data);
  }

  deleteWorkspace(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/workspaces/${id}/`);
  }

  getMembers(workspaceId: number): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/workspaces/${workspaceId}/members/`);
  }

  addMember(workspaceId: number, username: string, role: string): Observable<any> {
    return this.http.post(`${this.apiUrl}/workspaces/${workspaceId}/members/`, { username, role });
  }
}
