import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class TaskService {
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  getTasks(workspaceId?: number): Observable<any[]> {
    const param = workspaceId ? `?workspace=${workspaceId}` : '?workspace=';
    return this.http.get<any[]>(`${this.apiUrl}/tasks/${param}`);
  }

  searchTasks(query: string): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/tasks/?search=${encodeURIComponent(query)}`);
  }

  createTask(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/tasks/`, data);
  }

  updateTask(id: number, data: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/tasks/${id}/`, data);
  }

  deleteTask(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/tasks/${id}/`);
  }
}
