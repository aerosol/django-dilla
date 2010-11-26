from django.core.management.base import BaseCommand
from optparse import make_option
from dilla import Dilla

class Command(BaseCommand):
    help = "command help"

    option_list = BaseCommand.option_list + (
    make_option('--cycles',
        action='store',
        dest='cycles',
        default=1,
        help='Number of spam cycles to perform'),
    )

    def handle(self, *args, **options):
        d = Dilla(apps = ['testapp'], \
                cycles = int(options['cycles']))

        apps, affected, filled, omitted = d.run()

        self.stdout.write("Dilla finished!\n\
        %d app(s) spammed %d row(s) affected, %d field(s) filled, %d field(s) ommited.\nThank you!)" % \
                (apps, affected, filled, omitted)
                )
