from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class Household(models.Model):
    name = models.CharField(max_length=120)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="owned_households")
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return self.name
    def is_member(self, user): return self.memberships.filter(user=user).exists()
    def is_owner(self, user): return self.owner_id == user.id and self.is_member(user)


class Membership(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="household_memberships")
    joined_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["household", "user"], name="unique_household_member")]
        ordering = ["user__username"]


class Invitation(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="invitations")
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="chore_invitations")
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="sent_chore_invitations")
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["household", "invited_user"], name="unique_household_invitation")]


class Chore(models.Model):
    class Recurrence(models.TextChoices):
        NONE = "none", "Does not repeat"
        DAILY = "daily", "Daily"
        WEEKLY = "weekly", "Weekly"
        MONTHLY = "monthly", "Monthly"
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="chores")
    title = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="created_chores")
    assignee = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="assigned_chores")
    due_date = models.DateField(null=True, blank=True)
    recurrence = models.CharField(max_length=10, choices=Recurrence.choices, default=Recurrence.NONE)
    completed_at = models.DateTimeField(null=True, blank=True)
    share_with_all = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta: ordering = ["completed_at", "due_date", "-created_at"]
    @property
    def is_completed(self): return self.completed_at is not None
    @property
    def is_overdue(self): return bool(self.due_date and self.due_date < timezone.localdate() and not self.is_completed)
    def clean(self):
        # ModelForm validation happens before the create view attaches household.
        if self.assignee_id and self.household_id and not self.household.is_member(self.assignee):
            raise ValidationError({"assignee": "Assignee must be a current household member."})


class ChoreShare(models.Model):
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name="shares")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shared_chores")
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["chore", "user"], name="unique_chore_share")]
    def clean(self):
        if not self.chore.household.is_member(self.user): raise ValidationError("Share target must be a current household member.")


class Completion(models.Model):
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name="completion_history")
    completed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    completed_at = models.DateTimeField(auto_now_add=True)


class Comment(models.Model):
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    text = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["created_at"]


class Activity(models.Model):
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="activities")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    event_type = models.CharField(max_length=40)
    message = models.CharField(max_length=300)
    chore = models.ForeignKey(Chore, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["-created_at"]


class NotificationPreference(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preferences")
    reminders = models.BooleanField(default=True)
    overdue = models.BooleanField(default=True)
    activity = models.BooleanField(default=True)
    admin_transfer = models.BooleanField(default=True)


class Notification(models.Model):
    class Category(models.TextChoices):
        REMINDER = "reminder", "Approaching due date"
        OVERDUE = "overdue", "Overdue chore"
        ACTIVITY = "activity", "Activity"
        ADMIN = "admin", "Admin transfer"
    recipient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications")
    household = models.ForeignKey(Household, on_delete=models.CASCADE, related_name="notifications")
    chore = models.ForeignKey(Chore, on_delete=models.CASCADE, null=True, blank=True)
    category = models.CharField(max_length=12, choices=Category.choices)
    message = models.CharField(max_length=300)
    event_key = models.CharField(max_length=160)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["recipient", "event_key", "category"], name="unique_notification_event_recipient")]
        ordering = ["-created_at"]
