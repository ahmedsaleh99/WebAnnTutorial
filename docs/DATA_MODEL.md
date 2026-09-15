# Core data model

Lessons 5 and 8 establish the configuration and work-assignment domains.

```mermaid
erDiagram
    PROJECT_TEMPLATE ||--o{ PROJECT : configures
    PROJECT ||--o{ ANNOTATION_DIMENSION : owns
    ANNOTATION_DIMENSION ||--o{ ANNOTATION_LABEL : contains
    PROJECT ||--o{ SUBJECT : includes
    PROJECT ||--o{ VIDEO_ASSET : owns
    PROJECT ||--o{ TASK : owns
    TASK ||--o{ TASK_SUBJECT : selects
    SUBJECT ||--o{ TASK_SUBJECT : participates
    TASK ||--o{ VIDEO_VIEW : presents
    VIDEO_ASSET ||--o{ VIDEO_VIEW : supplies
    SUBJECT o|--o{ VIDEO_VIEW : identifies
    TASK ||--o{ ANNOTATION_JOB : assigns
    ANNOTATION_JOB ||--|{ ANNOTATION_WORK_ITEM : groups
    TASK_SUBJECT ||--o{ ANNOTATION_WORK_ITEM : scopes
    ANNOTATION_WORK_ITEM ||--o| ANNOTATION_RESULT : produces

    PROJECT_TEMPLATE {
        uuid id PK
        string key
        integer version
        json configuration
    }
    PROJECT {
        uuid id PK
        uuid template_id FK
        string key UK
        string status
        json configuration
    }
    ANNOTATION_DIMENSION {
        uuid id PK
        uuid project_id FK
        string key
        integer position
    }
    ANNOTATION_LABEL {
        uuid id PK
        uuid dimension_id FK
        string name
        string color
    }
    SUBJECT {
        uuid id PK
        uuid project_id FK
        string subject_id
        json attributes
    }
    VIDEO_ASSET {
        uuid id PK
        uuid project_id FK
        string source_type
        string processing_status
    }
    TASK {
        uuid id PK
        uuid project_id FK
        string key
        string status
    }
    TASK_SUBJECT {
        uuid id PK
        uuid task_id FK
        uuid subject_id FK
    }
    VIDEO_VIEW {
        uuid id PK
        uuid task_id FK
        uuid asset_id FK
        uuid subject_id FK
        string role
    }
    ANNOTATION_JOB {
        uuid id PK
        uuid task_id FK
        integer assigned_to_id FK
    }
    ANNOTATION_WORK_ITEM {
        uuid id PK
        uuid job_id FK
        uuid task_subject_id FK
        string status
    }
    ANNOTATION_RESULT {
        uuid id PK
        uuid work_item_id FK,UK
        json data
    }
```

## Invariants

- Template `(key, version)` pairs are unique and versions start at one.
- Project keys are globally unique and status is constrained to a known value.
- Dimension keys are unique within a project.
- Label names are unique within a dimension; colors use `#RRGGBB` syntax.
- Subject identifiers are unique within a project.
- Deleting a project cascades to its dimensions, labels, and subjects.
- Deleting a template referenced by a project is protected.
- Task keys are unique inside a project and selected subjects belong to it.
- A project defines available subjects; each task selects a subset of them.
- `TaskSubject` makes every member of a task's subject subset explicit.
- Creating a parent annotation job creates one work item per `TaskSubject`.
- Each work item tracks one subject's lifecycle and owns at most one result.
- Video assets and subjects used by a view share the task's project.
- A task has at most one main view, one back view, and one view per subject.
- Duplicate task/annotator assignments and work items are prevented.
- Work-item status follows `assigned → in_progress → completed → reviewed`.

`configuration` and `attributes` are JSON for intentionally flexible metadata.
Relationships and identity remain relational so PostgreSQL can enforce them.
The result `data` field is intentionally flexible until later lessons introduce
typed annotation structures.
