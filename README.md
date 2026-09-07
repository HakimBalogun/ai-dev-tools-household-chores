# AI Dev Tools Household Chores

Homework repository for Module 1 of the DataTalksClub AI Dev Tools Zoomcamp.

## Application

Homebase is a Django/SQLite household chore manager with real Django authentication, multiple households, registered-user invitations, selective chore sharing, comments, activity history, in-app notifications, and owner-only monitoring.

## Setup and running

This project uses Django and `uv` for dependency management. Start the local development server with:

```bash
uv run python manage.py runserver
```

Run database migrations with `uv run python manage.py migrate`; register from `/register/`, or create a Django superuser with `uv run python manage.py createsuperuser`. Run tests with `uv run python manage.py test`.

Run `uv run python manage.py process_chore_notifications` periodically (for example daily) to create in-app notifications. It sends reminders one day before a due date to eligible current recipients and overdue notices to the current household admin. Repeated command runs are deduplicated.

## Implementation decisions

- Invitations are visible in-app and can only target existing registered usernames; the recipient explicitly accepts.
- A chore has one optional assignee. Recurrence is stored as none/daily/weekly/monthly; completing a recurring chore records completion but does not automatically create its next instance.
- Dates use Django's timezone-aware UTC configuration. Notifications are persistent in-app only.
- Chore creators/assignees can see their chores; only the household admin can change chore details or sharing. Explicit recipients may view, complete, and comment.
- Household deletion, automatic recurrence generation, email/push delivery, and comment moderation are intentionally out of scope.

The project is named `household_chores` and the application domain lives in the `chores` Django app. The root page is a Django-rendered foundation only; household, authentication, and chore functionality will be implemented in later backlog tasks.
