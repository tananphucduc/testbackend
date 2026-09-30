# CẨM NANG BẢO VỆ BÀI THI BACKEND (DEFENSE INTERVIEW GUIDE)

Tài liệu này được biên soạn bám sát theo **Bộ tiêu chí chấm điểm và Phần 4: Phỏng vấn bảo vệ bài làm (15 - 30 phút)** của Quản lý chuyên môn. Hãy đọc kỹ từng phần để tự tin trả lời lưu loát.

---

## MỤC LỤC
1. [Tổng quan kiến trúc & Cấu trúc thư mục (Folder Structure)](#1-tong-quan-kien-truc--cau-truc-thu-muc)
2. [Thiết kế Cơ sở dữ liệu & Tên bảng (Database Design)](#2-thiet-ke-co-so-du-lieu--ten-bang)
3. [Luồng hoạt động Xác thực & Bảo mật (Authentication & Security)](#3-luong-hoat-dong-xac-thuc--bao-mat)
4. [Tối ưu truy vấn: Phân trang & Lọc DB-side (Query Optimization)](#4-toi-uu-truy-van-phan-trang--loc-db-side)
5. [Thiết kế CI/CD cho bài toán VPS yếu (DevOps Solution)](#5-thiet-ke-cicd-cho-bai-toan-vps-yeu)
6. [Các điểm code chuyên sâu chứng minh tính trung thực (Deep-dive Code)](#6-cac-diem-code-chuyen-sau-chung-minh-tinh-trung-thuc)
7. [Tiêu chí chặn rớt: Chuẩn hóa 100% tiếng Anh](#7-tieu-chi-chan-rot-chuan-hoa-100-tieng-anh)
8. [Bộ câu hỏi - đáp nhanh khi phỏng vấn (Flashcards Q&A)](#8-bo-cau-hoi---dap-nhanh-khi-phong-van)

---

## 1. TỔNG QUAN KIẾN TRÚC & CẤU TRÚC THƯ MỤC

### Sơ đồ thư mục dự án
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

### Tại sao chọn cấu trúc này?
- **Nguyên lý Single Responsibility (Trách nhiệm đơn lẻ)**: Không dồn toàn bộ mã nguồn vào `main.py`. Mỗi module đảm nhiệm duy nhất một vai trò:
  - `models/`: Chỉ phản ánh cấu trúc bảng vật lý trong database.
  - `schemas/`: Đóng vai trò Data Transfer Object (DTO), thực hiện việc validate dữ liệu đầu vào (Input Validation) và lọc bỏ các dữ liệu nhạy cảm (như mật khẩu) trước khi trả dữ liệu về client (Output Serialization).
  - `routers/`: Tách biệt rành mạch giữa nghiệp vụ tài khoản (auth) và quản lý công việc (tasks).
  - `dependencies/`: Tái sử dụng middleware xác thực tài khoản dạng Dependency Injection ở bất kỳ endpoint nào cần bảo vệ.

---

## 2. THIẾT KẾ CƠ SỞ DỮ LIỆU & TÊN BẢNG

### Cách đặt tên bảng
- Tuân thủ quy ước chuẩn quốc tế của SQL và ORM conventions: Tên bảng sử dụng danh từ số nhiều viết thường: **`users`** và **`tasks`**.

### Mối quan hệ 1-N (One-to-Many)
- Một User có thể có nhiều Tasks, nhưng mỗi Task chỉ thuộc về một User duy nhất:
  - Bảng `users`: Khóa chính `id = Column(Integer, primary_key=True)`.
  - Bảng `tasks`: Khóa ngoại `user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)`.
  - Được đánh chỉ mục `index=True` trên cột `user_id` để tăng tốc độ truy vấn khi người dùng lấy danh sách task của chính họ.
  - Sử dụng quan hệ hai chiều trong SQLAlchemy ORM:
    - Trong `User`: `tasks = relationship("Task", back_populates="owner")`
    - Trong `Task`: `owner = relationship("User", back_populates="tasks")`

### Các trường dữ liệu của Task
- `id`: Khóa chính (Integer).
- `user_id`: Khóa ngoại trỏ đến `users.id` (Integer).
- `title`: Tiêu đề công việc (String, bắt buộc, tối thiểu 1 ký tự).
- `description`: Mô tả chi tiết (String, cho phép null).
- `status`: Trạng thái chỉ gồm 2 giá trị `pending` hoặc `completed` (Kiểm soát chặt chẽ qua Python Enum & PostgreSQL Enum).
- `created_at`: Thời gian tạo, lưu theo chuẩn UTC (`datetime.now(timezone.utc)`).

---

## 3. LUỒNG HOẠT ĐỘNG XÁC THỰC & BẢO MẬT

```
+-------------------------------------------------------------------------+
|                           ĐĂNG KÝ (REGISTER)                            |
| Client -> POST /auth/register {username, email, password}               |
|   1. Kiểm tra tồn tại username/email trong DB -> Nếu có: 409 Conflict   |
|   2. Hash password bằng bcrypt (salt ngẫu nhiên tự động)               |
|   3. Lưu User vào DB (Chỉ lưu password_hash, KHÔNG lưu plain text)      |
+-------------------------------------------------------------------------+
                                     │
+-------------------------------------------------------------------------+
|                           ĐĂNG NHẬP (LOGIN)                             |
| Client -> POST /auth/login {username, password}                         |
|   1. Tìm user theo username trong DB -> Không thấy: 401 Unauthorized    |
|   2. verify_password(plain_password, user.password_hash)                |
|      -> Không khớp: 401 Unauthorized                                    |
|   3. Tạo JWT Token với claims:                                          |
|      - "sub": str(user.id) (Subject nhận diện user)                     |
|      - "exp": utcnow() + 30 phút (Thời hạn token)                       |
|      - Ký bằng thuật toán HS256 với SECRET_KEY từ .env                  |
|   4. Trả về: { "access_token": "...", "token_type": "bearer" }          |
+-------------------------------------------------------------------------+
                                     │
+-------------------------------------------------------------------------+
|                  TRUY CẬP API BẢO VỆ (PROTECTED API)                    |
| Client -> GET /tasks/ với Header: Authorization: Bearer <TOKEN>         |
|   1. FastAPI HTTPBearer trích xuất token -> Không có: 401               |
|   2. decode_access_token():                                             |
|      - Giải mã chữ ký bằng SECRET_KEY                                   |
|      - Kiểm tra tính toàn vẹn và hạn sử dụng ("exp") -> Lỗi: 401        |
|   3. Bắt lỗi payload: ép kiểu int(payload["sub"])                       |
|      - Bắt KeyError, ValueError, TypeError -> Trả 401 (Tránh lỗi 500)   |
|   4. Tìm user trong DB theo user_id -> Không thấy: 401                  |
|   5. Inject current_user vào endpoint để thực thi nghiệp vụ             |
+-------------------------------------------------------------------------+
```

---

## 4. TỐI ƯU TRUY VẤN: PHÂN TRANG & LỌC DB-SIDE

### Đoạn code tại `app/routers/tasks.py`:
```python
query = db.query(Task).filter(Task.user_id == current_user.id)

if status:
    query = query.filter(Task.status == status)

total = query.count()
offset = (page - 1) * page_size
tasks = query.offset(offset).limit(page_size).all()
```

### Tại sao query này KHÔNG tải toàn bộ dữ liệu vào RAM?
1. **Tính chất Lazy Evaluation (Thực thi lười) của SQLAlchemy**:
   - Khởi tạo `db.query(Task)` chỉ mới xây dựng cấu trúc truy vấn (AST), hoàn toàn chưa kết nối gửi lệnh tới PostgreSQL.
   - Khi áp dụng `.filter()`, `.offset()`, `.limit()`, SQLAlchemy cộng dồn các mệnh đề SQL vào chuỗi truy vấn.
2. **Thực thi trực tiếp trong Database Engine**:
   - Khi gọi `.all()`, SQLAlchemy mới phát sinh câu lệnh SQL chuẩn gửi xuống PostgreSQL:
     ```sql
     SELECT * FROM tasks 
     WHERE user_id = :user_id AND status = :status 
     LIMIT :limit OFFSET :offset;
     ```
   - Quá trình duyệt và cắt bản ghi diễn ra hoàn toàn bên trong PostgreSQL. Cơ sở dữ liệu chỉ gửi về đúng số lượng bản ghi tương ứng với `page_size` (mặc định 10 dòng) qua network.
   - Ứng dụng Python chỉ cấp phát bộ nhớ RAM cho đúng 10 bản ghi đó thay vì hàng triệu dòng dữ liệu.

---

## 5. THIẾT KẾ CI/CD CHO BÀI TOÁN VPS YẾU

### Bài toán thực tế
Nếu server VPS yếu (ví dụ: 1 vCPU, 1GB RAM) mà thực hiện `docker build` trực tiếp trên server:
- Quá trình tải dependency, giải nén và compile thư viện (như `bcrypt`, `psycopg2`) sẽ khiến **CPU vọt lên 100%**, RAM bị cạn kiệt (dẫn đến lỗi Out Of Memory - OOM).
- Toàn bộ dịch vụ đang chạy trên VPS sẽ bị treo hoặc sập (Downtime).

### Giải pháp kiến trúc CI/CD tối ưu
```
[Developer]
    │  git push origin main
    ▼
[GitHub Actions Runner] (Máy ảo Cloud miễn phí, cấu hình mạnh của GitHub)
    ├── 1. Checkout source code
    ├── 2. Đăng nhập GitHub Container Registry (ghcr.io)
    ├── 3. docker build -t ghcr.io/<owner>/task-management-api:latest .
    └── 4. docker push image lên GHCR
    ▼
[GitHub Container Registry (GHCR)] (Lưu trữ Docker Image đã đóng gói)
    │
    ▼ (Kịch bản Deploy lên VPS)
[VPS Server]
    ├── KHÔNG CẦN source code của dự án
    ├── KHÔNG CẦN cài đặt Python, GCC hay dependencies
    ├── Chỉ nhận lệnh: docker pull ghcr.io/<owner>/task-management-api:latest
    └── Khởi chạy: docker compose up -d (Chỉ mất vài giây và tốn vài MB RAM)
```

**Phân biệt rõ ràng:**
- `docker build`: Tiêu tốn CPU/RAM và thời gian để biên dịch file nhị phân. Thực hiện trên GitHub Actions.
- `docker pull`: Chỉ là thao tác tải file image đã đóng gói về máy qua mạng internet. Thực hiện trên VPS.

---

## 6. CÁC ĐIỂM CODE CHUYÊN SÂU CHỨNG MINH TÍNH TRUNG THỰC

Khi Quản lý chuyên môn hỏi sâu vào các dòng code cụ thể, hãy tự tin chỉ ra 4 giải pháp kỹ thuật thực tế sau:

### 1. Cơ chế Retry kết nối DB xử lý Race Condition (`app/core/database.py`)
- **Vấn đề**: Trong `docker-compose.yml`, chỉ thị `depends_on: - postgres` chỉ đảm bảo container DB được bật lên, chứ chưa đảm bảo PostgreSQL bên trong đã sẵn sàng nhận kết nối socket. Nếu API kết nối ngay sẽ văng lỗi `Connection refused` làm chết container API.
- **Dòng code xử lý**:
  ```python
  # Thử kết nối tối đa 5 lần, mỗi lần cách nhau 2 giây
  for attempt in range(5):
      try:
          with engine.connect() as conn:
              conn.execute(text("SELECT 1"))
          break
      except Exception:
          if attempt < 4:
              time.sleep(2)
          else:
              raise
  ```

### 2. Xử lý an toàn Token Payload tránh lỗi 500 (`app/dependencies/auth.py`)
- **Vấn đề**: Nếu kẻ xấu gửi token hợp lệ về mặt chữ ký nhưng cố tình xóa trường `sub` hoặc truyền `sub: "abc"` không phải số nguyên, code `int(payload["sub"])` sẽ văng lỗi `KeyError` hoặc `ValueError`, khiến FastAPI trả về mã lỗi 500 Internal Server Error (vi phạm tiêu chí chấm điểm).
- **Dòng code xử lý**:
  ```python
  try:
      user_id = int(payload["sub"])
  except (KeyError, ValueError, TypeError):
      raise HTTPException(
          status_code=status.HTTP_401_UNAUTHORIZED,
          detail="Invalid token payload",
      )
  ```

### 3. Phân quyền sở hữu & Trả về 404 thay vì 403 để chặn ID Enumeration (`app/routers/tasks.py`)
- **Vấn đề**: Khi User A cố tình gọi `GET /tasks/99` hoặc `PUT /tasks/99` của User B:
  - Nếu trả về `403 Forbidden`, kẻ tấn công biết được ID `99` có tồn tại trong hệ sinh thái của người khác (lỗ hổng Enumeration Attack).
  - Trả về `404 Not Found` vừa bảo vệ quyền riêng tư, vừa thống nhất logic nghiệp vụ: *"Đối với user hiện tại, task này không hề tồn tại"*.
- **Dòng code xử lý**:
  ```python
  task = db.query(Task).filter(Task.id == task_id, Task.user_id == current_user.id).first()
  if not task:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
  ```

### 4. Đảm bảo toàn vẹn dữ liệu khi Update Task
- **Vấn đề**: Không ghi đè toàn bộ model bằng dữ liệu rỗng nếu người dùng chỉ cập nhật 1 trường (ví dụ chỉ đổi status).
- **Dòng code xử lý**:
  ```python
  for key, value in data.model_dump(exclude_unset=True).items():
      setattr(task, key, value)
  ```
  `exclude_unset=True` đảm bảo chỉ những trường nào client thực sự gửi lên mới được cập nhật vào database.

---

## 7. TIÊU CHÍ CHẶN RỚT: CHUẨN HÓA 100% TIẾNG ANH

- Toàn bộ tên biến, tên hàm, class name, docstring, code comments trong dự án đều tuân thủ 100% bằng tiếng Anh chuẩn.
- Các thông báo lỗi (`detail`) của API:
  - `"Username already exists"`
  - `"Email already exists"`
  - `"Invalid credentials"`
  - `"Authentication required"`
  - `"Invalid or expired token"`
  - `"Task not found"`
- Không chứa bất kỳ từ ngữ tiếng Việt hoặc ký tự non-ASCII nào trong mã nguồn Python.

---

## 8. BỘ CÂU HỎI - ĐÁP NHANH KHI PHỎNG VẤN (FLASHCARDS Q&A)

| Câu hỏi của Giám khảo | Câu trả lời trọng tâm ngắn gọn |
| :--- | :--- |
| **Bảng users và tasks có quan hệ gì?** | Quan hệ 1-N. Bảng `tasks` có khóa ngoại `user_id` liên kết tới khóa chính `users.id`. |
| **Trạng thái của Task có những loại nào?** | Chỉ gồm `pending` và `completed`, được kiểm soát nghiêm ngặt bằng kiểu dữ liệu Enum. |
| **Mật khẩu được lưu trữ ra sao?** | Không lưu plain text. Mật khẩu được hash 1 chiều bằng thuật toán `bcrypt` có kèm salt ngẫu nhiên trước khi ghi vào database. |
| **Tại sao không commit file `.env` lên GitHub?** | Vì file `.env` chứa `SECRET_KEY` và thông tin kết nối DB. Đưa lên Git công khai sẽ bị lộ bí mật bảo mật. Dự án cung cấp `.env.example` làm mẫu cấu hình. |
| **Tại sao không tải toàn bộ dữ liệu lên RAM trước khi phân trang?** | Vì nếu bảng có hàng triệu dòng, tải hết lên RAM sẽ làm tràn bộ nhớ và treo server. Em áp dụng `.offset()` và `.limit()` trực tiếp trên query để database cắt trang và chỉ trả về đúng số dòng cần thiết. |
| **Mục đích của việc build Docker image trên GitHub Actions là gì?** | Giúp tận dụng tài nguyên cloud của GitHub để build image, tránh làm quá tải CPU/RAM trên VPS yếu, giúp quá trình deploy trên VPS chỉ cần `docker pull` nhanh chóng và an toàn. |
| **Khác biệt giữa mã lỗi 401 và 403?** | `401 Unauthorized` là lỗi chưa xác thực (thiếu token, token sai hoặc hết hạn). `403 Forbidden` là đã xác thực danh tính nhưng không có quyền truy cập tài nguyên. |
| **PostgreSQL có cần mở port ra ngoài Internet không?** | Không cần. Container API và Postgres giao tiếp an toàn qua mạng nội bộ Docker network. Việc không expose port 5432 giúp triệt tiêu rủi ro bị tấn công từ bên ngoài. |
