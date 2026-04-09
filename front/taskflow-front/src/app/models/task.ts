export interface Task {
  id?: number;
  title: string;
  description: string;
  status: string;
  priority?: string;
  due_date?: string;
  workspace: number;
  category: number;
  created_by?: string;
  completed_by?: string;
}
