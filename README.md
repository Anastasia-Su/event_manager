# Event Manager API

A RESTful API for managing events and user registrations. Built with Django REST Framework and designed to be run locally or via Docker.


## Tech Stack

- **Python 3.12**
- **Django** + **Django REST Framework**
- **PostgreSQL 17**
- **JWT Authentication** (SimpleJWT)
- **Uvicorn** 
- **Docker** + **Docker Compose**
- **uv** (dependency management)


## Features

- **Custom user model** — email-based authentication, no username required
- **Account activation** — users receive a one-time token via email; account stays inactive until verified
- **JWT authentication** — secure login with access/refresh tokens and full token blacklisting on logout
- **Event management** — full CRUD with organizer-only write access; only the creator can edit or delete their event
- **Event registration** — authenticated users can register for an event with duplicate prevention; email is sent
- **Registration cancellation** — users can cancel their registration; email is sent
- **Filtering & search** — filter events by date/location, search by title or description
- **Ordering** — sort events by date, title, or location (ascending and descending)
- **Pagination** — page-based pagination on all event listings
- **Auto-generated API docs** — interactive Swagger UI and ReDoc available out of the box via `drf-spectacular`


## Validations

### User Registration
- Email must be unique
- Password minimum 8 characters
- Password must contain at least one uppercase letter, lowercase letter, and digit
- Password confirmation must match

### Account Activation
- Token must exist and belong to the provided email
- Token expires after 24 hours and is deleted on expiry
- Token is deleted after successful activation (one-time use)

### Events
- Event date cannot be in the past
- Title, date, and location combination must be unique (no duplicate events)
- Only the organizer can update or delete their own event

### Event Registration
- A user cannot register for the same event twice
- Cannot register for a past event
- Cannot cancel registration for a past event


## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/Anastasia-Su/event_manager.git
cd event_manager
```

### 2. Create `.env` file

Create a `.env` file based on `.env.sample`:
```bash
SECRET_KEY=DJANGO_SECRET_KEY

POSTGRES_HOST=db
POSTGRES_DB=events_db
POSTGRES_USER=admin
POSTGRES_PASSWORD=password

PGADMIN_DEFAULT_EMAIL=admin@admin.com
PGADMIN_DEFAULT_PASSWORD=admin
```
### 3. Install dependencies and activate virtual environment

```bash
pip install uv
uv sync

# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
```

### 4. Run migrations, seed data, and start the server

```bash
python manage.py migrate
python manage.py populate_db
python manage.py runserver                
```

## Running with Docker
 
```bash
docker compose up -d --build
```

Seed the database inside the container if needed:
```bash
docker compose exec web python manage.py populate_db
```

### Services

| Service | URL |
|---------|-----|
| Django API | `http://localhost:8000` |
| pgAdmin | `http://localhost:8080` |

## API Documentation

Once the app is running:

* **Swagger UI**: `http://127.0.0.1:8000/api/doc/swagger/`
* **ReDoc**: `http://127.0.0.1:8000/api/doc/redoc`



