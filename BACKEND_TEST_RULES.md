# BACKEND PRACTICAL TEST — IMPLEMENTATION RULES

> **Purpose:** This document is the single source of truth for implementing the Backend practical test.
>
> **Target:** Build a small, production-minded RESTful Task Management API with FastAPI, database persistence, authentication, validation/error handling, Docker/Compose, and a documented CI/CD design.
>
> **Important:** The implementation must remain small enough to complete and understand within the 3-hour practical test. Do not introduce unnecessary architecture, frameworks, services, or features.

---

# 1. TEST OVERVIEW

## 1.1 Duration

**Practical implementation:** 3 hours

| Part | Expected Time |
|---|---:|
| Part 1 — API, Database, Business Logic | 1.5 hours |
| Part 2 — Security and Error Handling | 45 minutes |
| Part 3 — DevOps and System Integration | 45 minutes |
| Part 4 — Defense Interview | 15–30 minutes |

---

# 2. CORE REQUIREMENTS

The system must provide:

1. RESTful API built with **FastAPI**
2. Database containing:
   - `users`
   - `tasks`
3. One-to-many relationship:
   - One user can have many tasks
   - Each task belongs to one user
4. Task CRUD APIs
5. Pagination
6. Filtering tasks by status
7. Database-side filtering and pagination
8. Authentication using JWT or a simple API Key
9. Authenticated access for protected task operations
10. Environment-based configuration for secrets and database settings
11. Standard HTTP error handling
12. Dockerfile
13. `docker-compose.yml`
14. CI/CD design using external image building
15. Container Registry
16. VPS deployment by pulling the pre-built image
17. 100% English:
   - variable names
   - function names
   - error messages
   - code comments
   - UI/API-facing text if applicable
18. Code must be understandable and defensible by the candidate.

---

# 3. NON-GOALS

Do NOT add features that are not required by the test.

Do not introduce:

- Frontend/UI
- Microservices
- Kubernetes
- Redis
- Message queues
- Celery
- Event-driven architecture
- Complex repository patterns
- CQRS
- Domain-driven design
- Event sourcing
- GraphQL
- WebSockets
- Unnecessary third-party services
- Complex caching
- Unnecessary abstraction layers
- Unnecessary design patterns

The goal is a clean, understandable Backend solution, not a large production platform.

---

# 4. RECOMMENDED TECHNOLOGY

Use:

- Python 3.12+
- FastAPI
- Pydantic
- SQLAlchemy
- PostgreSQL OR SQLite
- JWT authentication
- Docker
- Docker Compose
- GitHub Actions
- GitHub Container Registry (GHCR)

## Database choice

The test explicitly allows:

- SQLite
- PostgreSQL

Prefer PostgreSQL if it can be implemented confidently within the time limit.

SQLite is acceptable if it significantly reduces implementation risk and time.

If PostgreSQL is used, Docker Compose should run:

```text
api
postgres
```

---

# 5. PROJECT STRUCTURE

Use a simple modular structure.

Recommended:

```text
backend-test/
│
├── app/
│   ├── main.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   └── security.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   └── task.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   └── task.py
│   │
│   ├── routers/
│   │   ├── auth.py
│   │   └── tasks.py
│   │
│   └── dependencies/
│       └── auth.py
│
├── .env
├── .env.example
├── .gitignore
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── README.md
└── .github/
    └── workflows/
        └── ci.yml
```

This structure is a recommendation, not a requirement to create every file if the implementation can remain clean with fewer files.

## Responsibility rules

### `main.py`

Only application initialization and router registration.

Do not put all business logic into `main.py`.

### `core/config.py`

Application configuration and environment variables.

### `core/database.py`

Database engine/session configuration.

### `core/security.py`

Password hashing, JWT creation, and JWT verification utilities.

### `models/`

SQLAlchemy database models.

### `schemas/`

Pydantic request/response schemas.

