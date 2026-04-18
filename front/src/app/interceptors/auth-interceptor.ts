import {
  HttpInterceptorFn,
  HttpRequest,
  HttpHandlerFn,
  HttpErrorResponse,
} from '@angular/common/http';
import { inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { catchError, switchMap, throwError } from 'rxjs';
import { Router } from '@angular/router';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const token = localStorage.getItem('access');
  const http = inject(HttpClient);
  const router = inject(Router);

  const authReq = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // если 401 и это не запрос на refresh
      if (error.status === 401 && !req.url.includes('/api/token/refresh/')) {
        const refresh = localStorage.getItem('refresh');
        if (refresh) {
          return http.post<any>('/api/token/refresh/', { refresh }).pipe(
            switchMap((tokens) => {
              localStorage.setItem('access', tokens.access);
              const retryReq = req.clone({
                setHeaders: { Authorization: `Bearer ${tokens.access}` },
              });
              return next(retryReq);
            }),
            catchError((refreshError) => {
              // refresh тоже протух — выкидываем на логин
              localStorage.clear();
              router.navigate(['/login']);
              return throwError(() => refreshError);
            }),
          );
        } else {
          localStorage.clear();
          router.navigate(['/login']);
        }
      }
      return throwError(() => error);
    }),
  );
};
