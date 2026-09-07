from datetime import timedelta
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from .models import Chore, ChoreShare, Household, Invitation, Membership, Notification, NotificationPreference

class AppTests(TestCase):
    def setUp(self):
        self.owner=User.objects.create_user('owner',password='StrongPass123!')
        self.member=User.objects.create_user('member',password='StrongPass123!')
        self.other=User.objects.create_user('other',password='StrongPass123!')
        self.h=Household.objects.create(name='Home',owner=self.owner)
        Membership.objects.create(household=self.h,user=self.owner)
        Membership.objects.create(household=self.h,user=self.member)
    def login(self,u): self.client.force_login(u)
    def test_registration_and_login_protection(self):
        response=self.client.get(reverse('chores:households'));self.assertEqual(response.status_code,302)
        response=self.client.post(reverse('chores:register'),{'username':'new','email':'n@example.com','password1':'ThisPass123!','password2':'ThisPass123!'})
        self.assertTrue(User.objects.filter(username='new').exists());self.assertEqual(response.status_code,302)
    def test_household_creation_owner_and_multiple_memberships(self):
        self.login(self.owner);self.client.post(reverse('chores:household_create'),{'name':'Second'})
        h=Household.objects.get(name='Second');self.assertEqual(h.owner,self.owner);self.assertTrue(h.is_member(self.owner));self.assertEqual(self.owner.household_memberships.count(),2)
    def test_isolation_and_removal_revocation(self):
        c=Chore.objects.create(household=self.h,title='Private',creator=self.owner)
        self.login(self.member);self.assertEqual(self.client.get(reverse('chores:chore_detail',args=[self.h.id,c.id])).status_code,404)
        ChoreShare.objects.create(chore=c,user=self.member);self.assertEqual(self.client.get(reverse('chores:chore_detail',args=[self.h.id,c.id])).status_code,200)
        self.client.force_login(self.owner);self.client.post(reverse('chores:remove_member',args=[self.h.id,self.member.id]))
        self.client.force_login(self.member);self.assertEqual(self.client.get(reverse('chores:dashboard',args=[self.h.id])).status_code,404)
    def test_invitation_acceptance(self):
        self.login(self.owner);self.client.post(reverse('chores:invite',args=[self.h.id]),{'username':'other'})
        i=Invitation.objects.get(household=self.h,invited_user=self.other);self.client.force_login(self.other);self.client.post(reverse('chores:accept_invitation',args=[i.id]))
        self.assertTrue(self.h.is_member(self.other));self.assertTrue(Invitation.objects.get(pk=i.id).accepted)
    def test_owner_must_transfer_before_leaving(self):
        self.login(self.owner);self.client.post(reverse('chores:leave_household',args=[self.h.id]));self.assertTrue(self.h.is_member(self.owner))
        self.client.post(reverse('chores:transfer',args=[self.h.id]),{'user_id':self.member.id});self.h.refresh_from_db();self.assertEqual(self.h.owner,self.member)
        self.client.force_login(self.owner);self.client.post(reverse('chores:leave_household',args=[self.h.id]));self.assertFalse(self.h.is_member(self.owner));self.assertTrue(Notification.objects.filter(recipient=self.member,category='admin').exists())
    def test_chore_creation_assignment_and_cross_household_rejection(self):
        self.login(self.owner);response=self.client.post(reverse('chores:chore_create',args=[self.h.id]),{'title':'Dishes','description':'','assignee':self.member.id,'due_date':'','recurrence':'weekly'})
        self.assertEqual(response.status_code,302);c=Chore.objects.get(title='Dishes');self.assertEqual(c.assignee,self.member)
        self.client.post(reverse('chores:chore_create',args=[self.h.id]),{'title':'Bad','description':'','assignee':self.other.id,'due_date':'','recurrence':'none'});self.assertFalse(Chore.objects.filter(title='Bad').exists())
    def test_selected_and_everyone_share_permissions(self):
        c=Chore.objects.create(household=self.h,title='Dishes',creator=self.owner)
        self.login(self.owner);self.client.post(reverse('chores:share_chore',args=[self.h.id,c.id]),{'recipients':[self.member.id]})
        self.client.force_login(self.member);self.assertEqual(self.client.get(reverse('chores:chore_detail',args=[self.h.id,c.id])).status_code,200);self.assertEqual(self.client.get(reverse('chores:chore_edit',args=[self.h.id,c.id])).status_code,403)
        self.client.force_login(self.owner);self.client.post(reverse('chores:share_chore',args=[self.h.id,c.id]),{'share_with_all':'on','recipients':[]});self.client.force_login(self.member);self.assertEqual(self.client.get(reverse('chores:chore_detail',args=[self.h.id,c.id])).status_code,200)
    def test_completion_comments_and_overdue(self):
        c=Chore.objects.create(household=self.h,title='Old',creator=self.owner,due_date=timezone.localdate()-timedelta(days=1));self.assertTrue(c.is_overdue)
        ChoreShare.objects.create(chore=c,user=self.member);self.login(self.member);self.client.post(reverse('chores:add_comment',args=[self.h.id,c.id]),{'text':'done soon'});self.client.post(reverse('chores:complete_chore',args=[self.h.id,c.id]));c.refresh_from_db();self.assertTrue(c.is_completed);self.assertFalse(c.is_overdue);self.assertEqual(c.comments.count(),1)
    def test_preferences_reminders_and_deduplication(self):
        c=Chore.objects.create(household=self.h,title='Tomorrow',creator=self.owner,assignee=self.member,due_date=timezone.localdate()+timedelta(days=1),share_with_all=True)
        call_command('process_chore_notifications');call_command('process_chore_notifications');self.assertEqual(Notification.objects.filter(chore=c,category='reminder').count(),2)
        p,_=NotificationPreference.objects.get_or_create(user=self.member);p.reminders=False;p.save();c2=Chore.objects.create(household=self.h,title='No ping',creator=self.owner,assignee=self.member,due_date=timezone.localdate()+timedelta(days=1));call_command('process_chore_notifications');self.assertFalse(Notification.objects.filter(chore=c2,recipient=self.member).exists())
    def test_overdue_notification_respects_current_owner_membership(self):
        c=Chore.objects.create(household=self.h,title='Late',creator=self.owner,due_date=timezone.localdate()-timedelta(days=1));call_command('process_chore_notifications');self.assertTrue(Notification.objects.filter(chore=c,recipient=self.owner,category='overdue').exists())
