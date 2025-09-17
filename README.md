# 🏠 Asset Management Backend

Django REST Framework backend for managing users and properties (real estate assets).
Supports authentication (JWT), property CRUD, media uploads, and MySQL database.

---

## 🚀 Features

- Custom User model with email login
- JWT authentication (login, refresh, change password, profile)
- Property CRUD with filtering & image upload
- Admin panel for superusers
- Dockerized setup (Django + MySQL)
- Environment-based configuration (`.env`)

---

## 🛠 Requirements

- Python 3.11+ (for local dev)
- MySQL 8+
- Docker & Docker Compose (for containerized setup)

---

## ⚙️ Installation (Local)

```bash
git clone https://github.com/yourusername/asset-management-backend.git
cd asset-management-backend

# Create env file
cp .env.example .env

# Create virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows PowerShell

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run dev server
python manage.py runserver
````

---

## 🐳 Installation (Docker)

```bash
git clone https://github.com/yourusername/asset-management-backend.git
cd asset-management-backend

# Create env file
cp .env.example .env

# Build and start services
docker compose up --build
```

* Backend → [http://127.0.0.1:8000](http://127.0.0.1:8000)
* Admin → [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
* Media → [http://127.0.0.1:8000/media/](http://127.0.0.1:8000/media/)

---

## 🌐 API Endpoints

### 🔑 Auth

* `POST /api/auth/register/` → Register a new user
* `POST /api/auth/token/` → Login (get JWT access & refresh)
* `POST /api/auth/token/refresh/` → Refresh access token
* `GET /api/auth/profile/` → Get current user profile
* `PUT /api/auth/profile/` → Update profile
* `PUT /api/auth/change-password/` → Change password

### 🏡 Properties

* `GET /api/properties/` → List user’s properties (supports filters: price\_min, price\_max, purchase\_date\_from, etc.)
* `POST /api/properties/` → Create property (with optional image upload)
* `GET /api/properties/{id}/` → Retrieve property by ID
* `PUT /api/properties/{id}/` → Update property
* `DELETE /api/properties/{id}/` → Delete property

---

## 🧪 Smoke Tests (with curl)

### 1. Register

```bash
curl -X POST http://127.0.0.1:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "name": "User One", "password": "pass1234"}'
```

### 2. Login

```bash
curl -X POST http://127.0.0.1:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user1@example.com", "password": "pass1234"}'
```

> Copy `"access"` token from the response.

### 3. Get Profile

```bash
curl -X GET http://127.0.0.1:8000/api/auth/profile/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

### 4. Create Property

```bash
curl -X POST http://127.0.0.1:8000/api/properties/ \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -F "title=My House" \
  -F "address=123 Street" \
  -F "property_type=house" \
  -F "price=250000" \
  -F "image=@/path/to/photo.jpg"
```

### 5. List Properties

```bash
curl -X GET "http://127.0.0.1:8000/api/properties/?price_min=100000&price_max=500000" \
  -H "Authorization: Bearer <ACCESS_TOKEN>"
```

---
### 🏡 Property Filters

The `/api/properties/` endpoint supports filtering via query parameters:

| Filter                | Example                                   | Description                                |
|------------------------|-------------------------------------------|--------------------------------------------|
| `price_min`           | `/api/properties/?price_min=100000`       | Return properties with `price >= 100000`   |
| `price_max`           | `/api/properties/?price_max=500000`       | Return properties with `price <= 500000`   |
| `purchase_date_from`  | `/api/properties/?purchase_date_from=2023-01-01` | Purchased on/after given date       |
| `purchase_date_to`    | `/api/properties/?purchase_date_to=2023-12-31`   | Purchased on/before given date      |
| `created_from`        | `/api/properties/?created_from=2024-01-01`       | Created on/after given date         |

#### 🔎 Examples

- Properties priced between 100k–500k:
  ```http
  GET /api/properties/?price_min=100000&price_max=500000
  ```

* Properties purchased in 2023:

  ```http
  GET /api/properties/?purchase_date_from=2023-01-01&purchase_date_to=2023-12-31
  ```

* Properties created since Jan 2024:

  ```http
  GET /api/properties/?created_from=2024-01-01
  ```

---

## 🗂 Project Structure

```
asset-management-backend/
├── apps/
│   ├── authentication/     # custom user model & auth
│   ├── properties/         # property CRUD & filters
├── asset_management/
│   ├── settings.py         # single settings file
│   ├── urls.py
│   └── wsgi.py
├── docker/
│   └── entrypoint.sh
├── media/                  # uploaded property images
├── .env.example
├── docker-compose.yml
├── Dockerfile
├── manage.py
└── requirements.txt
```

---

## 📜 License
```
MIT (update if needed).
```
---