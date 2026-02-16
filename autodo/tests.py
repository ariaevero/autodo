from django.test import TestCase

from autodo.models import User


class UserModelTest(TestCase):
    def test_user_creation(self):
        user = User.objects.create_user(username="tester", password="secret")
        self.assertEqual(user.username, "tester")
