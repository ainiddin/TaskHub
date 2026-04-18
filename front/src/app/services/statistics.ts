import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class StatisticsService {
  private apiUrl = 'http://127.0.0.1:8000/api';

  constructor(private http: HttpClient) {}

  getStats(period: string, dateFrom?: string, dateTo?: string): Observable<any> {
    let url = `${this.apiUrl}/statistics/?period=${period}`;
    if (period === 'custom' && dateFrom && dateTo) {
      url += `&date_from=${dateFrom}&date_to=${dateTo}`;
    }
    return this.http.get(url);
  }
}