### `routers/`

HTTP endpoints.

### `dependencies/auth.py`

Authentication dependencies such as retrieving the current authenticated user.

---

# 6. DATABASE DESIGN

The database must contain two main tables.

## 6.1 Users

Required minimum fields:

```text
users
-----
id
username
email
password_hash
created_at
```

Recommended:

- `id`: primary key
- `username`: unique
- `email`: unique
- `password_hash`: required
- `created_at`: timestamp

Never store a plain-text password.

---

# 7. TASKS TABLE

Required fields:

```text
tasks
-----
id
user_id
title
description
status
created_at
```

Requirements:

- `id`: primary key
- `user_id`: foreign key to `users.id`
- `title`: required
- `description`: optional or required according to implementation
- `status`: only `pending` or `completed`
- `created_at`: timestamp

Recommended status representation:

```python
class TaskStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
```

---

# 8. DATABASE RELATIONSHIP

Required relationship:

```text
User 1 ───────── N Tasks
```

Example:

```text
User #1
 ├── Task #1
 ├── Task #2
 └── Task #3

User #2
 ├── Task #4
 └── Task #5
```

Every task must belong to a user through:

```text
tasks.user_id → users.id
```

The implementation must prevent a user from modifying another user's task.

---

# 9. REST API

Use a consistent API prefix:

```text
/api/v1
```

---

# 10. AUTHENTICATION ENDPOINTS

Minimum:

```http
POST /api/v1/auth/register
POST /api/v1/auth/login
```

## Register

Example request:

```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "password123"
}
```

Password must be hashed before persistence.

## Login

Example request:

```json
{
  "username": "john",
  "password": "password123"
}
```

Successful response should contain an access token.

Example:

```json
{
  "access_token": "JWT_TOKEN",
  "token_type": "bearer"
}
```

---

# 11. TASK CRUD ENDPOINTS

Required:

```http
POST   /api/v1/tasks
GET    /api/v1/tasks
GET    /api/v1/tasks/{task_id}
PUT    /api/v1/tasks/{task_id}
DELETE /api/v1/tasks/{task_id}
```

---

# 12. CREATE TASK

Endpoint:

```http
POST /api/v1/tasks
```

Authentication required.

Example:

```json
{
  "title": "Complete backend test",
  "description": "Implement Task Management API",
  "status": "pending"
}
```

The authenticated user's ID must be assigned as `user_id`.

The client must not be allowed to arbitrarily assign another user's ID.

Expected success status:

```text
201 Created
```

---

# 13. GET TASK LIST

Endpoint:

```http
GET /api/v1/tasks
```

Authentication required.

Must support pagination.

Example:

```http
GET /api/v1/tasks?page=1&page_size=10
```

Must support filtering by status:

```http
GET /api/v1/tasks?status=pending
```

Combined:

```http
GET /api/v1/tasks?page=1&page_size=10&status=pending
```

---

# 14. PAGINATION RULES

Recommended parameters:

```text
page
page_size
```

Example:

```text
page=2
page_size=10
```

Calculate:

```text
offset = (page - 1) * page_size
```

Then query the database with:

```text
OFFSET
LIMIT
```

---

# 15. FILTERING RULES

Supported status values:

```text
pending
completed
```

Filtering must be executed by the database.

DO NOT:

```python
tasks = get_all_tasks()

filtered_tasks = [
    task for task in tasks
    if task.status == requested_status
]
```

This loads unnecessary records into application memory.

Instead, construct a database query:

```text
SELECT ...
FROM tasks
WHERE status = ?
LIMIT ?
OFFSET ?
```

The exact ORM syntax may vary.

The important requirement is:

```text
Database
    ↓
Filter
    ↓
Pagination
    ↓
Only required records
    ↓
FastAPI
```

---

# 16. GET SINGLE TASK

Endpoint:

```http
GET /api/v1/tasks/{task_id}
```

Authentication required.

