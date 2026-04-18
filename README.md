<div align="center">
  <h1>📋 TaskFlow</h1>
  <p><b>Your Personal Navigator to Peak Productivity</b></p>
</div>

## Team Members

- Sailaukhan Yenglik
- Yessirkep Ainiddin
- Saparkhan Sanzhar

## Project Description

TaskFlow is a full-stack task management system that helps users organize personal and workspace tasks in a simple and structured way.  
The application allows users to manage daily activities, create subtasks, collaborate inside workspaces, track task progress, and work with recurring tasks for repeated routines.

## What does the app do?

- User Authentication: users can register, log in, log out, and access their personal profile.
- Task Management: users can create, edit, delete, and manage personal or workspace tasks.
- Workspace System: users can create workspaces, join collaborative spaces, and manage workspace members.
- Task Status Control: tasks can be marked as not done, done, or overdue.
- Recurring Tasks: users can create daily, weekly, monthly, or custom recurring tasks.
- Subtasks: users can break large tasks into smaller subtasks and track their completion.
- Filtering and Search: users can filter tasks by status or priority and search tasks by title or description.
- Statistics: users can see task statistics for different periods.
- Activity Tracking: workspace activity is recorded for important actions such as task creation, completion, and member management.

## Technologies

### Frontend
- Angular
- TypeScript
- HTML
- CSS

### Backend
- Python
- Django
- Django REST Framework
- Simple JWT
- django-cors-headers
- SQLite

## Main Features

- JWT authentication: register, login, logout, profile
- Full CRUD for tasks
- Full CRUD for subtasks
- Workspace creation and deletion
- Workspace member management
- Personal tasks and workspace tasks
- Task filtering by status
- Task filtering by priority
- Task search
- Recurring task logic
- Activity history
- User statistics
- Objects linked to authenticated user

## Project Structure

```bash
TaskFlow/
│
├── front/                  # Angular frontend
│   ├── src/
│   ├── package.json
│   └── angular.json
│
├── back/                   # Django backend
│   ├── api/
│   ├── config/
│   ├── manage.py
│   ├── requirements.txt
│   └── db.sqlite3
│
├── .gitignore
└── README.md
```

## How to Run the Project

### Backend

```bash
cd back
.\venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Backend runs on:

```bash
http://127.0.0.1:8000/
```

### Frontend

Open a second terminal:

```bash
cd front
npm install
ng serve
```

Frontend runs on:

```bash
http://localhost:4200/
```

## API Endpoints

```bash
POST   /api/register/
POST   /api/login/
POST   /api/logout/
GET    /api/profile/

GET    /api/workspaces/
POST   /api/workspaces/
GET    /api/workspaces/<id>/
PATCH  /api/workspaces/<id>/
DELETE /api/workspaces/<id>/

GET    /api/workspaces/<workspace_id>/members/
POST   /api/workspaces/<workspace_id>/members/

GET    /api/tasks/
POST   /api/tasks/
GET    /api/tasks/<id>/
PATCH  /api/tasks/<id>/
DELETE /api/tasks/<id>/

GET    /api/subtasks/
POST   /api/subtasks/
GET    /api/subtasks/<id>/
PATCH  /api/subtasks/<id>/
DELETE /api/subtasks/<id>/

GET    /api/activity/
GET    /api/statistics/
```

## Recurring Task Logic

TaskFlow supports recurring tasks.

- If a task is marked as recurring, it can repeat on a daily, weekly, monthly, or custom schedule.
- When a recurring task is completed, it stays completed until the next occurrence date arrives.
- After the next cycle starts, the task becomes active again.

## Notes

- `requirements.txt` is needed only for the backend.
- Frontend dependencies are stored in `package.json`.
- `node_modules`, `venv`, `.angular`, and `db.sqlite3` should not be pushed to Git.
- `.gitignore` should be created in the root folder of the project.

## Academic Info

Student project for Web Development, KBTU 2025–2026.
