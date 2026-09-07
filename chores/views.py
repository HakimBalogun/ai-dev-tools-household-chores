from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from .forms import *
from .models import *
from .services import notify, record_activity, transfer_owner

def home(r): return redirect('chores:households') if r.user.is_authenticated else render(r,'chores/home.html')
def register(r):
    if r.user.is_authenticated:return redirect('chores:households')
    f=RegisterForm(r.POST or None)
    if r.method=='POST' and f.is_valid():
        u=f.save();NotificationPreference.objects.create(user=u);login(r,u);return redirect('chores:households')
    return render(r,'chores/form.html',{'form':f,'title':'Create your account'})
@login_required
def households(r):return render(r,'chores/households.html',{'memberships':r.user.household_memberships.select_related('household'),'invitations':r.user.chore_invitations.filter(accepted=False).select_related('household')})
@login_required
def household_create(r):
    f=HouseholdForm(r.POST or None)
    if r.method=='POST' and f.is_valid():
        with transaction.atomic():
            h=f.save(commit=False);h.owner=r.user;h.save();Membership.objects.create(household=h,user=r.user);record_activity(h,r.user,'household_created',f'{h.name} was created.')
        return redirect('chores:dashboard',household_id=h.id)
    return render(r,'chores/form.html',{'form':f,'title':'Create household'})
def hh(r,i):
    h=get_object_or_404(Household,pk=i)
    if not h.is_member(r.user):raise Http404('Household not found')
    return h
def can(c,u):return c.household.is_member(u) and (c.household.is_owner(u) or c.creator_id==u.id or c.assignee_id==u.id or c.share_with_all or c.shares.filter(user=u).exists())
@login_required
def dashboard(r,household_id):
    h=hh(r,household_id);cs=Chore.objects.filter(household=h) if h.is_owner(r.user) else Chore.objects.filter(household=h).filter(Q(creator=r.user)|Q(assignee=r.user)|Q(share_with_all=True)|Q(shares__user=r.user)).distinct()
    return render(r,'chores/dashboard.html',{'household':h,'chores':cs,'is_owner':h.is_owner(r.user)})
@login_required
def members(r,household_id):
    h=hh(r,household_id);return render(r,'chores/members.html',{'household':h,'memberships':h.memberships.select_related('user'),'is_owner':h.is_owner(r.user),'invite_form':InviteForm()})
@login_required
@require_POST
def invite(r,household_id):
    h=hh(r,household_id)
    if not h.is_owner(r.user):return HttpResponseForbidden()
    f=InviteForm(r.POST)
    if f.is_valid():
        try:u=User.objects.get(username=f.cleaned_data['username'])
        except User.DoesNotExist:messages.error(r,'That registered user does not exist.')
        else:
            if h.is_member(u):messages.error(r,'User is already a member.')
            else:Invitation.objects.update_or_create(household=h,invited_user=u,defaults={'invited_by':r.user,'accepted':False});record_activity(h,r.user,'invited',f'{u.username} was invited.')
    return redirect('chores:members',household_id=h.id)
@login_required
@require_POST
def accept_invitation(r,invitation_id):
    i=get_object_or_404(Invitation,pk=invitation_id,invited_user=r.user,accepted=False);Membership.objects.get_or_create(household=i.household,user=r.user);i.accepted=True;i.save();record_activity(i.household,r.user,'invitation_accepted',f'{r.user.username} joined.');return redirect('chores:dashboard',household_id=i.household_id)
@login_required
@require_POST
def remove_member(r,household_id,user_id):
    h=hh(r,household_id)
    if not h.is_owner(r.user) or user_id==h.owner_id:return HttpResponseForbidden()
    m=get_object_or_404(Membership,household=h,user_id=user_id);n=m.user.username;m.delete();record_activity(h,r.user,'member_removed',f'{n} was removed.');return redirect('chores:members',household_id=h.id)
@login_required
@require_POST
def leave_household(r,household_id):
    h=hh(r,household_id)
    if h.is_owner(r.user):messages.error(r,'Transfer household administration before leaving.');return redirect('chores:members',household_id=h.id)
    Membership.objects.filter(household=h,user=r.user).delete();record_activity(h,r.user,'member_left',f'{r.user.username} left.');return redirect('chores:households')
@login_required
@require_POST
def transfer(r,household_id):
    h=hh(r,household_id)
    if not h.is_owner(r.user):return HttpResponseForbidden()
    try:transfer_owner(h,r.user,get_object_or_404(User,pk=r.POST.get('user_id')))
    except ValueError:return HttpResponseForbidden()
    return redirect('chores:members',household_id=h.id)