The API must verify that the requested task belongs to the authenticated user.

If it does not exist:

```text
404 Not Found
```

Example:

```json
{
  "detail": "Task not found"
}
```

---

# 17. UPDATE TASK

Endpoint:

```http
PUT /api/v1/tasks/{task_id}
```

Authentication required.

The user may update their own task.

The API must verify ownership.

If the task does not exist:

```text
404 Not Found
```

---

# 18. DELETE TASK

Endpoint:

```http
DELETE /api/v1/tasks/{task_id}
```

Authentication required.

The user may delete their own task.

Recommended success response:

```text
204 No Content
```

---

# 19. AUTHORIZATION RULE

Authentication is not enough.

The API must also enforce task ownership.

Example:

```text
User A
  └── Task 1

User B
  └── Task 2
```

If User A requests:

```http
GET /api/v1/tasks/2
```

the API must not expose User B's task.

A consistent design may return:

```text
404 Not Found
```

to avoid revealing whether another user's resource exists.

---

# 20. JWT AUTHENTICATION FLOW

Recommended flow:

```text
Client
  ↓
POST /auth/login
  ↓
Verify username/password
  ↓
Generate JWT
  ↓
Return access token
```

Then:

```text
Client
  ↓
Authorization: Bearer <token>
  ↓
FastAPI authentication dependency
  ↓
Decode JWT
  ↓
Get user identity
  ↓
Query user
  ↓
Allow protected endpoint
```

The implementation must be understandable enough to explain during the defense interview.

---

# 21. PASSWORD SECURITY

Never store plain-text passwords.

Wrong:

```text
password = "123456"
```

Correct:

```text
password_hash = hash(password)
```

During login:

```text
provided password
       ↓
verify against password hash
       ↓
valid
       ↓
generate JWT
```

Use a standard password hashing library.

---

# 22. ENVIRONMENT CONFIGURATION

Sensitive values must not be hard-coded.

Example `.env`:

```env
DATABASE_URL=postgresql://user:password@postgres:5432/taskdb
SECRET_KEY=replace-with-a-secure-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

If SQLite is used:

```env
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=replace-with-a-secure-secret
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

The application must read these values from environment variables.

---

# 23. `.env` SECURITY

`.env` must not be committed.

`.gitignore` must contain:

```text
.env
```

Provide:

```text
.env.example
```

with placeholder values.

Example:

```env
DATABASE_URL=
SECRET_KEY=
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

Never put real credentials or production secrets into `.env.example`.

---

# 24. ERROR HANDLING

Use appropriate HTTP status codes.

Required examples:

| Situation | Status |
|---|---:|
| Successful GET | `200 OK` |
| Successful CREATE | `201 Created` |
| Successful DELETE | `204 No Content` |
| Missing/invalid authentication | `401 Unauthorized` |
| Resource not found | `404 Not Found` |
| Invalid request data | `400 Bad Request` or FastAPI's appropriate validation status |
| Duplicate username/email | Appropriate `400` or `409` |

Error messages must be clear and written in English.

Examples:

```json
{
  "detail": "Task not found"
}
```

```json
{
  "detail": "Invalid credentials"
}
```

```json
{
  "detail": "Authentication required"
}
```

Do not expose internal stack traces or sensitive database information to clients.

---

# 25. INPUT VALIDATION

Use Pydantic schemas.

Validate at minimum:

- required title
- valid task status
- valid authentication input
- reasonable pagination values

Examples:

```text
page >= 1
page_size >= 1
```

Prevent invalid status values outside:

```text
pending
completed
```

---

# 26. ENGLISH-ONLY RULE — CRITICAL

This is a **mandatory pass/fail requirement**.

The following must be **100% English**:

- variable names
- function names
- class names
- database field names
- API error messages
- validation messages where customized
- code comments
- README technical descriptions
- log messages
- user-facing API text

Correct:

```python
current_user
task_id
created_at
password_hash
get_current_user()
create_task()
```

Correct:

```python
# Retrieve the authenticated user
```

Correct:

```text
Task not found
Invalid credentials
Authentication required
```

Do not use Vietnamese in source code, comments, error messages, or technical documentation.

---

# 27. NAMING CONVENTIONS

## Python

Use `snake_case`:

```text
user_id
task_id
created_at
password_hash
current_user
page_size
```

Functions:

```text
create_task()
get_task()
update_task()
delete_task()
get_current_user()
```

Classes:

```text
User
Task
TaskStatus
```

## Database

Use plural snake_case table names:

```text
users
tasks
```

Columns:

```text
user_id
created_at
password_hash
```

Avoid:

```text
tbl_users
UserTable
TaskManagementData
```

unless there is a specific project convention.

---

# 28. DOCKERFILE

A Dockerfile is mandatory.

Requirements:

- Use a lightweight Python base image
- Install dependencies
- Copy application source
- Expose FastAPI port
- Run FastAPI with Uvicorn
- Do not require source-code build operations on the VPS

Example runtime command:

```text
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

