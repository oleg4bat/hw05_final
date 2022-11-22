import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post, User
from .consts import TEXT, USERNAME

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.form = PostForm()

    def setUp(self):
        self.user = User.objects.create_user(username=USERNAME)
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        image_name = 'small.gif'
        uploaded = SimpleUploadedFile(
            name=image_name,
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'текст',
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': 'HasNoName'})
        )
        self.assertEqual(Post.objects.count(), 1)
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
        new_group = Group.objects.create(
            title='New Test group',
            slug='new-test-group',
            description='new test description'
        )
        new_post = Post.objects.create(
            author=self.user,
            text=TEXT,
        )
        form_data = {
            'text': 'слово',
            'group': new_group.id
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': new_post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', kwargs={'post_id': new_post.id})
        )
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.text, form_data['text'])
        self.assertEqual(post.group.id, form_data['group'])

    def test_geust_cant_edit(self):
        """Валидная форма создает запись в Post."""
        post = Post.objects.create(
            author=self.user,
            text=TEXT,
        )
        form_data = {
            'text': 'слово',
        }
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, ('/auth/login/?next=/posts/1/edit/'))
        self.assertEqual(Post.objects.first().text, post.text)
