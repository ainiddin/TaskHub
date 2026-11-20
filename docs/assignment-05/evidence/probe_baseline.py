# Scratch verification probes (Assignment #05). NOT part of the product; run by copying into back/ and: python manage.py test probe_baseline
"""Throw-away verification probes for Assignment #05 (NOT part of the product).

Each probe prints one 'PROBE Hn | observed ...' line. They only describe observed
behaviour of the baseline code; they assert nothing, so the baseline run cannot fail.
Run: python manage.py test probe_baseline -v 2
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from django.test import TestCase

from api.models import Workspace, WorkspaceMember, Task, SubTask, TaskActivity, UserStats


def mk_user(name):
    return User.objects.create_user(username=name, password='pass12345!')


def api_for(user):
    c = APIClient(raise_request_exception=False)
    c.force_authenticate(user=user)
    return c


def say(tag, text):
    print(f'PROBE {tag} | {text}')


class Probes(TestCase):
    def setUp(self):
        self.alice = mk_user('alice')
        self.bob = mk_user('bob')          # outsider, member of nothing
        self.carol = mk_user('carol')      # plain "member" of Alice's workspace
        self.ws = Workspace.objects.create(name='Alice WS', created_by=self.alice)
        WorkspaceMember.objects.create(workspace=self.ws, user=self.alice, role='owner')
        WorkspaceMember.objects.create(workspace=self.ws, user=self.carol, role='member')
        self.ws_task = Task.objects.create(title='ws task', workspace=self.ws, created_by=self.alice)
        self.personal = Task.objects.create(title='alice personal', created_by=self.alice)
        self.sub = SubTask.objects.create(title='s1', task=self.personal, created_by=self.alice, status='done')
        self.a = api_for(self.alice)
        self.b = api_for(self.bob)
        self.c = api_for(self.carol)

    def test_H1_member_list_idor(self):
        r = self.b.get(f'/api/workspaces/{self.ws.id}/members/')
        say('H1', f'bob (non-member) GET members of Alice WS -> HTTP {r.status_code}, rows={len(r.json()) if r.status_code == 200 else "-"}')

    def test_H2_cross_workspace_task_create(self):
        before = TaskActivity.objects.filter(workspace=self.ws).count()
        r = self.b.post('/api/tasks/', {'title': 'planted by bob', 'workspace': self.ws.id}, format='json')
        t = Task.objects.filter(title='planted by bob').first()
        say('H2', f'bob POST task into Alice WS -> HTTP {r.status_code}; stored workspace_id={t.workspace_id if t else None}; '
                  f'new activity rows in Alice WS={TaskActivity.objects.filter(workspace=self.ws).count() - before}')

    def test_H3_foreign_subtask(self):
        task = Task.objects.create(title='alice ws task 2', workspace=self.ws, created_by=self.alice)
        r = self.b.post('/api/subtasks/', {'title': 'blocker by bob', 'task': task.id}, format='json')
        r2 = self.a.patch(f'/api/tasks/{task.id}/', {'status': 'done'}, format='json')
        say('H3', f'bob POST subtask onto Alice task -> HTTP {r.status_code}; then Alice PATCH task status=done -> HTTP {r2.status_code} {r2.json() if r2.status_code >= 400 else ""}')

    def test_H4_duplicate_username(self):
        c = APIClient(raise_request_exception=False)
        r1 = c.post('/api/register/', {'username': 'dup', 'password': 'pass12345!'}, format='json')
        r2 = c.post('/api/register/', {'username': 'dup', 'password': 'pass12345!'}, format='json')
        say('H4', f'register same username twice -> HTTP {r1.status_code} then HTTP {r2.status_code}')

    def test_H5_weak_password(self):
        c = APIClient(raise_request_exception=False)
        r = c.post('/api/register/', {'username': 'weakling', 'password': '1'}, format='json')
        say('H5', f'register with password "1" -> HTTP {r.status_code}')

    def test_H6_H7_statistics(self):
        r = self.a.get('/api/statistics/?period=custom&date_from=bad&date_to=bad')
        say('H6', f'statistics custom with invalid dates -> HTTP {r.status_code}')
        n0 = UserStats.objects.filter(user=self.alice).count()
        for _ in range(3):
            self.a.get('/api/statistics/?period=week')
        n1 = UserStats.objects.filter(user=self.alice).count()
        say('H7', f'3 x GET /api/statistics/ -> UserStats rows for alice: {n0} -> {n1}')

    def test_H8_logout_does_not_revoke(self):
        c = APIClient(raise_request_exception=False)
        login = c.post('/api/login/', {'username': 'alice', 'password': 'pass12345!'}, format='json').json()
        c.credentials(HTTP_AUTHORIZATION=f'Bearer {login["access"]}')
        lo = c.post('/api/logout/')
        c2 = APIClient(raise_request_exception=False)
        rf = c2.post('/api/token/refresh/', {'refresh': login['refresh']}, format='json')
        say('H8', f'logout -> HTTP {lo.status_code}; refresh with the same refresh token afterwards -> HTTP {rf.status_code}')

    def test_H9_member_can_rename_workspace(self):
        r = self.c.patch(f'/api/workspaces/{self.ws.id}/', {'name': 'renamed by carol'}, format='json')
        self.ws.refresh_from_db()
        say('H9', f'carol (role=member) PATCH workspace name -> HTTP {r.status_code}; name now "{self.ws.name}"')

    def test_H10_arbitrary_role(self):
        r1 = self.a.post(f'/api/workspaces/{self.ws.id}/members/', {'username': 'bob', 'role': 'superuser-xyz'}, format='json')
        say('H10', f'owner adds bob with role="superuser-xyz" -> HTTP {r1.status_code}; stored role={r1.json().get("role") if r1.status_code == 201 else "-"}')
        # promote check: can an *admin* mint another owner?
        admin = mk_user('dave')
        WorkspaceMember.objects.create(workspace=self.ws, user=admin, role='admin')
        eve = mk_user('eve')
        r2 = api_for(admin).post(f'/api/workspaces/{self.ws.id}/members/', {'username': 'eve', 'role': 'owner'}, format='json')
        say('H10b', f'admin dave adds eve with role="owner" -> HTTP {r2.status_code}; stored role={r2.json().get("role") if r2.status_code == 201 else "-"}')

    def test_H11_move_task_to_foreign_workspace(self):
        other = Workspace.objects.create(name='Bob private WS', created_by=self.bob)
        WorkspaceMember.objects.create(workspace=other, user=self.bob, role='owner')
        r = self.a.patch(f'/api/tasks/{self.personal.id}/', {'workspace': other.id}, format='json')
        self.personal.refresh_from_db()
        say('H11', f'alice PATCH her personal task workspace=<Bob WS she is not in> -> HTTP {r.status_code}; task.workspace_id now {self.personal.workspace_id} (Bob WS id={other.id})')

    def test_H12_get_list_resets_foreign_recurring(self):
        t = Task.objects.create(title='daily', created_by=self.alice, is_recurring=True, repeat_type='daily',
                                status='done', next_occurrence=date.today() - timedelta(days=1))
        self.b.get('/api/tasks/')
        t.refresh_from_db()
        say('H12', f'bob GET /api/tasks/ -> Alice recurring task status now "{t.status}" (was "done")')

    def test_H13_no_login_throttle(self):
        c = APIClient(raise_request_exception=False)
        codes = [c.post('/api/login/', {'username': 'alice', 'password': f'wrong{i}'}, format='json').status_code for i in range(20)]
        say('H13', f'20 wrong-password logins -> status codes set {sorted(set(codes))}')

    def test_H14_monthly_is_30_days(self):
        t = Task.objects.create(title='monthly', created_by=self.alice, is_recurring=True, repeat_type='monthly')
        self.a.patch(f'/api/tasks/{t.id}/', {'status': 'done'}, format='json')
        t.refresh_from_db()
        say('H14', f'monthly task completed -> next_occurrence - today = {(t.next_occurrence - date.today()).days} days')

    def test_H15_personal_task_idor(self):
        r = self.b.get(f'/api/tasks/{self.personal.id}/')
        say('H15', f'bob GET alice personal task by id -> HTTP {r.status_code}')

    def test_H16_subtask_idor(self):
        r = self.b.get(f'/api/subtasks/{self.sub.id}/')
        say('H16', f'bob GET alice subtask by id -> HTTP {r.status_code}')

    def test_H17_search_injection(self):
        r = self.b.get("/api/tasks/?search=' OR 1=1 --")
        say('H17', f"bob GET /api/tasks/?search=' OR 1=1 -- -> HTTP {r.status_code}, rows returned={len(r.json())}")

    def test_H18_jwt_lifetimes(self):
        from rest_framework_simplejwt.settings import api_settings
        say('H18', f'ACCESS_TOKEN_LIFETIME={api_settings.ACCESS_TOKEN_LIFETIME}, REFRESH_TOKEN_LIFETIME={api_settings.REFRESH_TOKEN_LIFETIME}')

    def test_H19_activity_leak(self):
        TaskActivity.objects.create(workspace=self.ws, user=self.alice, action='task_created', message='secret')
        r = self.b.get('/api/activities/')
        say('H19', f'bob GET /api/activities/ -> HTTP {r.status_code}, rows={len(r.json())}')

    def test_H20_anonymous_read(self):
        r = APIClient(raise_request_exception=False).get('/api/tasks/')
        say('H20', f'anonymous GET /api/tasks/ -> HTTP {r.status_code}')
