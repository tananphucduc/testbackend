# Task Management API

A RESTful Task Management API built with FastAPI, PostgreSQL, and JWT authentication.

## Technology Stack

- **Python 3.12** + **FastAPI**
- **SQLAlchemy** (ORM)
- **PostgreSQL** (database)
- **JWT** authentication (python-jose + passlib/bcrypt)
- **Docker** + **Docker Compose**
- **GitHub Actions** + **GitHub Container Registry (GHCR)**

## Project Structure

```
app/
├── main.py              # Entry point: Khởi tạo FastAPI, mount routers, init tables
├── core/                # Các thành phần cấu hình cốt lõi dùng chung
│   ├── config.py        # Quản lý cấu hình biến môi trường (.env) bằng Pydantic BaseSettings
│   ├── database.py      # Thiết lập SQLAlchemy engine, SessionLocal và cơ chế retry kết nối
│   └── security.py      # Thuật toán hash mật khẩu (bcrypt), tạo & decode JWT token
├── models/              # Định nghĩa thực thể Database (SQLAlchemy ORM Models)
│   ├── user.py          # Bảng users
│   └── task.py          # Bảng tasks
├── schemas/             # Data Transfer Objects (Pydantic Schemas - Request/Response Validation)
│   ├── auth.py          # UserRegister, UserLogin, Token
│   └── task.py          # TaskCreate, TaskUpdate, TaskResponse, TaskListResponse
├── routers/             # Controller/Endpoints xử lý các luồng HTTP request
│   ├── auth.py          # /api/v1/auth: register, login
│   └── tasks.py         # /api/v1/tasks: CRUD, pagination, filter
└── dependencies/        # Cơ chế Dependency Injection của FastAPI
    └── auth.py          # Middleware get_current_user xác thực JWT Bearer token

```

## Environment Configuration

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:

| Variable                      | Description                    |
| ----------------------------- | ------------------------------ |
| `DATABASE_URL`                | PostgreSQL connection string   |
| `SECRET_KEY`                  | JWT signing secret             |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration (default: 30) |

## Local Development

Build the Docker image locally, then start with Compose:

```bash
docker build -t ghcr.io/tananphucduc/task-management-api:latest .
docker compose up
```

The API will be available at `http://localhost:8000`.

Swagger documentation: `http://localhost:8000/docs`

## API Endpoints

### Authentication

| Method | Endpoint                | Description                 |
| ------ | ----------------------- | --------------------------- |
| POST   | `/api/v1/auth/register` | Register a new user         |
| POST   | `/api/v1/auth/login`    | Login and receive JWT token |

### Tasks (authentication required)

| Method | Endpoint                  | Description                                |
| ------ | ------------------------- | ------------------------------------------ |
| POST   | `/api/v1/tasks`           | Create a task                              |
| GET    | `/api/v1/tasks`           | List tasks (with pagination and filtering) |
| GET    | `/api/v1/tasks/{task_id}` | Get a single task                          |
| PUT    | `/api/v1/tasks/{task_id}` | Update a task                              |
| DELETE | `/api/v1/tasks/{task_id}` | Delete a task                              |

### Pagination and Filtering

```
GET /api/v1/tasks?page=1&page_size=10
GET /api/v1/tasks?status=pending
GET /api/v1/tasks?page=1&page_size=10&status=pending
```

## Authentication Flow

1. **Register** — `POST /api/v1/auth/register` with username, email, and password
2. **Login** — `POST /api/v1/auth/login` to receive a JWT access token
3. **Use token** — Include `Authorization: Bearer <token>` in protected requests

Each user can only access their own tasks. Attempting to access another user's task returns `404 Not Found`.

## Database

Two tables with a one-to-many relationship:

```
users (1) ──── (N) tasks
```

- `users`: id, username, email, password_hash, created_at
- `tasks`: id, user_id (FK → users.id), title, description, status, created_at
- Task status: `pending` or `completed`

## CI/CD Architecture

```
Developer
   │ git push
   ▼
GitHub
   │
   ▼
GitHub Actions
   │ docker build + push
   ▼
GitHub Container Registry (GHCR)
   │
   ▼
VPS (docker pull + run)
```

The Docker image is built by GitHub Actions — **not on the VPS**. This prevents resource-intensive builds from affecting the production server.

### VPS Deployment

```bash
docker pull ghcr.io/tananphucduc/task-management-api:latest
docker compose up -d
```
