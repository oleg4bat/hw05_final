from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Post, User
from .consts import TEXT, USERNAME


class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.form = PostForm()
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'текст',
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'HasNoName'})
        )
        self.assertEqual(Post.objects.count(), tasks_count + 1)
        text = Post.objects.first().text
        self.assertEqual(text, form_data['text'])

    def test_geust_cant_create(self):
        """Валидная форма создает запись в Post."""
        tasks_count = Post.objects.count()
        form_data = {
            'text': 'текст',
        }
        response = self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, '/auth/login/?next=/create/')
        self.assertEqual(Post.objects.count(), tasks_count)

    def test_post_edit(self):
        form_data = {
            'text': 'слово',
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': 1})
        )
        self.assertEqual(Post.objects.first().text, form_data['text'])

    def test_geust_cant_edit(self):
        """Валидная форма создает запись в Post."""
        form_data = {
            'text': 'слово',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': 1}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/edit/'))
        self.assertEqual(Post.objects.first().text, self.post.text)
