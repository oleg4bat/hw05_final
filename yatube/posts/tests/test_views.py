import tempfile

from django.conf import settings
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..consts import POSTS_IN_PAGE
from ..forms import PostForm
from ..models import Follow, Group, Post, User
from .consts import GROUP_DESCRIPTION, GROUP_SLUG, GROUP_TITLE, TEXT, USERNAME

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
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
            group=cls.group,
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse(
                'posts:group_list', kwargs={'slug': 'test-slug'}
            ): 'posts/group_list.html',
            reverse(
                'posts:profile', kwargs={'username': 'HasNoName'}
            ): 'posts/profile.html',
            reverse(
                'posts:post_detail', kwargs={'post_id': 1}
            ): 'posts/post_detail.html',
            reverse(
                'posts:post_edit', kwargs={'post_id': 1}
            ): 'posts/create_post.html',
            reverse('posts:post_create'): 'posts/create_post.html',
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                cache.clear()
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_create_and_edit_pages_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        urls = [
            ('posts:post_create', None, False),
            ('posts:post_edit', '1', True),
        ]
        for name, args, is_edit_value in urls:
            response = self.authorized_client.get(reverse(name, args=args))
            self.assertIn('form', response.context)
            self.assertIsInstance(response.context['form'], PostForm)
            self.assertIn('is_edit', response.context)
            is_edit = response.context['is_edit']
            self.assertIsInstance(is_edit, bool)
            self.assertEqual(is_edit, is_edit_value)

    def check_context_contains_page_or_post(self, context, post=False):
        if post:
            self.assertIn('post', context)
            post = context['post']
        else:
            self.assertIn('page_obj', context)
            post = context['page_obj'][0]
        self.assertEqual(post.author, self.post.author)
        self.assertEqual(post.pub_date, self.post.pub_date)
        self.assertEqual(post.text, self.post.text)
        self.assertEqual(post.group, self.post.group)

    def test_index_page_context_is_correct(self):
        response = self.guest_client.get(reverse('posts:index'))
        self.check_context_contains_page_or_post(response.context)

    def test_profile_page_context_is_correct(self):
        response = self.guest_client.get(reverse('posts:profile',
                                         kwargs={'username': 'HasNoName'}))
        self.check_context_contains_page_or_post(response.context)

        self.assertIn('author', response.context)
        self.assertEqual(response.context['author'], self.user)

    def test_post_datail_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1}
        ))
        self.check_context_contains_page_or_post(response.context, post=True)
        self.assertIn('user', response.context)
        self.assertEqual(response.context['user'], self.user)

    def test_paginator(self):
        pages = (
            (1, 10),
            (2, 1)
        )
        for i in range(POSTS_IN_PAGE):
            Post.objects.create(
                author=self.user,
                text=TEXT,
                group=self.group,
            )
        for page, expected_count in pages:
            response = self.guest_client.get(
                reverse('posts:index'), {'page': page}
            )
            self.assertEqual(
                len(response.context.get('page_obj').object_list),
                expected_count
            )
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_IN_PAGE)

    def test_cache_index_page(self):
        response = self.client.get(reverse('posts:index'))
        cache_response = response.content
        Post.objects.all().delete()
        response = self.client.get(reverse('posts:index'))
        cache_content = response.content
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(cache_response, cache_content)
        self.assertNotEqual(cache_response, response)

    def test_follow(self):
        follow_count = self.user.follower.all().count()
        user1 = User.objects.create_user(username='user')
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': user1})
        )
        after_follow_count = self.user.follower.all().count()
        self.assertEqual(after_follow_count, follow_count + 1)

    def test_unfollow(self):
        user1 = User.objects.create_user(username='user')
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': user1})
        )
        after_follow_count = self.user.follower.all().count()
        Follow.objects.get(user=self.user, author=user1).delete()
        after_unfollow_count = self.user.follower.all().count()
        self.assertEqual(after_unfollow_count, after_follow_count - 1)
