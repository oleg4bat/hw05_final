from http import HTTPStatus

from django.core.cache import cache
from django.test import Client, TestCase

from ..models import Group, Post, User
from .consts import GROUP_DESCRIPTION, GROUP_SLUG, GROUP_TITLE, TEXT, USERNAME


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user1 = User.objects.create_user(username='user')
        cls.post = Post.objects.create(
            author=cls.user,
            text=TEXT,
        )
        cls.group = Group.objects.create(
            title=GROUP_TITLE,
            slug=GROUP_SLUG,
            description=GROUP_DESCRIPTION,
        )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user1)
        cls.authorized_client.force_login(cls.user)
        cls.access = {
            '/': 'all',
            f'/group/{cls.group.slug}/': 'all',
            f'/profile/{cls.user.username}/': 'all',
            f'/posts/{cls.post.pk}/': 'all',
            f'/posts/{cls.post.pk}/edit/': 'author',
            '/create/': 'authorized',
        }
        cls.templates_url_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/HasNoName/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/posts/1/edit/': 'posts/create_post.html',
            '/create/': 'posts/create_post.html',
        }

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        for address, template in self.templates_url_names.items():
            with self.subTest(address=address):
                cache.clear()
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_access_for_author(self):
        """Проверка страниц доступных автору"""
        for address, access, in self.access.items():
            if access == 'authorized':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
            if access == 'all':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
            if access == 'author':
                with self.subTest(address=address):
                    response = self.authorized_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_access_for_guest(self):
        """Проверка страниц доступных гостю"""
        for address, access, in self.access.items():
            if access == 'authorized':
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code,
                                     HTTPStatus.FOUND)
                    self.assertRedirects(response,
                                         ('/auth/login/?next=/create/'))
            if access == 'all':
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
            if access == 'author':
                with self.subTest(address=address):
                    response = self.guest_client.get(address)
                    self.assertEqual(response.status_code,
                                     HTTPStatus.FOUND)
                    self.assertRedirects(response,
                                         ('/auth/login/?next=/posts/1/edit/'))

    def test_urls_access_for_authorized(self):
        """Проверка страниц доступных авторизованному"""
        for address, access, in self.access.items():
            if access == 'authorized':
                with self.subTest(address=address):
                    response = self.authorized_client1.get(address)
                    self.assertEqual(response.status_code,
                                     HTTPStatus.OK)
            if access == 'all':
                with self.subTest(address=address):
                    response = self.authorized_client1.get(address)
                    self.assertEqual(response.status_code, HTTPStatus.OK)
            if access == 'author':
                with self.subTest(address=address):
                    response = self.authorized_client1.get(address)
                    self.assertEqual(response.status_code,
                                     HTTPStatus.FOUND)
                    self.assertRedirects(response, (f'/posts/{self.post.pk}/'))

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
