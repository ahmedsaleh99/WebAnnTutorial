# Core data model

Lesson 5 introduces the configuration domain used by later APIs and workflows.

```mermaid
erDiagram
    PROJECT_TEMPLATE ||--o{ PROJECT : configures
    PROJECT ||--o{ ANNOTATION_DIMENSION : owns
    ANNOTATION_DIMENSION ||--o{ ANNOTATION_LABEL : contains
    PROJECT ||--o{ SUBJECT : includes

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
```

## Invariants

- Template `(key, version)` pairs are unique and versions start at one.
- Project keys are globally unique and status is constrained to a known value.
- Dimension keys are unique within a project.
- Label names are unique within a dimension; colors use `#RRGGBB` syntax.
- Subject identifiers are unique within a project.
- Deleting a project cascades to its dimensions, labels, and subjects.
- Deleting a template referenced by a project is protected.

`configuration` and `attributes` are JSON for intentionally flexible metadata.
Relationships and identity remain relational so PostgreSQL can enforce them.