# 29. DOCKER COMPOSE

A `docker-compose.yml` is mandatory.

If PostgreSQL is selected, use:

```text
services:
  api:
  postgres:
```

Expected architecture:

```text
Docker Compose
├── api
│   └── FastAPI
│
└── postgres
    └── PostgreSQL
```

The API container must connect to the database through the Compose service name, not `localhost`.

Example concept:

```text
postgres:5432
```

inside the Docker network.

---

# 30. CI/CD DESIGN

The CI/CD design must solve this problem:

> The production VPS has weak hardware. How can new code be deployed without building Docker images directly on the VPS and potentially freezing the server?

Required solution:

```text
Developer
    ↓
git push
    ↓
GitHub
    ↓
GitHub Actions
    ↓
Docker build
    ↓
Container Registry
    ↓
VPS
    ↓
docker pull
    ↓
Run new image
```

The VPS must NOT perform:

```text
docker build
```

for normal deployments.

---

# 31. EXPECTED CI/CD RESPONSIBILITIES

## GitHub Actions

Responsible for:

1. Checkout source
2. Login to Container Registry
3. Build Docker image
4. Tag image
5. Push image to Container Registry

## VPS

Responsible for:

1. Pull pre-built image
2. Stop/remove old container if necessary
3. Start new container
4. Verify service health

This separates resource-intensive image building from the weak production server.

---

# 32. CONTAINER IMAGE NAMING

Recommended:

```text
ghcr.io/<github-owner>/task-management-api:latest
```

For production-quality workflows, commit SHA tags are preferred:

```text
ghcr.io/<github-owner>/task-management-api:<commit-sha>
```

However, `latest` is acceptable for the practical test if it keeps the implementation simple.

---

# 33. GITHUB ACTIONS PSEUDOCODE

A minimal CI workflow should conceptually do:

```yaml
on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest

    steps:
      - checkout source

      - login to container registry

      - docker build image

      - docker push image
```

If implementing automatic VPS deployment, the deployment stage may:

```text
SSH to VPS
    ↓
docker pull image
    ↓
docker compose up -d
```

Do not expose SSH passwords or registry tokens in source code.

Use GitHub Secrets for sensitive deployment credentials.

---

# 34. DEVOPS DESIGN EXPLANATION

The candidate must be able to explain:

### Why build outside the VPS?

Because Docker image builds consume:

- CPU
- RAM
- disk I/O
- network bandwidth

A weak VPS may become slow or unavailable during the build.

### Why use a Container Registry?

The Registry stores the already-built Docker image.

The VPS does not need the source code or build environment.

### What does the VPS do?

Only:

```text
pull image
run image
```

This reduces resource usage and deployment risk.

---

# 35. TESTING REQUIREMENTS

Before considering the implementation complete, verify:

