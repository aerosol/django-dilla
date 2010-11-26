from django.core.management.base import BaseCommand
from dilla import Dilla, spamlib

class Command(BaseCommand):
    help = "command help"

    def handle(self, *args, **options):
        d = Dilla(apps = ['testapp'], spamlib = spamlib)
        d.run()
