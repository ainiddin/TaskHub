"""Tests for the two mitigated risks of Assignment #05.

R-01  cross-workspace authorization gaps (members list, task create/move, subtask create)
R-03  registration robustness (duplicate username -> 500, weak password accepted)

They were written first and FAIL on the pre-mitigation code (see docs/assignment-05/evidence).
"""
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Workspace, WorkspaceMember, Task, SubTask, TaskActivity


def make_user(username):
    return User.objects.create_user(username=username, password='pass12345!')


def client_for(user):
    # raise_request_exception=False: an unhandled server error must show up as HTTP 500, not abort the test
    client = APIClient(raise_request_exception=False)
    client.force_authenticate(user=user)
    return client


class R01AuthorizationTests(TestCase):
    def setUp(self):
        self.alice = make_user('alice')   # owner of the workspace
        self.bob = make_user('bob')       # outsider
        self.workspace = Workspace.objects.create(name='Alice WS', created_by=self.alice)
        WorkspaceMember.objects.create(workspace=self.workspace, user=self.alice, role='owner')
        self.workspace_task = Task.objects.create(title='ws task', workspace=self.workspace, created_by=self.alice)
        self.alice_client = client_for(self.alice)
        self.bob_client = client_for(self.bob)

    # --- members list ---------------------------------------------------------------------
    def test_non_member_cannot_list_workspace_members(self):
        response = self.bob_client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 403)

    def test_member_can_list_workspace_members(self):
        response = self.alice_client.get(f'/api/workspaces/{self.workspace.id}/members/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()), 1)

    # --- task create / move ---------------------------------------------------------------
    def test_non_member_cannot_create_task_in_foreign_workspace(self):
        response = self.bob_client.post('/api/tasks/', {'title': 'planted', 'workspace': self.workspace.id}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(Task.objects.filter(title='planted').exists())
        self.assertFalse(TaskActivity.objects.filter(workspace=self.workspace).exists())

    def test_member_can_create_task_in_own_workspace(self):
        response = self.alice_client.post('/api/tasks/', {'title': 'legit', 'workspace': self.workspace.id}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Task.objects.get(title='legit').workspace_id, self.workspace.id)

    def test_personal_task_without_workspace_still_works(self):
        response = self.bob_client.post('/api/tasks/', {'title': 'mine'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIsNone(Task.objects.get(title='mine').workspace_id)

    def test_cannot_move_task_into_foreign_workspace(self):
        personal = Task.objects.create(title='bob personal', created_by=self.bob)
        response = self.bob_client.patch(f'/api/tasks/{personal.id}/', {'workspace': self.workspace.id}, format='json')
        self.assertEqual(response.status_code, 400)
        personal.refresh_from_db()
        self.assertIsNone(personal.workspace_id)

    # --- subtask create -------------------------------------------------------------------
    def test_non_member_cannot_add_subtask_to_foreign_task(self):
        response = self.bob_client.post('/api/subtasks/', {'title': 'blocker', 'task': self.workspace_task.id}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(SubTask.objects.filter(title='blocker').exists())

    def test_member_can_add_subtask_to_workspace_task(self):
        response = self.alice_client.post('/api/subtasks/', {'title': 'ok', 'task': self.workspace_task.id}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_owner_can_add_subtask_to_own_personal_task(self):
        personal = Task.objects.create(title='p', created_by=self.alice)
        response = self.alice_client.post('/api/subtasks/', {'title': 'ok', 'task': personal.id}, format='json')
        self.assertEqual(response.status_code, 201)

    def test_user_cannot_add_subtask_to_someone_elses_personal_task(self):
        personal = Task.objects.create(title='p', created_by=self.alice)
        response = self.bob_client.post('/api/subtasks/', {'title': 'x', 'task': personal.id}, format='json')
        self.assertEqual(response.status_code, 400)


class R03RegistrationTests(TestCase):
    def setUp(self):
        self.client = APIClient(raise_request_exception=False)

    def register(self, username, password):
        return self.client.post('/api/register/', {'username': username, 'password': password}, format='json')

    def test_duplicate_username_returns_400_not_500(self):
        self.assertEqual(self.register('dup', 'pass12345!').status_code, 201)
        response = self.register('dup', 'pass12345!')
        self.assertEqual(response.status_code, 400)
        self.assertIn('username', response.json())
        self.assertEqual(User.objects.filter(username='dup').count(), 1)

    def test_too_short_password_is_rejected(self):
        response = self.register('weak1', '1')
        self.assertEqual(response.status_code, 400)
        self.assertIn('password', response.json())
        self.assertFalse(User.objects.filter(username='weak1').exists())

    def test_common_password_is_rejected(self):
        response = self.register('weak2', 'password')
        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.filter(username='weak2').exists())

    def test_strong_password_still_registers(self):
        self.assertEqual(self.register('strong', 'Tr0ub4dor&3-horse').status_code, 201)