## Authentication

- Register succeeds
- Login succeeds
- Invalid credentials return an appropriate error
- Missing token cannot access protected endpoints

## Task CRUD

- Create task works
- Get task works
- List tasks works
- Update task works
- Delete task works
- Non-existing task returns 404
- User cannot access another user's task

## Pagination

Test:

```text
?page=1&page_size=10
```

and:

```text
?page=2&page_size=10
```

## Filtering

Test:

```text
?status=pending
```

and:

```text
?status=completed
```

Test combined:

```text
?page=1&page_size=10&status=pending
```

## HTTP status codes

Verify at least:

```text
200
201
204
401
404
400/422
```

---

# 36. POSTMAN COLLECTION

Create a Postman Collection covering:

```text
Authentication
├── Register
└── Login

Tasks
├── Create Task
├── Get Tasks
├── Get Task
├── Update Task
└── Delete Task
```

Recommended environment variables:

```text
base_url
access_token
task_id
```

Example:

```text
base_url = http://localhost:8000/api/v1
```

After login, use:

```text
Authorization: Bearer {{access_token}}
```

The collection should demonstrate that the API works with real data.

---

# 37. README REQUIREMENTS

README should briefly explain:

1. Project purpose
2. Technology stack
3. Project structure
4. Environment configuration
5. Local setup
6. Database setup
7. API endpoints
8. Authentication
9. Docker usage
10. Docker Compose usage
11. CI/CD architecture

Do not write a huge documentation system.

Keep it concise and technically accurate.

---

# 38. DEFENSE INTERVIEW REQUIREMENTS

After implementation, the candidate must explain the solution.

Expected topics:

## 38.1 Project structure

Explain:

- Why routers are separated
- Why models are separated
- Why schemas are separated
- Why authentication utilities are separated

## 38.2 Database

Explain:

- `users` and `tasks`
- primary keys
- foreign key
- one-to-many relationship
- why `user_id` exists in `tasks`

## 38.3 Authentication

Explain:

```text
Register
→ password hashing

Login
→ password verification
→ JWT generation

Protected API
→ Bearer token
→ JWT verification
→ current user
```

## 38.4 Pagination

Explain:

```text
page
page_size
offset
limit
```

and why filtering/pagination should happen inside the database query.

## 38.5 Error handling

Explain why:

```text
401 = authentication problem
404 = resource not found
400/422 = invalid request
```

## 38.6 CI/CD

Explain:

```text
Git push
→ GitHub Actions
→ Docker build
→ Registry
→ VPS pull
→ Run
```

and why the VPS does not build the image.

---

# 39. CODE OWNERSHIP / AI USAGE RULE

The implementation must be understandable by the candidate.

Do not generate or include code that the candidate cannot explain.

The evaluator may select random lines and ask:

- What does this line do?
- Why is this dependency required?
- Why is this query written this way?
- Why is this status code returned?
- Where does `current_user` come from?
- How is the JWT validated?
- Why is `user_id` assigned from the authenticated user?
- Why is pagination performed in the database?
- Why is the Docker image built outside the VPS?

The candidate must be able to answer these questions from the actual implementation.

Therefore:

- Prefer simple code.
- Avoid unnecessary abstractions.
- Avoid unexplained magic.
- Avoid copy-pasted template code.
- Keep naming explicit.
- Keep functions reasonably small.
- Keep business logic easy to trace.

---

# 40. TIME MANAGEMENT

Total practical time:

```text
180 minutes
```

Recommended allocation:

| Time | Task |
|---|---|
| 0–10 min | Project setup and structure |
| 10–35 min | Database and models |
| 35–65 min | Authentication/JWT |
| 65–100 min | Task CRUD |
| 100–115 min | Pagination/filtering |
| 115–130 min | Error handling and validation |
| 130–150 min | Dockerfile and Compose |
| 150–170 min | GitHub Actions / Registry design |
| 170–180 min | Testing, README, English-only review |

