import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class SubtaskService {
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  createSubtask(data: any): Observable<any> {
    return this.http.post(`${this.apiUrl}/subtasks/`, data);
  }

  updateSubtask(id: number, data: any): Observable<any> {
    return this.http.patch(`${this.apiUrl}/subtasks/${id}/`, data);
  }

  deleteSubtask(id: number): Observable<any> {
    return this.http.delete(`${this.apiUrl}/subtasks/${id}/`);
  }
}
