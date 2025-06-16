from datetime import datetime, timedelta

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from news.forms import CommentForm
from news.models import Comment, News


@pytest.fixture
def home_url():
    return reverse('news:home')


@pytest.fixture
def news_list():
    today = datetime.today()
    News.objects.bulk_create([
        News(
            title=f'Новость {i}',
            text='Просто текст.',
            date=today - timedelta(days=i),
        )
        for i in range(settings.NEWS_COUNT_ON_HOME_PAGE + 1)
    ])
    return News.objects.all()


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Комментатор')


@pytest.fixture
def detailed_news(author):
    news = News.objects.create(title='Тестовая новость', text='Просто текст.')
    now = timezone.now()
    for index in range(10):
        comment = Comment.objects.create(
            news=news, author=author, text=f'Tекст {index}',
        )
        comment.created = now + timedelta(days=index)
        comment.save()
    return news


@pytest.mark.django_db
def test_news_count(client, news_list, home_url):
    response = client.get(home_url)
    object_list = response.context['object_list']
    assert object_list.count() == settings.NEWS_COUNT_ON_HOME_PAGE


@pytest.mark.django_db
def test_news_order(client, news_list, home_url):
    response = client.get(home_url)
    object_list = response.context['object_list']
    dates = [news.date for news in object_list]
    assert dates == sorted(dates, reverse=True)


@pytest.mark.django_db
def test_comments_order(client, detailed_news):
    url = reverse('news:detail', args=(detailed_news.id,))
    response = client.get(url)
    news = response.context['news']
    comments = news.comment_set.all()
    timestamps = [comment.created for comment in comments]
    assert timestamps == sorted(timestamps)


@pytest.mark.django_db
def test_anonymous_client_has_no_form(client, detailed_news):
    url = reverse('news:detail', args=(detailed_news.id,))
    response = client.get(url)
    assert 'form' not in response.context


@pytest.mark.django_db
def test_authorized_client_has_form(client, detailed_news, author):
    url = reverse('news:detail', args=(detailed_news.id,))
    client.force_login(author)
    response = client.get(url)
    assert 'form' in response.context
    assert isinstance(response.context['form'], CommentForm)
