from django import forms
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..consts import POSTS_IN_PAGE
from ..models import Follow, Group, Post, User
from .consts import GROUP_DESCRIPTION, GROUP_SLUG, GROUP_TITLE, TEXT, USERNAME


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username=USERNAME)
        cls.user1 = User.objects.create_user(username='user')
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
        for i in range(POSTS_IN_PAGE):
            Post.objects.create(
                author=cls.user,
                text=TEXT,
                group=cls.group,
            )
        cls.guest_client = Client()
        cls.authorized_client = Client()
        cls.authorized_client1 = Client()
        cls.authorized_client1.force_login(cls.user1)
        cls.authorized_client.force_login(cls.user)

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

    def test_create_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': 1}
        ))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
        post = response.context['post']
        expected_post = PostPagesTests.post
        self.assertEqual(post, expected_post)

    def test_post_datail_page_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': 1}
        ))
        post = response.context['post']
        expected_post = PostPagesTests.post
        self.assertEqual(post, expected_post)

    def test_first_page_contains_ten_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), POSTS_IN_PAGE)

    def test_second_page_contains_tree_records(self):
        cache.clear()
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 1)

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
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user1})
        )
        after_follow_count = self.user.follower.all().count()
        self.assertEqual(after_follow_count, follow_count + 1)

    def test_unfollow(self):
        self.authorized_client.get(reverse(
            'posts:profile_follow', kwargs={'username': self.user1})
        )
        after_follow_count = self.user.follower.all().count()
        Follow.objects.get(user=self.user, author=self.user1).delete()
        after_unfollow_count = self.user.follower.all().count()
        self.assertEqual(after_unfollow_count, after_follow_count - 1)
