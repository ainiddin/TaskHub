import { HttpInterceptorFn, HttpErrorResponse, HttpClient } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, switchMap, throwError, BehaviorSubject, filter, take } from 'rxjs';
import { Router } from '@angular/router';

export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const router = inject(Router);
  const http = inject(HttpClient); // В новых версиях Angular это допустимо, НО нужно фильтровать URL

  const apiUrl = 'http://127.0.0.1:8000/api';
  const token = localStorage.getItem('access');

  // Добавляем токен, если он есть
  let authReq = req;
  if (token) {
    authReq = req.clone({
      setHeaders: { Authorization: `Bearer ${token}` },
    });
  }

  return next(authReq).pipe(
    catchError((error: HttpErrorResponse) => {
      // 1. Если это 401 ошибка и это НЕ запрос на логин или рефреш
      if (
        error.status === 401 &&
        !req.url.includes('/login/') &&
        !req.url.includes('/token/refresh/')
      ) {
        const refresh = localStorage.getItem('refresh');

        if (refresh) {
          // Пытаемся обновить токен
          return http.post<any>(`${apiUrl}/token/refresh/`, { refresh }).pipe(
            switchMap((res) => {
              // Обновляем токены в хранилище
              localStorage.setItem('access', res.access);

              // Повторяем изначальный запрос с НОВЫМ токеном
              const retryReq = req.clone({
                setHeaders: { Authorization: `Bearer ${res.access}` },
              });
              return next(retryReq);
            }),
            catchError((refreshError) => {
              // Если даже рефреш не помог — разлогиниваем
              localStorage.clear();
              router.navigate(['/login']);
              return throwError(() => refreshError);
            }),
          );
        } else {
          // Если рефреш-токена нет вообще
          localStorage.clear();
          router.navigate(['/login']);
        }
      }
      return throwError(() => error);
    }),
  );
};
