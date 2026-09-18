# Lesson 11 — Project templates page

## Goal and checkpoint

Match the original EngAnnWeb login page and app header, then build **only the Project templates page** in this lesson. The login page and password-change flow come from Lesson 10. The header keeps the original role-based navigation and ordering; pages other than Project templates are clear placeholders until their lessons.

**Branch:** `lesson/11-project-admin`

**Pull request:** `Lesson 11: match the project templates page`

Compare the local reference at `/home/Shared/assale02/EngAnnWeb/frontend/src/App.tsx` (`TemplatesPage`, `TemplateCard`, and `TemplateDialog`) and its `styles.css`. Follow the reference's page heading, compact add button, Search/Status/Type filters, cards, and create/edit dialog. Use the tutorial's `/api/templates/` endpoint for real data and actions.

## Template data

The template API returns a paginated list. Follow `next` pages through the same-origin `/api/templates/` path. A template has a name, unique key, project type (`dipser`, `cvip2020`, or `cvip2026`), description, configuration JSON, active flag, version, creator username, and timestamps. The configuration's `dimensions` array supplies the card chips. Older templates created before this lesson may have no recorded creator; show “Unknown” for those records.

The migration adds `project_type` and `created_by` to the tutorial model. The server assigns the creator from the authenticated administrator. It starts a new template at version 1 and increments the version after a successful edit. The frontend never chooses a creator or version. Existing templates default to DIPSER. `created_by` remains nullable for legacy rows, avoiding an invented creator during migration.

The tutorial still has the earlier unique `(key, version)` constraint. Later schema lessons can revisit whether to move to the original repository's unique-key rule. The form reports the backend's validation error either way.

## Build the page

Render the heading **Project templates** with the subtitle “Define reusable annotation schemas and behavior.” The reference's add button expands on hover or keyboard focus. Search matches name, key, and description; Status and Type filter the loaded cards. The count reflects the filtered and total records. Empty results explain whether to clear filters or create a first template.

Each card shows project type, version, and active state as badges, followed by name, description, dimensions from configuration, creator, and update date. Edit opens the populated dialog. Delete asks for confirmation; the API rejects deletion with `409` when a project uses that template, so keep the card and show the server's message. The dialog uses controlled inputs for name, key, type, active state, description, and configuration JSON. It generates a key from a new name until the user edits that key. Keep the entered values when JSON parsing or API validation fails. Move focus into the dialog and restore it when closed.

The Status, Type, and Project type menus use the shared `Dropdown` component so
their open state looks consistent across browsers. Its trigger exposes the
selected value, its options expose selection to assistive technology, and
Arrow keys, Enter, Escape, Tab, and outside clicks behave as expected. Test
keyboard selection as well as pointer selection.

The reference's default configuration contains action, affect, and engagement dimensions. The tutorial stores that JSON but does not yet interpret all of its annotation behavior. Project configuration and annotation workflows remain separate lessons.

Keep the template dialog's header and actions visible while the fields scroll
between them, especially when the JSON editor makes the form tall.

## Verify

Run:

```bash
make check
git diff --check
```

Manually sign in as an administrator, open **Project templates**, create a CVIP2026 template, filter by Type, edit its description, and check that its version increases. Try invalid JSON and a duplicate key; both should leave the dialog open. Delete an unused template, then try deleting one referenced by a project and check that the `409` message appears. The backend permission class remains authoritative: only administrators can write templates.

The visual scope of this checkpoint is the login page, the app header, and the Project templates page. The other navigation destinations are placeholders until their lessons; they should not be presented as finished workflows.
