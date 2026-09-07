# Household Chores Application Backlog

This backlog converts `_docs/plan.md` into small, independently executable implementation tasks. Items that depend on an unresolved product or technical decision explicitly call that out rather than selecting a solution prematurely.

## Task 1 — Establish the application foundation

Create the initial responsive web-application structure, including a documented approach for authentication, an authenticated application shell, and a place to select the active household once households exist.

Acceptance criteria / constraints:

- The foundation supports account creation and signed-in access.
- The shell has a responsive baseline suitable for desktop and mobile.
- Household-specific routes or views can require an active household context.
- Select technology and authentication details consistent with the existing project; do not make unrelated product changes.

## Task 2 — Record deferred domain decisions

Document the implementation decisions that must be made before dependent tasks: invitation acceptance and delivery, single versus multiple chore assignees, recurrence semantics, time-zone handling, reminder timing, notification channels, and recurring-chore completion behavior.

Acceptance criteria / constraints:

- Preserve the requirement that only registered users may be invited.
- Do not decide behavior not agreed in the plan without recording it as an implementation decision.
- Resolve only the decisions needed to unblock the next tasks; leave unrelated non-goals unchanged.

## Task 3 — Add household and membership persistence

Implement the data model and persistence for households and household memberships, including a household-scoped owner/admin designation.

Acceptance criteria / constraints:

- A user can belong to multiple households.
- Membership and roles are scoped to one household.
- Every active household has one designated owner/admin.
- Data design supports immediate membership revocation and household isolation.

## Task 4 — Create households and select the active household

Implement the signed-in flow for creating a household and selecting between a user's households.

Acceptance criteria / constraints:

- The household creator becomes its initial owner/admin.
- A user can switch between households they currently belong to.
- Users cannot select or access a household where they are not a current member.

## Task 5 — Enforce household access at the server/API boundary

Add reusable authorization checks that require current membership for all household-scoped data and actions.

Acceptance criteria / constraints:

- Non-members and former members cannot access that household's chores or activities.
- Enforcement occurs at the server/API layer, not only by hiding interface controls.
- A user's data and permissions in one household do not expose another household's data.

## Task 6 — Invite registered users to a household

Implement the owner/admin flow to invite a registered user to their household, using the invitation lifecycle chosen in Task 2.

Acceptance criteria / constraints:

- Only a household owner/admin can invite.
- The target must be a registered user.
- A successful invitation results in a current membership only according to the chosen acceptance flow.
- Invitation and membership changes remain household-scoped.

## Task 7 — Implement household departure and member removal

Implement member self-service departure and owner/admin removal of another household member.

Acceptance criteria / constraints:

- Only an owner/admin can remove members.
- Departed or removed users immediately lose access to household chores and activities, including chores previously shared with them.
- The action should be represented in relevant activity history when that history is added.

## Task 8 — Transfer admin responsibility safely

Implement admin transfer to another current household member and prevent the current admin from leaving until the transfer succeeds.

Acceptance criteria / constraints:

- The new admin must already be a current member of the same household.
- The household must retain a designated admin throughout the operation.
- Record an admin-transfer activity event and trigger the new-admin notification through the notification system when it exists.

## Task 9 — Add household chore and assignment data

Implement the core chore model and household-scoped creation flow, including the creator/manager or assigner relationship and assignment representation.

Acceptance criteria / constraints:

- Chores belong to exactly one household.
- Confirm and use the assignee cardinality decided in Task 2; do not silently assume single or multiple assignment.
- The model supports later due dates, recurrence, completion, comments, and explicit sharing.

## Task 10 — Implement chore details, completion, and comments

Add optional due dates, the chosen recurrence representation, completion state/history, and chore comments.

Acceptance criteria / constraints:

- A user with permitted chore access can mark it complete and add comments.
- Completion and comments retain actor and timestamp context for later history/activity views.
- Recurrence behavior follows the decision documented in Task 2.

## Task 11 — Implement baseline chore visibility rules

Implement server/API and UI checks that allow a current household member to see a chore they manage or assigned, but do not expose all household chores by default.

Acceptance criteria / constraints:

- Household membership alone does not grant access to every chore.
- Non-members and former members cannot access a chore, even through a direct URL or API request.
- Any editing authority beyond the explicitly specified rules should follow a documented implementation decision.

## Task 12 — Add admin chore sharing controls

Implement owner/admin sharing of a chore with one selected member, multiple selected members, or everyone in that household.

Acceptance criteria / constraints:

- Only the household owner/admin can manage sharing.
- Every selected recipient must be a current member of the same household.
- Reject cross-household recipients.
- The data model supports both selected-recipient and everyone-in-household sharing.

## Task 13 — Enforce shared-recipient permissions

Implement the access grant for a shared recipient and restrict the actions available to them.

Acceptance criteria / constraints:

- A shared recipient can view, complete, and comment on the chore.
- Sharing alone does not permit changing assignment, due date, recurrence, or sharing settings.
- Separate owner/admin management permission may permit those management actions.

## Task 14 — Capture household activity events

Implement a durable activity-event model and record relevant events from already implemented flows, including completions, comments, membership changes, and admin transfers.

Acceptance criteria / constraints:

- Events retain enough household, actor, related-chore (when applicable), and timestamp information for history views.
- Only users authorized for household activity can access it.
- Do not introduce event types outside the planned feature set unless required for implementation traceability.

## Task 15 — Build the admin household dashboard

Implement the owner/admin overview showing pending, completed, and overdue chores plus relevant member activity and completed-chore history.

Acceptance criteria / constraints:

- Only the household owner/admin can access the dashboard and monitoring views.
- A chore is overdue only if it has a due date, remains incomplete, and its due date has passed.
- Dashboard data is limited to the active household.

## Task 16 — Add notification preferences

Implement per-user controls to enable, reduce, or disable notification types.

Acceptance criteria / constraints:

- Preferences are owned by the user and apply before a notification is delivered.
- Support the planned categories: advance reminders, overdue/admin notifications, relevant completion/activity events, and new-admin role notifications.
- Defaults and any more detailed preference grouping follow a documented implementation decision.

## Task 17 — Create notification events with recipient deduplication

Implement notification-event creation for relevant completion/activity events and admin-role transfers, including recipient selection and delivery tracking.

Acceptance criteria / constraints:

- Respect each recipient's preferences.
- A user receives no more than one notification for the same event and notification type, even if they qualify through multiple relationships.
- Validate current household membership and authorization when processing recipients, particularly after removal or departure.
- New admins receive the role-change notification.

## Task 18 — Implement due-date reminders and overdue processing

Implement the scheduled/background processing chosen in Task 2 for advance reminders and overdue detection.

Acceptance criteria / constraints:

- Advance reminders occur before a due date for applicable recipients who allow them.
- An incomplete chore becomes overdue once its due date passes.
- The household owner/admin receives the overdue notification if their preferences permit it.
- Time-zone, reminder lead-time, scheduling, retries, and delivery-channel behavior follow the documented decisions from Task 2.

## Task 19 — Complete responsive and accessible core workflows

Review and refine the implemented account, household, chore, sharing, dashboard, and notification-preference screens for desktop and mobile use.

Acceptance criteria / constraints:

- Core workflows work well on mobile and desktop widths.
- Provide appropriate loading, empty, validation, and authorization-error states.
- Preserve the same permission rules regardless of viewport or navigation path.

## Task 20 — Add authorization and domain-rule tests

Add automated tests for the core security and business-rule boundaries.

Acceptance criteria / constraints:

- Cover household isolation, non-member access denial, and immediate access revocation after removal/departure.
- Cover the single-admin invariant and required transfer before an admin leaves.
- Cover chore visibility, same-household sharing validation, and shared-recipient action limits.
- Cover overdue calculation, notification preferences, and duplicate-recipient prevention.

## Task 21 — Validate end-to-end main workflows

Run end-to-end validation of the principal user journeys and correct implementation defects found within the agreed scope.

Acceptance criteria / constraints:

- Validate create account, create/select household, invite registered user, leave/remove, and admin transfer.
- Validate create/assign/share/complete/comment chore flows and their permissions.
- Validate admin monitoring, advance reminders, overdue notifications, activity notifications, and new-admin notification behavior.
- Confirm that no scoring, points, leaderboards, or other gamification has been added.
