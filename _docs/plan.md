# Household Chores Application — Implementation Plan

## Product overview

Build a responsive web application for households to manage shared chores. Registered users may participate in more than one household. Within each household, members can create, assign, complete, and discuss chores, while the household admin has the visibility and controls needed to oversee the household.

Chore visibility is intentionally selective: household membership alone does not expose every chore. A user sees chores they manage or assign, plus chores explicitly shared with them by the household admin. The product has no points, scores, leaderboards, or other gamification.

## Goals

- Let anyone create an account and take part in one or more households.
- Support clear household membership and administration, including safe ownership transfer.
- Make chores actionable through assignment, deadlines, recurrence, completion, and comments.
- Preserve privacy through explicit per-chore sharing.
- Give the household admin an overview of pending, completed, and overdue work, plus relevant member activity history.
- Deliver useful, configurable reminders and activity notifications without duplicate messages.
- Provide a usable experience on both mobile and desktop screen sizes.

## Core features

### Accounts and households

- Account creation and authenticated access.
- Creation of a household; its creator becomes the initial owner/admin.
- Membership in multiple households.
- Invitation of already registered users by a household owner/admin.
- Leaving a household and removal of members by its owner/admin.
- Owner/admin transfer to an existing household member before the current owner/admin leaves.
- Notification to the member who becomes the new admin.
- Household-scoped access so former members immediately lose access to that household's chores and activities.

### Chores

- Create a chore within a household.
- Assign a chore to a user or users as supported by the eventual data model and UI; the exact cardinality of assignment should be confirmed during implementation.
- Add an optional due date/deadline.
- Configure recurrence.
- Mark a chore complete.
- Add comments to a chore.
- Share a chore, as an owner/admin, with one selected member, multiple selected members, or all household members.
- Allow shared recipients to view, complete, and comment on the shared chore.
- Restrict changes to assignment, due date, recurrence, and sharing settings to users with the required management authority.

### Admin monitoring

- Household dashboard/overview for the owner/admin.
- Admin visibility into pending, completed, and overdue chores.
- Admin visibility into relevant member activity and completed-chore history.

### Notifications

- Configurable per-user notification preferences.
- Advance due-date reminders.
- Overdue notifications to the household owner/admin, subject to preferences.
- Notifications for relevant completion and activity events.
- Notification when a member becomes a household admin.

## User roles and permissions

Permissions must always be evaluated in the context of one household. A user can have a different role in each household.

| Role or relationship | Allowed actions |
| --- | --- |
| Household owner/admin | Invite and remove household members; share chores; access household overview, chore status, activity, and history; transfer admin responsibility; receive applicable admin notifications. |
| Household member | Access only chores they manage/assign or that the admin has explicitly shared with them; complete and comment on chores they can access; leave the household; configure their own notifications. |
| Chore manager/assigner | Can see the chore they manage or assigned. Whether this relationship grants any editing rights beyond those explicitly required must be determined during implementation. |
| Shared chore recipient | Can view, mark complete, and comment. Cannot change assignment, due date, recurrence, or sharing settings unless separately authorized as an owner/admin manager. |
| Non-member / former member | Cannot access the household's chores or activities. |

The application should enforce these rules on the server/API as well as in the interface; hiding a screen alone is not an authorization mechanism.

## Main workflows

### Create and join households

1. A person creates an account and signs in.
2. They create a household and become its owner/admin, or receive an invitation to a household where they are already a registered user.
3. The household member list reflects the new membership.
4. The user selects a household before viewing household-specific chores or activity.

The invitation delivery, acceptance flow, and treatment of invitations to non-registered people are not specified. The agreed requirement is inviting registered users; choose an implementation approach that preserves that boundary.

### Leave, remove, and transfer administration

1. A member leaves a household, or an owner/admin removes a member.
2. Membership is revoked immediately and all household chore/activity access checks fail for that person from that point forward.
3. If the departing user is the current owner/admin, they first select another current household member as the new admin.
4. The system transfers responsibility, records the relevant activity, and notifies the new admin.
5. The household retains one designated admin at all times.

### Create, assign, and share a chore

1. An authorized user selects a household and creates a chore.
2. They set assignment and optional deadline/recurrence details as applicable.
3. The household owner/admin chooses whether to share it with selected same-household members or everyone in the household.
4. The system rejects any attempted sharing target who is not a current member of that household.
5. Eligible users see the chore according to the visibility rules and can take their permitted actions.

### Complete and discuss a chore

1. A user with chore access opens it.
2. The user marks it complete and/or adds a comment.
3. The system records the event in relevant history/activity views.
4. It sends relevant notifications according to recipients' preferences while deduplicating recipients.

### Due dates, reminders, and overdue status

1. Before a chore's due date, eligible recipients may receive advance reminders according to their notification settings.
2. When the due date passes and the chore remains incomplete, it becomes overdue.
3. The household owner/admin receives the overdue notification if enabled in their preferences.
4. The dashboard and appropriate chore status views reflect the overdue state.

The exact reminder lead times, delivery channels, scheduling mechanism, time-zone handling, and recurring-chore completion behavior must be determined during implementation.

## Business rules

