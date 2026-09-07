from django.contrib import admin
from .models import Activity, Chore, ChoreShare, Comment, Completion, Household, Invitation, Membership, Notification, NotificationPreference

admin.site.register([Household, Membership, Invitation, Chore, ChoreShare, Completion, Comment, Activity, Notification, NotificationPreference])

# Register your models here.
