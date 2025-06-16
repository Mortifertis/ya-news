from http import HTTPStatus

import pytest
from django.urls import reverse

from news.forms import BAD_WORDS, WARNING
from news.models import Comment, News

COMMENT_TEXT = 'Текст комментария'
NEW_COMMENT_TEXT = 'Обновлённый комментарий'


@pytest.fixture
def author(django_user_model):
    return django_user_model.objects.create(username='Мимо Крокодил')


@pytest.fixture
def reader(django_user_model):
    return django_user_model.objects.create(username='Читатель')


@pytest.fixture
def news():
    return News.objects.create(title='Заголовок', text='Текст')


@pytest.fixture
def comment(news, author):
    return Comment.objects.create(news=news, author=author, text=COMMENT_TEXT)


@pytest.mark.django_db
def test_anonymous_user_cant_create_comment(client, news):
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': COMMENT_TEXT}
    client.post(url, data=form_data)
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_can_create_comment(client, author, news):
    url = reverse('news:detail', args=(news.id,))
    form_data = {'text': COMMENT_TEXT}
    client.force_login(author)
    response = client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f'{url}#comments'
    assert Comment.objects.count() == 1
    comment = Comment.objects.get()
    assert comment.text == COMMENT_TEXT
    assert comment.news == news
    assert comment.author == author


@pytest.mark.django_db
def test_user_cant_use_bad_words(client, author, news):
    url = reverse('news:detail', args=(news.id,))
    bad_words_data = {'text': f'Какой-то текст, {BAD_WORDS[0]}, еще текст'}
    client.force_login(author)
    response = client.post(url, data=bad_words_data)
    form = response.context['form']
    assert form.errors.get('text') == [WARNING]
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_author_can_delete_comment(client, author, comment):
    url = reverse('news:delete', args=(comment.id,))
    redirect_url = reverse('news:detail', args=(comment.news.id,)) + '#comments'
    client.force_login(author)
    response = client.delete(url)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == redirect_url
    assert Comment.objects.count() == 0


@pytest.mark.django_db
def test_user_cant_delete_comment_of_another_user(client, reader, comment):
    url = reverse('news:delete', args=(comment.id,))
    client.force_login(reader)
    response = client.delete(url)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert Comment.objects.count() == 1


@pytest.mark.django_db
def test_author_can_edit_comment(client, author, comment):
    url = reverse('news:edit', args=(comment.id,))
    redirect_url = reverse('news:detail', args=(comment.news.id,)) + '#comments'
    form_data = {'text': NEW_COMMENT_TEXT}
    client.force_login(author)
    response = client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.url == redirect_url
    comment.refresh_from_db()
    assert comment.text == NEW_COMMENT_TEXT


@pytest.mark.django_db
def test_user_cant_edit_comment_of_another_user(client, reader, comment):
    url = reverse('news:edit', args=(comment.id,))
    form_data = {'text': NEW_COMMENT_TEXT}
    client.force_login(reader)
    response = client.post(url, data=form_data)
    assert response.status_code == HTTPStatus.NOT_FOUND
    comment.refresh_from_db()
    assert comment.text == COMMENT_TEXT