- A user must be a current member of a household before they can access that household's chores or activities.
- A user may belong to multiple households; data and permissions remain isolated by household.
- Each active household always has exactly one designated owner/admin unless a future product decision explicitly introduces multiple admins.
- The current owner/admin cannot leave until responsibility has been transferred to another current member.
- Only an owner/admin can invite or remove members, share chores, access the admin dashboard, and manage household-wide monitoring.
- Removal or departure revokes household access immediately, including access previously obtained through chore sharing.
- A chore may only be shared with current members of the same household.
- Household membership does not, by itself, grant access to all chores.
- A user can see a chore when they assigned/manage it or when the household owner/admin explicitly shared it with them.
- Shared recipients may view, complete, and comment, but cannot alter assignment, deadline, recurrence, or sharing unless they separately have owner/admin management permission.
- A chore is overdue only when it has a due date, that due date has passed, and the chore remains incomplete.
- Completion and relevant activity should be retained in history for admin monitoring.
- Notification preferences may reduce or disable notification types. Recipient selection must remove duplicates, including when the owner/admin is also another relevant recipient.

Details such as deletion versus archival of chores, editing permissions for creators/managers, comment moderation, household deletion, and member-role names beyond the designated owner/admin are intentionally not product decisions in this plan and should be resolved before their corresponding implementation tasks.

## Data and domain concepts likely needed

The exact schema and technology are implementation decisions, but the following concepts are expected:

| Concept | Purpose |
| --- | --- |
| User | Account identity and personal notification preferences. |
| Household | A shared organizational boundary with a designated owner/admin. |
| Household membership | Connects users to households and captures the household-specific role/status needed for access control. |
| Invitation | Represents an admin's invitation of a registered user and its lifecycle, if an explicit acceptance flow is used. |
| Chore | Household-scoped work item with creator/manager or assigner relationship, status, due-date, and recurrence information. |
| Chore assignment | Captures who a chore is assigned to; model shape to be finalized once single versus multiple assignment is decided. |
| Chore share/access grant | Records explicit recipient visibility for a chore, including an efficient representation for “everyone in the household.” |
| Comment | Chore discussion entry with author and timestamp. |
| Completion record / status history | Records completion and supports completed-chore history, including recurring instances if applicable. |
| Activity event | Auditable household events such as completion, comments, membership changes, and admin transfer. |
| Notification preference | A user's opt-in/out choices by notification type. |
| Notification event / delivery | Tracks generated notifications and supports deduplication and delivery state. |

The model should preserve enough actor, household, chore, recipient, and timestamp context to enforce permissions and render the admin history/dashboard.

## Notification behavior

- Users control notification types and can reduce or disable notifications through their preferences.
- Assigned users may receive applicable notifications according to their preferences.
- Advance reminders are generated before a due date for applicable recipients; timing is to be determined.
- If an incomplete chore passes its due date, the household owner/admin is notified if they allow overdue notifications.
- Relevant completion and activity events generate notifications for the applicable audience, subject to preferences.
- A newly designated owner/admin receives a role-change notification.
- Before delivery, notification recipients are deduplicated so one person receives at most one notification for the same event and notification type, even if they qualify in multiple ways.
- Notification generation must respect current household membership and authorization at the time it is processed, especially after removals or departures.

The precise event-to-recipient mapping, notification channels, retry policy, digest behavior, and preference defaults remain to be determined during implementation.

## Non-goals and explicit exclusions

- No points, scores, rewards, leaderboards, streaks, or other gamification.
- No implicit visibility of every household member's chores.
- No cross-household chore sharing or access.
- No ability for a shared recipient to change assignment, deadline, recurrence, or sharing settings solely because a chore was shared with them.
- No access to household chores or activity for users who are not current members.
- No application implementation is included in this planning stage.

## Sensible implementation sequence

1. Establish the application foundation: authentication, responsive layout baseline, and household selection/context. Confirm the implementation decisions that affect the rest of the model, especially invitation acceptance, assignment cardinality, recurrence semantics, time zones, and notification channels.
2. Implement household and membership persistence plus server-enforced household authorization. Add household creation, member listing, registered-user invitations, leaving, removal, and safe admin transfer with the invariant that every active household has an admin.
3. Implement chore persistence and core interfaces: household-scoped creation, assignment/manager relationship, optional due date, recurrence representation, completion state, and comments.
4. Implement chore visibility and sharing rules. Add admin sharing to selected members or all members, validate targets, and enforce view/action permissions for managers/assigners and recipients.
5. Build the admin dashboard and history/activity views, deriving pending, completed, and overdue states correctly from chore data.
6. Implement notification preferences, notification event creation, recipient selection/deduplication, due-date reminder scheduling, overdue processing, completion/activity notifications, and admin-transfer notification.
7. Complete responsive UX work across core flows, including mobile and desktop checks, empty/error states, and accessibility considerations.
8. Add automated tests for authorization boundaries, membership revocation, admin-transfer invariants, chore sharing, overdue calculation, notification preferences, and duplicate-recipient prevention. Perform end-to-end validation of the main workflows.

Each implementation phase should be decomposed into small, independently testable tasks only after the unresolved implementation decisions relevant to that phase have been made.