Do not spend excessive time on optional improvements before core requirements work.

---

# 41. PRIORITY ORDER

If time becomes limited, prioritize:

```text
1. Database relationship
2. Task CRUD
3. Authentication
4. Pagination/filter
5. Error handling
6. Dockerfile
7. docker-compose.yml
8. CI/CD design
9. Testing
10. README polish
```

Never sacrifice required core functionality for unnecessary architecture.

---

# 42. ACCEPTANCE CHECKLIST

Before submission, verify every item.

## Database

- [ ] `users` table exists
- [ ] `tasks` table exists
- [ ] `tasks.user_id` references `users.id`
- [ ] One-to-many relationship works
- [ ] Task contains title
- [ ] Task contains description
- [ ] Task contains status
- [ ] Task contains created_at
- [ ] Status supports `pending`
- [ ] Status supports `completed`

## API

- [ ] Register works
- [ ] Login works
- [ ] Create task works
- [ ] List tasks works
- [ ] Get task works
- [ ] Update task works
- [ ] Delete task works
- [ ] Pagination works
- [ ] Status filtering works
- [ ] Database performs filtering/pagination
- [ ] User ownership is enforced

## Security

- [ ] Passwords are hashed
- [ ] JWT or API Key authentication works
- [ ] Protected endpoints require authentication
- [ ] Secrets are environment variables
- [ ] `.env` is ignored by Git
- [ ] `.env.example` exists
- [ ] No real secrets are committed

## Error Handling

- [ ] 401 is returned for missing/invalid authentication
- [ ] 404 is returned for missing task
- [ ] 400/422 is returned for invalid input
- [ ] Error messages are clear
- [ ] Error messages are English
- [ ] Internal errors are not leaked

## Code Quality

- [ ] Variables are English
- [ ] Functions are English
- [ ] Comments are English
- [ ] Error messages are English
- [ ] Database names are consistent
- [ ] Structure is easy to explain
- [ ] No unnecessary architecture

## Docker

- [ ] Dockerfile exists
- [ ] Application builds successfully
- [ ] Container starts successfully
- [ ] docker-compose.yml exists
- [ ] Database runs with Compose when PostgreSQL is selected
- [ ] API connects to database correctly

## CI/CD

- [ ] GitHub Actions workflow is documented or implemented
- [ ] Docker image is built outside VPS
- [ ] Image is pushed to Container Registry
- [ ] VPS pulls pre-built image
- [ ] VPS does not build the production image

## Documentation

- [ ] README exists
- [ ] Setup instructions are correct
- [ ] API usage is documented
- [ ] CI/CD flow is documented
- [ ] Postman Collection exists if required
- [ ] Documentation is English

---

# 43. SCORING CRITERIA

## 1. Technical Knowledge — 20 points

Evaluate:

- Database schema design
- One-to-many relationship
- RESTful API design
- FastAPI knowledge
- Query optimization
- Pagination
- Filtering

---

## 2. Practical Implementation — 25 points

Evaluate:

- Required Task fields
- CRUD APIs
- Correct business logic
- Working list API
- Pagination
- Filtering

### Mandatory fail condition

The following must be 100% English:

- variable names
- function names
- error messages
- code comments

---

## 3. Product and Code Quality — 15 points

Evaluate:

- Project structure
- Database naming
- Code readability
- Maintainability
- Candidate's understanding and ownership of the code

---

## 4. Problem Solving — 15 points

Evaluate:

- Authentication explanation
- CI/CD explanation
- Weak-server deployment solution
- Reasoning behind external image building
- Technical decision making

---

## 5. Independence — 10 points

Evaluate the ability to complete:

```text
API / Logic
Security
DevOps
```

within the 3-hour limit.

---

## 6. Collaboration / Reporting / Handover — 5 points

Evaluate:

