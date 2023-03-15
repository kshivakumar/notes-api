from random import choice

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from api.models import Notebook, Page, Block, BLOCK_TYPE


User = get_user_model()


class Command(BaseCommand):
    help = "Creates sample data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--skip-if-exists",
            action="store_true",
            help="Skip sample data creation if users already exist",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        usernames = ["user1", "user2", "user3"]

        if options["skip_if_exists"]:
            if User.objects.filter(username__in=usernames).count() >= 1:
                self.stdout.write(
                    f"Skipping sample data creation as one or more sample users, {usernames} already exist"
                )
                return

        self.stdout.write("Creating sample data...")

        users = []
        for username in usernames:
            users.append(User.objects.create_user(username=username, password=username))
            self.stdout.write(f"Created user {username} with password {username}")

        self.stdout.write("Creating notebooks, pages and blocks...")
        for user in users:
            Notebook.objects.create(user=user, title=f"Notebook without pages")
            notebook = Notebook.objects.create(user=user, title="My Notebook")

            for j in range(1, 3):
                page = Page.objects.create(notebook=notebook, title=f"Page {j}")

                for k in range(1, 6):
                    block_type = choice([b[0] for b in BLOCK_TYPE])
                    content = f"Lorem Ipsum {k}"
                    Block.objects.create(
                        page=page, block_type=block_type, content=content
                    )
            else:
                Page.objects.create(notebook=notebook, title="Page without blocks")

        self.stdout.write("Sample data created successfully!")
