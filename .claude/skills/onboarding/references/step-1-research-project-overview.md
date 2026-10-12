# Step 1 — Project Overview

**Goal:** Learn the basic facts about the project. First, read [PROJECT_OVERVIEW.md](../../../references/PROJECT_OVERVIEW.md) to see what is already there. At the end, write what you found to the same file.

## 1.1 — Project Name and Description

Look for config files: `package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `.csproj`, `pubspec.yaml`, `composer.json`. Get the `name` and `description` fields.

If you cannot find them, or they are empty or unclear, ask the user:

> "What is the project name and description?"

## 1.2 — Programming Languages and Frameworks

Look for these signs in the repo:

| Sign                       | Language / Framework |
| -------------------------- | -------------------- |
| `.ts`, `.tsx` files        | TypeScript           |
| `.js`, `.jsx` files        | JavaScript           |
| `next.config.*`            | Next.js              |
| `vite.config.*`            | Vite                 |
| `angular.json`             | Angular              |
| `nuxt.config.*`            | Nuxt                 |
| `.py` files                | Python               |
| `settings.py`, `manage.py` | Django               |
| `fastapi` in deps          | FastAPI              |
| `.go` files                | Go                   |
| `.rs` files                | Rust                 |
| `.java` + `pom.xml`        | Java / Maven         |
| `spring` in `pom.xml`      | Spring Boot          |
| `.cs` + `.csproj`          | C# / .NET            |
| `.dart` + `pubspec.yaml`   | Dart / Flutter       |
| `.rb` + `Gemfile`          | Ruby                 |
| `.php` + `composer.json`   | PHP / Laravel        |

In a monorepo or microservices project, list the languages and frameworks for each package or service.

## 1.3 — Package Manager

Look at the lock file:

| Lock File           | Package Manager |
| ------------------- | --------------- |
| `yarn.lock`         | Yarn            |
| `package-lock.json` | npm             |
| `pnpm-lock.yaml`    | pnpm            |
| `bun.lockb`         | Bun             |
| `Pipfile.lock`      | Pipenv          |
| `poetry.lock`       | Poetry          |
| `uv.lock`           | uv              |
| `Cargo.lock`        | Cargo           |
| `go.sum`            | Go modules      |
| `Gemfile.lock`      | Bundler         |
| `composer.lock`     | Composer        |

If there is more than one lock file for the same language, ask the user:

> "I found more than one lock file ([list them]). Which package manager should I use?"

## 1.4 — Key Libraries

Look at `package.json`, `requirements.txt`, `pyproject.toml`, or other package files. List the main libraries that many parts of the code use. For example: `prisma`, `axios`, `formik`, `react-query`, `zod`, `express`, `sqlalchemy`, `celery`. Skip dev-only tools and tools used in only one place.

## 1.5 — Database

Skip this if the repo is frontend-only and has no database.

Look for:

- ORM or schema files: `prisma/schema.prisma`, `ormconfig.*`, `alembic.ini`, `database.yml`
- Env variable names (names only, not values): `DATABASE_URL`, `DB_HOST`, `MONGO_URI`, `REDIS_URL`
- Dependencies: `pg`, `mysql2`, `mongodb`, `sqlite3`, `redis`, `typeorm`, `sequelize`, `sqlalchemy`

If you find nothing, ask:

> "Does this project use a database? If so, which one?"

## 1.6 — Doc Directory

Ask the user:

> "Where should the agent save plan files? (e.g. `docs/`, `.github/docs/`, `.claude/docs/`, `plans/`)"

## 1.7 — Testing Workflow

Ask the user:

> "How do you write tests?"
>
> - **Code-First** — Write the code first, then the tests
> - **Test-First** — Write the tests first, then the code (TDD/BDD)
> - **Skip-Testing** — This project has no automated tests

## 1.8 — Playwright Check

Ask the user:

> "When the UI changes, should the review and tester agents run Playwright (browser) checks?"
>
> - **Always** — Always run them when the UI changes
> - **None** — Never run them
> - **Ask-User** — Ask each time (default)

If the user does not answer, use `Ask-User`.

## 1.9 — Write PROJECT_OVERVIEW.md

Write everything you found to [PROJECT_OVERVIEW.md](../../../references/PROJECT_OVERVIEW.md).