- CI/CD documentation
- Clear technical explanation
- Ability to explain implementation decisions

---

## 7. Security / Testing / Risk Awareness — 5 points

Evaluate:

- Authentication
- Secret management
- Error handling
- HTTP status codes
- Basic validation
- Security awareness

---

## 8. Responsibility / Discipline — 5 points

Evaluate:

- Completion of the required defense interview
- Dockerfile
- docker-compose.yml
- Following the requested delivery format

---

# 44. FINAL IMPLEMENTATION RULES FOR THE CODING AGENT

The coding agent MUST follow these rules:

1. Read this document before modifying the project.
2. Treat this file as the source of truth for the practical test.
3. Do not add features outside the requirements unless explicitly requested.
4. Do not introduce unnecessary architecture.
5. Keep the implementation small and understandable.
6. Use English for all code identifiers.
7. Use English for all comments.
8. Use English for all API error messages.
9. Never hard-code secrets.
10. Never commit `.env`.
11. Use database-side filtering and pagination.
12. Enforce authenticated user ownership of tasks.
13. Do not expose another user's tasks.
14. Use correct HTTP status codes.
15. Keep authentication logic explicit and explainable.
16. Ensure Docker can build the application.
17. Ensure Docker Compose can start the required services.
18. Design CI/CD so Docker images are built outside the weak VPS.
19. Push built images to a Container Registry.
20. Make the VPS pull and run pre-built images.
21. Do not use `docker build` on the production VPS as part of normal deployment.
22. Do not generate unnecessary frontend code.
23. Do not introduce Kubernetes, Redis, Celery, microservices, or other unrelated infrastructure.
24. Prefer simple, explicit implementations over clever abstractions.
25. Before finishing, run a complete acceptance checklist.
26. Before finishing, verify that the code can be explained line-by-line during the defense interview.
27. Do not claim a feature is complete unless it has been tested.
28. Do not silently change requirements.
29. If a requirement is ambiguous, choose the simplest implementation that satisfies the explicit test criteria.
30. Preserve a clear Git history with meaningful commits when Git is available.

---

# 45. EXPECTED FINAL ARCHITECTURE

The final system should conceptually look like:

```text
                    CLIENT
                       │
                       ▼
              ┌─────────────────┐
              │    FastAPI      │
              │   REST API      │
              └────────┬────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
      Authentication          Task CRUD
            │                     │
            │              Pagination
            │              Status Filter
            │                     │
            └──────────┬──────────┘
                       ▼
                 SQL Database
                 ┌─────────┐
                 │  users  │
                 └────┬────┘
                      │ 1:N
                 ┌────▼────┐
                 │  tasks  │
                 └─────────┘


CI/CD:

Developer
   │
   │ git push
   ▼
GitHub
   │
   ▼
GitHub Actions
   │
   │ docker build
   ▼
Container Registry
   │
   │ docker pull
   ▼
Weak VPS
   │
   ▼
Docker Container
   │
   ▼
FastAPI
```

---

# 46. DEFINITION OF DONE

The implementation is considered complete only when:

```text
[✓] FastAPI application starts
[✓] Database works
[✓] Users can register/login
[✓] Authentication works
[✓] Tasks can be created
[✓] Tasks can be listed
[✓] Tasks can be retrieved
[✓] Tasks can be updated
[✓] Tasks can be deleted
[✓] Task ownership is enforced
[✓] Pagination works
[✓] Status filtering works
[✓] Filtering/pagination are performed by the database
[✓] Correct HTTP errors are returned
[✓] Secrets are environment-based
[✓] Dockerfile works
[✓] Docker Compose works
[✓] CI/CD architecture is documented
[✓] Container image can be built outside the VPS
[✓] Image can be pushed to a Container Registry
[✓] VPS can pull the image
[✓] All code identifiers are English
[✓] All comments are English
[✓] All error messages are English
[✓] The candidate can explain the implementation
```

**End of specification.**
