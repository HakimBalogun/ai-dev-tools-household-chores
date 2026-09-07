from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Chore, Comment, Household, NotificationPreference

class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    class Meta(UserCreationForm.Meta): model = User; fields = ("username", "email", "password1", "password2")
class HouseholdForm(forms.ModelForm):
    class Meta: model = Household; fields = ("name",)
class InviteForm(forms.Form): username = forms.CharField(max_length=150)
class ChoreForm(forms.ModelForm):
    class Meta:
        model = Chore; fields = ("title", "description", "assignee", "due_date", "recurrence")
        widgets = {"due_date": forms.DateInput(attrs={"type": "date"})}
    def __init__(self, *args, household, **kwargs):
        super().__init__(*args, **kwargs); self.fields["assignee"].queryset = User.objects.filter(household_memberships__household=household).distinct()
class CommentForm(forms.ModelForm):
    class Meta: model = Comment; fields = ("text",); widgets = {"text": forms.Textarea(attrs={"rows": 3, "placeholder": "Add a comment"})}
class ShareForm(forms.Form):
    share_with_all = forms.BooleanField(required=False, label="Share with everyone in this household")
    recipients = forms.ModelMultipleChoiceField(queryset=User.objects.none(), required=False, widget=forms.CheckboxSelectMultiple)
    def __init__(self, *args, household, **kwargs):
        super().__init__(*args, **kwargs); self.fields["recipients"].queryset = User.objects.filter(household_memberships__household=household).distinct()
class PreferenceForm(forms.ModelForm):
    class Meta: model = NotificationPreference; fields = ("reminders", "overdue", "activity", "admin_transfer")
