from django.test import TestCase

from ..models import SLICE_OF_TEXT, Group, Post, User
from .consts import GROUP_DESCRIPTION, GROUP_SLUG, GROUP_TITLE, TEXT, USERNAME


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
        )

    def test_post_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        post = PostModelTest.post
        text = PostModelTest.post.text[:SLICE_OF_TEXT]
        self.assertEqual(
            str(post), text, '__str__ выводит неправильную инфомацию'
        )

    def test_group_have_correct_object_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        title = PostModelTest.group.title
        group = PostModelTest.group
        self.assertEqual(
            str(group), title, '__str__ выводит неправильную инфомацию'
        )
