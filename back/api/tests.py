"""Acceptance-criteria tests (AC1-AC5 from AGENTS.md).

These tests describe behaviour that must stay true after any change. They were written against
the baseline code (commit 5954516) and pass on it, so they also act as a safety net for refactoring.
"""
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Workspace, WorkspaceMember, Task, SubTask


def make_user(username):
    return User.objects.create_user(username=username, password='pass12345!')


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


class AC1VisibilityTests(TestCase):
    """AC1: a user only sees own personal tasks and tasks of workspaces they belong to."""

    def setUp(self):
        self.alice = make_user('alice')
        self.bob = make_user('bob')
        self.workspace = Workspace.objects.create(name='Team', created_by=self.alice)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.alice, role='owner')
        self.personal = Task.objects.create(title='alice personal', created_by=self.alice)
        self.shared = Task.objects.create(title='alice shared', created_by=self.alice, workspace=self.workspace)
        self.subtask = SubTask.objects.create(title='s', task=self.personal, created_by=self.alice)

    def test_owner_sees_personal_and_workspace_tasks(self):
        client = client_for(self.alice)
        personal = client.get('/api/tasks/')
        in_workspace = client.get(f'/api/tasks/?workspace={self.workspace.id}')
        self.assertEqual([t['id'] for t in personal.json()], [self.personal.id])
        self.assertEqual([t['id'] for t in in_workspace.json()], [self.shared.id])

    def test_other_user_cannot_read_foreign_personal_task_or_subtask(self):
        client = client_for(self.bob)
        self.assertEqual(client.get(f'/api/tasks/{self.personal.id}/').status_code, 404)
        self.assertEqual(client.get(f'/api/subtasks/{self.subtask.id}/').status_code, 404)

    def test_other_user_cannot_read_foreign_workspace_tasks(self):
        response = client_for(self.bob).get(f'/api/tasks/?workspace={self.workspace.id}')
        self.assertEqual(response.json(), [])

    def test_anonymous_is_rejected(self):
        self.assertEqual(APIClient().get('/api/tasks/').status_code, 401)


class AC2CompletionRuleTests(TestCase):
    """AC2: a task with unfinished subtasks cannot be completed."""

    def setUp(self):
        self.user = make_user('alice')
        self.client = client_for(self.user)
        self.task = Task.objects.create(title='t', created_by=self.user)
        self.sub = SubTask.objects.create(title='s', task=self.task, created_by=self.user)

    def test_cannot_complete_with_open_subtask(self):
        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'status': 'done'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'not_done')

    def test_can_complete_after_subtasks_done_and_completion_is_recorded(self):
        self.client.patch(f'/api/subtasks/{self.sub.id}/', {'status': 'done'}, format='json')
        response = self.client.patch(f'/api/tasks/{self.task.id}/', {'status': 'done'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'done')
        self.assertEqual(self.task.completed_by, self.user)
        self.assertIsNotNone(self.task.completed_at)


class AC3RecurrenceTests(TestCase):
    """AC3: completing a recurring task sets next_occurrence by repeat_type."""

    def setUp(self):
        self.user = make_user('alice')
        self.client = client_for(self.user)

    def complete(self, **fields):
        task = Task.objects.create(title='r', created_by=self.user, **fields)
        response = self.client.patch(f'/api/tasks/{task.id}/', {'status': 'done'}, format='json')
        self.assertEqual(response.status_code, 200)
        task.refresh_from_db()
        return task

    def test_daily(self):
        task = self.complete(is_recurring=True, repeat_type='daily')
        self.assertEqual(task.next_occurrence, date.today() + timedelta(days=1))

    def test_weekly(self):
        task = self.complete(is_recurring=True, repeat_type='weekly')
        self.assertEqual(task.next_occurrence, date.today() + timedelta(days=7))

    def test_monthly_is_30_days(self):
        task = self.complete(is_recurring=True, repeat_type='monthly')
        self.assertEqual(task.next_occurrence, date.today() + timedelta(days=30))

    def test_custom_uses_repeat_every_days(self):
        task = self.complete(is_recurring=True, repeat_type='custom', repeat_every_days=5)
        self.assertEqual(task.next_occurrence, date.today() + timedelta(days=5))

    def test_custom_without_interval_sets_nothing(self):
        task = self.complete(is_recurring=True, repeat_type='custom')
        self.assertIsNone(task.next_occurrence)

    def test_non_recurring_has_no_next_occurrence(self):
        task = self.complete()
        self.assertIsNone(task.next_occurrence)


class AC4RegistrationAndLoginTests(TestCase):
    """AC4: registration creates user + personal workspace (owner); login returns tokens."""

    def test_register_creates_user_and_owner_workspace_then_login_works(self):
        client = APIClient()
        response = client.post('/api/register/', {'username': 'newbie', 'password': 'pass12345!'}, format='json')
        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username='newbie')
        membership = WorkspaceMember.objects.get(user=user)
        self.assertEqual(membership.role, 'owner')
        self.assertEqual(membership.workspace_id, response.json()['workspace_id'])

        login = client.post('/api/login/', {'username': 'newbie', 'password': 'pass12345!'}, format='json')
        self.assertEqual(login.status_code, 200)
        self.assertIn('access', login.json())
        self.assertIn('refresh', login.json())

    def test_login_with_wrong_password_is_rejected(self):
        make_user('alice')
        response = APIClient().post('/api/login/', {'username': 'alice', 'password': 'nope'}, format='json')
        self.assertEqual(response.status_code, 400)


class AC5WorkspaceRoleTests(TestCase):
    """AC5: only owner/admin add members; only the creator deletes a workspace."""

    def setUp(self):
        self.owner = make_user('owner')
        self.admin = make_user('admin')
        self.member = make_user('member')
        self.newcomer = make_user('newcomer')
        self.workspace = Workspace.objects.create(name='Team', created_by=self.owner)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.owner, role='owner')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.admin, role='admin')
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.member, role='member')
        self.members_url = f'/api/workspaces/{self.workspace.id}/members/'

    def test_plain_member_cannot_add_members(self):
        response = client_for(self.member).post(self.members_url, {'username': 'newcomer'}, format='json')
        self.assertEqual(response.status_code, 403)

    def test_admin_can_add_members(self):
        response = client_for(self.admin).post(self.members_url, {'username': 'newcomer'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(WorkspaceMember.objects.filter(workspace=self.workspace, user=self.newcomer).exists())

    def test_only_creator_can_delete_workspace(self):
        url = f'/api/workspaces/{self.workspace.id}/'
        self.assertEqual(client_for(self.admin).delete(url).status_code, 403)
        self.assertEqual(client_for(self.owner).delete(url).status_code, 204)
        self.assertFalse(Workspace.objects.filter(pk=self.workspace.id).exists())