@login_required
def chore_create(r,household_id):
    h=hh(r,household_id);f=ChoreForm(r.POST or None,household=h)
    if r.method=='POST' and f.is_valid():
        c=f.save(commit=False);c.household=h;c.creator=r.user;c.full_clean();c.save();record_activity(h,r.user,'chore_created',f'Created: {c.title}',c);return redirect('chores:chore_detail',household_id=h.id,chore_id=c.id)
    return render(r,'chores/form.html',{'form':f,'title':'New chore'})
@login_required
def chore_detail(r,household_id,chore_id):
    h=hh(r,household_id);c=get_object_or_404(Chore,pk=chore_id,household=h)
    if not can(c,r.user):raise Http404('Chore not found')
    return render(r,'chores/chore_detail.html',{'household':h,'chore':c,'comment_form':CommentForm(),'can_manage':h.is_owner(r.user),'share_form':ShareForm(household=h,initial={'share_with_all':c.share_with_all,'recipients':c.shares.values_list('user',flat=True)})})
@login_required
def chore_edit(r,household_id,chore_id):
    h=hh(r,household_id);c=get_object_or_404(Chore,pk=chore_id,household=h)
    if not h.is_owner(r.user):return HttpResponseForbidden()
    f=ChoreForm(r.POST or None,instance=c,household=h)
    if r.method=='POST' and f.is_valid():f.save();return redirect('chores:chore_detail',household_id=h.id,chore_id=c.id)
    return render(r,'chores/form.html',{'form':f,'title':'Edit chore'})
@login_required
@require_POST
def complete_chore(r,household_id,chore_id):
    h=hh(r,household_id);c=get_object_or_404(Chore,pk=chore_id,household=h)
    if not can(c,r.user):raise Http404()
    if not c.is_completed:
        c.completed_at=timezone.now();c.save();Completion.objects.create(chore=c,completed_by=r.user);record_activity(h,r.user,'chore_completed',f'Completed: {c.title}',c)
        for u in {h.owner,c.creator,c.assignee}-{None,r.user}:notify(u,h,'activity',f'{r.user.username} completed {c.title}.',f'completion-{c.id}',c)
    return redirect('chores:chore_detail',household_id=h.id,chore_id=c.id)
@login_required
@require_POST
def add_comment(r,household_id,chore_id):
    h=hh(r,household_id);c=get_object_or_404(Chore,pk=chore_id,household=h)
    if not can(c,r.user):raise Http404()
    f=CommentForm(r.POST)
    if f.is_valid():x=f.save(commit=False);x.chore=c;x.author=r.user;x.save();record_activity(h,r.user,'comment',f'Commented on {c.title}',c)
    return redirect('chores:chore_detail',household_id=h.id,chore_id=c.id)
@login_required
@require_POST
def share_chore(r,household_id,chore_id):
    h=hh(r,household_id);c=get_object_or_404(Chore,pk=chore_id,household=h)
    if not h.is_owner(r.user):return HttpResponseForbidden()
    f=ShareForm(r.POST,household=h)
    if f.is_valid():
        c.share_with_all=f.cleaned_data['share_with_all'];c.save();ChoreShare.objects.filter(chore=c).exclude(user__in=f.cleaned_data['recipients']).delete()
        for u in f.cleaned_data['recipients']:ChoreShare.objects.get_or_create(chore=c,user=u)
        record_activity(h,r.user,'chore_shared',f'Updated sharing: {c.title}',c)
    return redirect('chores:chore_detail',household_id=h.id,chore_id=c.id)
@login_required
def admin_dashboard(r,household_id):
    h=hh(r,household_id)
    if not h.is_owner(r.user):return HttpResponseForbidden()
    cs=list(h.chores.all());return render(r,'chores/admin_dashboard.html',{'household':h,'pending':[c for c in cs if not c.is_completed],'completed':[c for c in cs if c.is_completed],'overdue':[c for c in cs if c.is_overdue],'activities':h.activities.all()[:20]})
@login_required
def notifications(r):return render(r,'chores/notifications.html',{'notifications':r.user.notifications.select_related('household','chore')})
@login_required
def preferences(r):
    p,_=NotificationPreference.objects.get_or_create(user=r.user);f=PreferenceForm(r.POST or None,instance=p)
    if r.method=='POST' and f.is_valid():f.save();return redirect('chores:preferences')
    return render(r,'chores/form.html',{'form':f,'title':'Notification preferences'})
