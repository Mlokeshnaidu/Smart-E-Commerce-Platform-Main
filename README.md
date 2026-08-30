# Smart E-Commerce Platform (Full Stack Architecture)

A production-grade, modular Smart E-Commerce Platform built with **FastAPI** (asynchronous core APIs, cart, checkout, payments, and real-time WebSockets) and **Django** (enterprise admin management, Chart.js analytics dashboard, and automated CSV/PDF report generators).

---

## 🏛️ System Architecture

```
                               ┌─────────────────────────┐
                               │   Client Applications   │
                               │ (Web / Mobile / Postman)│
                               └───────────┬─────────────┘
                                           │
                    ┌──────────────────────┴──────────────────────┐
                    │                                             │
             REST & WebSockets                             Admin & Analytics
                    │                                             │
                    ▼                                             ▼
       ┌─────────────────────────┐                   ┌─────────────────────────┐
       │     FastAPI Backend     │                   │   Django Admin Panel    │
       │       (Port 8000)       │                   │       (Port 8002)       │
       ├─────────────────────────┤                   ├─────────────────────────┤
       │ • JWT & Auth0 Social    │                   │ • User / Product / Order│
       │ • Product Catalog       │                   │   Management & Actions  │
       │ • Cart & Tax Engine     │                   │ • Chart.js Telemetry    │
       │ • Stripe Checkout API   │                   │ • PDF & CSV Report Gen  │
       │ • Real-time WebSockets  │                   │ • Staff Access Controls │
       └────────────┬────────────┘                   └────────────┬────────────┘
                    │                                             │
                    └──────────────────────┬──────────────────────┘
                                           │
                                           ▼
                              ┌─────────────────────────┐
                              │     Shared Database     │
                              │  (SQLite / PostgreSQL)  │
                              └─────────────────────────┘
```

---

## 📋 Milestones & Tasks Completed

| Milestone | Key Implementations |
| :--- | :--- |
| **Task 3: Authentication & RBAC** | • Email & password registration/login with Bcrypt hashing.<br>• JWT Access & Refresh token rotation.<br>• Auth0 Social Login integration (`/auth/social-login`).<br>• Role-Based Access Control (`admin`, `staff`, `customer`). |
| **Task 4: Product Catalog & Cart** | • Product catalog with multi-filter queries (`category`, `price range`, `in_stock`, `sort_by_popularity`).<br>• Full cart operations (`/cart/add`, `/cart/update`, `/cart/remove`, `/cart`).<br>• Automatic tax, item totals, and grand total calculations. |
| **Task 5: Checkout & Stripe Payments** | • Cart stock validation & decrement at checkout.<br>• Stripe Checkout Session and Payment Intent creation.<br>• Stripe Webhook listener (`/checkout/webhook`) updating order state (`paid`, `shipped`, `delivered`, `cancelled`). |
| **Task 6: Notifications & WebSockets** | • Database-backed user notifications with read status.<br>• SMTP email alerts for order confirmation, payment status, and shipping.<br>• Real-time WebSocket endpoint (`/ws/notifications`) pushing live `order_status_updated` and `cart_updated` events. |
| **Task 7: Django Admin & Analytics** | • Enterprise Django Admin management for Users, Products, Carts, Orders, Payments, and Notifications.<br>• Interactive **Chart.js** analytics dashboard (revenue trends, top products, low stock alerts).<br>• One-click export for **CSV** and **PDF** reports (Orders, Sales, Users) via ReportLab. |

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- Python 3.10+ installed
- Virtual environment created and activated:
```bash
python -m venv .venv
.\.venv\Scripts\activate      # Windows
# or: source .venv/bin/activate  # Linux/macOS
```

### 2. Install Dependencies
```bash
# Install FastAPI backend dependencies
pip install -r project-root/requirements.txt

# Install Django admin & reporting dependencies
pip install -r django_admin/requirements.txt
```

### 3. Seed Demo Data
Populate the database with sample users, catalog products, initial orders, payments, and notifications:
```bash
python seed_data.py
```

### 4. Run Django Migrations & Setup Admin Superuser
```bash
cd django_admin
python manage.py migrate
python manage.py shell -c "from django.contrib.auth.models import User; User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', 'admin@example.com', 'AdminPassword123!')"
cd ..
```

---

## 🖥️ Running the Services

### Start FastAPI Backend (Port 8000)
```bash
cd project-root
uvicorn main:app --reload --port 8000
```
- **API Docs (Swagger UI)**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **API Alternative (ReDoc)**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### Start Django Admin & Analytics (Port 8002)
```bash
cd django_admin
python manage.py runserver 8002
```
- **Analytics Dashboard**: [http://127.0.0.1:8002/admin/dashboard/](http://127.0.0.1:8002/admin/dashboard/)
- **Reports Export Center**: [http://127.0.0.1:8002/admin/reports/](http://127.0.0.1:8002/admin/reports/)
- **Django Standard Admin**: [http://127.0.0.1:8002/admin/](http://127.0.0.1:8002/admin/)

### Open Frontend Storefront
Open [`frontend/index.html`](file:///c:/Users/manda/OneDrive/Desktop/ai%20saas%20backend%20training/smart-ecommerce-mainplatform/frontend/index.html) directly in your browser or run:
```bash
cd frontend
python -m http.server 3000
```
Then visit [http://127.0.0.1:3000](http://127.0.0.1:3000).

---

## 🔑 Pre-Configured Demo Credentials

| Role | Email | Password | Access Level |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@example.com` | `Password123!` | Full admin rights, product CRUD, user role management, analytics |
| **Staff** | `staff@example.com` | `Password123!` | Order fulfillment, inventory management, analytics view |
| **Customer** | `customer@example.com` | `Password123!` | Browse products, cart operations, checkout, live notifications |
| **Django Superuser** | `admin` | `AdminPassword123!` | Full Django Admin backend portal access |

---

## 📬 Postman Collection

Import `postman_collection.json` into Postman. It includes pre-configured folders and requests:
1. `1. Authentication & RBAC (Task 3)`
2. `2. User Management (Task 3 & 7)`
3. `3. Product Catalog & Filters (Task 4)`
4. `4. Shopping Cart System (Task 4)`
5. `5. Checkout & Payments (Task 5)`
6. `6. Notifications & WebSockets (Task 6)`
7. `7. Admin Analytics & Reporting (Task 7)`

---

## 🐳 Optional Docker Deployment

Run the complete multi-service stack with Docker Compose:
```bash
docker-compose up --build
```
- FastAPI Backend: `http://localhost:8000`
- Django Admin & Analytics: `http://localhost:8002`
