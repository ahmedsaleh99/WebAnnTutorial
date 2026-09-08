# Build the CVIP Annotation Platform

This repository is a project-based tutorial for rebuilding the
[EngAnnWeb](https://github.com/ahmedsaleh99/EngAnnWeb) multi-camera video
annotation platform from an empty repository.

This is the **course and reference repository**. Each student creates a
separate, empty GitHub repository for their own application and follows the
lessons there. At the end of the course, the student's `main` branch should
contain the same application capabilities and essential repository structure
as the reference implementation, while preserving the student's own pull
request and commit history.

The course teaches the technologies as they become useful, then combines them
into production features. Every lesson is completed on its own branch and
submitted as a pull request. Tests are written before or with production code,
and a pull request is merged only when its acceptance criteria and CI checks
pass.

## Start here

- [Tutorial plan](docs/TUTORIAL_PLAN.md)
- [Student repository workflow](docs/STUDENT_WORKFLOW.md)
- [Lesson 1: repository workflow and CI/CD foundation](docs/lessons/01-CI-CD-FOUNDATION.md)
- [Lesson 2: local developer tooling and quality gates](docs/lessons/02-DEVELOPER-TOOLING.md)
- [Lesson 3: Docker and Compose foundations](docs/lessons/03-DOCKER-COMPOSE.md)
- [Lesson 4: Django foundations and the first test](docs/lessons/04-DJANGO-FOUNDATIONS.md)
- [Developer tooling reference](docs/TOOLING.md)
- [Docker development reference](docs/DOCKER.md)
- [GitHub branch and environment protection](docs/BRANCH_PROTECTION.md)

Each lesson includes a student walkthrough and a gold-standard reference
implementation. Attempt the lesson first, then compare approaches and record
what you learned in the pull request before final review.

Students should not fork this repository as their implementation repository or
copy the completed EngAnnWeb source. The learning objective is to build each
increment in their own repository from the tests and requirements in the
lesson.
