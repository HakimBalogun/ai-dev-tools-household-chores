from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from chores.models import Chore
from chores.services import notify

class Command(BaseCommand):
    help = 'Create deduplicated one-day reminders and overdue notifications.'
    def handle(self, *args, **options):
        today = timezone.localdate()
        for chore in Chore.objects.filter(completed_at__isnull=True, due_date=today + timedelta(days=1)):
            recipients = set([chore.creator, chore.assignee]) - {None}
            recipients.update(chore.shares.values_list('user', flat=True))
            if chore.share_with_all: recipients.update(chore.household.memberships.values_list('user', flat=True))
            from django.contrib.auth import get_user_model
            User = get_user_model()
            for item in recipients:
                user = item if hasattr(item, 'pk') else User.objects.get(pk=item)
                notify(user, chore.household, 'reminder', f'{chore.title} is due tomorrow.', f'reminder-{chore.pk}-{today}', chore)
        for chore in Chore.objects.filter(completed_at__isnull=True, due_date__lt=today):
            notify(chore.household.owner, chore.household, 'overdue', f'{chore.title} is overdue.', f'overdue-{chore.pk}', chore)
        self.stdout.write(self.style.SUCCESS('Chore notifications processed.'))
