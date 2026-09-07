from django.db import transaction
from .models import Activity, Membership, Notification, NotificationPreference

def record_activity(household, actor, event_type, message, chore=None):
    return Activity.objects.create(household=household, actor=actor, event_type=event_type, message=message, chore=chore)

def notify(user, household, category, message, event_key, chore=None):
    if not Membership.objects.filter(household=household, user=user).exists(): return None
    prefs, _ = NotificationPreference.objects.get_or_create(user=user)
    field = {"reminder": "reminders", "overdue": "overdue", "activity": "activity", "admin": "admin_transfer"}[category]
    if not getattr(prefs, field): return None
    return Notification.objects.get_or_create(recipient=user, event_key=event_key, category=category, defaults={"household": household, "chore": chore, "message": message})[0]

@transaction.atomic
def transfer_owner(household, old_owner, new_owner):
    if household.owner_id != old_owner.id or not Membership.objects.filter(household=household, user=new_owner).exists(): raise ValueError("New owner must be a current household member.")
    household.owner = new_owner; household.save(update_fields=["owner"])
    record_activity(household, old_owner, "admin_transfer", f"{new_owner.username} became household admin.")
    notify(new_owner, household, "admin", "You are now the household admin.", f"admin-transfer-{household.pk}-{new_owner.pk}")
