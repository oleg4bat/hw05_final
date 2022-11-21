from django.core.paginator import Paginator

from .consts import POSTS_IN_PAGE


def paginator(request, post_list):
    paginator = Paginator(post_list, POSTS_IN_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
