import { Routes } from '@angular/router';
import { Login } from './pages/login/login';
import { Tasks } from './pages/tasks/tasks';
import { TaskDetail } from './pages/task-detail/task-detail';
import { Categories } from './pages/categories/categories';

export const routes: Routes = [
  { path: '', redirectTo: 'login', pathMatch: 'full' },
  { path: 'login', component: Login },
  { path: 'tasks', component: Tasks },
  { path: 'tasks/:id', component: TaskDetail },
  { path: 'categories', component: Categories },
];
