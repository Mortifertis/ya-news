from http import HTTPStatus

import pytest
from pytest_lazy_fixtures import lf
from django.urls import reverse

from news.models import Comment, News


@pytest.fixture
def news():
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Лев Толстой')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель простой')


@pytest.fixture
def comment(news, author):
    return Comment.objects.create(news=news, author=author, text='Текст комментария')


@pytest.mark.django_db
def test_pages_availability(client, news):
    urls = (
        ('news:home', None, client.get),
        ('news:detail', (news.id,), client.get),
        ('users:login', None, client.get),
        ('users:logout', None, client.post),
        ('users:signup', None, client.get),
    )
    for name, args, request in urls:
        url = reverse(name, args=args)
        response = request(url)
        assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db
@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
@pytest.mark.parametrize(
    'user, expected_status',
    (
        pytest.param(lf('author'), HTTPStatus.OK, id='author'),
        pytest.param(lf('reader'), HTTPStatus.NOT_FOUND, id='reader'),
    ),
)
def test_availability_for_comment_edit_and_delete(client, name, user, expected_status, comment):
    client.force_login(user)
    url = reverse(name, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == expected_status


@pytest.mark.django_db
@pytest.mark.parametrize('name', ('news:edit', 'news:delete'))
def test_redirect_for_anonymous_client(client, name, comment):
    login_url = reverse('users:login')
    url = reverse(name, args=(comment.id,))
    response = client.get(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{login_url}?next={url}'
