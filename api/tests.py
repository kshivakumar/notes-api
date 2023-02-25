from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Notebook, Page, Block


def fmt_dt(dt):
    return dt.isoformat().replace("+00:00", "Z")


USERNAME = "test-user"
PASSWORD = "test-pwd"


def setUpModule():
    global User, user
    User = get_user_model()
    user = User.objects.create_user(
        username=USERNAME, password=PASSWORD, email="user@example.com"
    )


class NotebookModelTest(TestCase):

    def test_save_and_delete(self):
        nb1 = Notebook.objects.create(user=user, title="nb1")
        nb2 = Notebook.objects.create(user=user, title="nb2")
        nb3 = Notebook.objects.create(user=user, title="nb3")
        nb4 = Notebook.objects.create(user=user, title="nb4")

        self.assertEqual(
            User.objects.get(username=USERNAME).custom_notebook_order,
            [
                nb1.pk,
                nb2.pk,
                nb3.pk,
                nb4.pk,
            ],
        )

        nb2.delete()
        self.assertEqual(
            User.objects.get(username=USERNAME).custom_notebook_order,
            [nb1.pk, nb3.pk, nb4.pk],
        )


class NotebookAPITest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.notebooks = Notebook.objects.bulk_create(
            [
                Notebook(user=user, title="nb1"),
                Notebook(user=user, title="nb2"),
                Notebook(user=user, title="nb3"),
                Notebook(user=user, title="nb4"),
            ]
        )

    def setUp(self):
        self.client = APIClient()
        self.client.login(username=USERNAME, password=PASSWORD)

    def test_list(self):
        resp = self.client.get(reverse("notebook-list"))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data, [{"id": str(nb.pk), "title": nb.title} for nb in self.notebooks]
        )

    def test_retrieve(self):
        nb = self.notebooks[-1]
        resp = self.client.get(reverse("notebook-detail", kwargs={"pk": nb.pk}))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {
                "id": str(nb.pk),
                "title": nb.title,
                "created": fmt_dt(nb.created),
                "updated": fmt_dt(nb.updated),
                "preferences": nb.preferences,
            },
        )

    def test_retrieve_with_page_list(self):
        nb = self.notebooks[0]
        pg1 = Page.objects.create(notebook=nb, title="nb1-p1")
        pg2 = Page.objects.create(notebook=nb, title="nb1-p2")

        resp = self.client.get(
            reverse("notebook-detail", kwargs={"pk": nb.pk}) + "?include_page_list=true"
        )

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(
            resp.data,
            {
                "id": str(nb.pk),
                "title": nb.title,
                "created": fmt_dt(nb.created),
                "updated": fmt_dt(nb.updated),
                "preferences": nb.preferences,
                "pages": [
                    {
                        "id": str(pg1.pk),
                        "title": pg1.title,
                        "updated": fmt_dt(pg1.updated),
                    },
                    {
                        "id": str(pg2.pk),
                        "title": pg2.title,
                        "updated": fmt_dt(pg2.updated),
                    },
                ],
            },
        )


class PageModelTest(TestCase):
    def test_reposition_block(self):
        nb = Notebook.objects.create(user=user, title="pgtnb")
        page = Page.objects.create(notebook=nb, title="pgt1")
        b1 = Block.objects.create(block_type="h1", page=page).pk
        b2 = Block.objects.create(block_type="h1", page=page).pk
        b3 = Block.objects.create(block_type="h1", page=page).pk
        b4 = Block.objects.create(block_type="h1", page=page).pk
        b5 = Block.objects.create(block_type="h1", page=page).pk

        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b1, b2, b3, b4, b5])

        page.reposition_block(b3, position="top")
        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b3, b1, b2, b4, b5])

        page.reposition_block(b3, position="top")
        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b3, b1, b2, b4, b5])

        page.reposition_block(b1, position="bottom")
        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b3, b2, b4, b5, b1])

        page.reposition_block(b5, after=b2)
        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b3, b2, b5, b4, b1])

        page.reposition_block(b2, after=b1)
        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b3, b5, b4, b1, b2])

        page.reposition_block(b2, after=b1)
        self.assertEqual(Page.objects.get(pk=page.pk).block_order, [b3, b5, b4, b1, b2])

