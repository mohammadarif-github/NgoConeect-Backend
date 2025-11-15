# NGO Connect Backend

Django REST API backend for the NGO Connect platform.

## Features

- Django 4.2+ with Django REST Framework
- PostgreSQL database
- JWT Authentication with SimpleJWT
- Celery for async tasks
- Celery Beat for scheduled tasks
- Redis for caching and message broker
- Docker & Docker Compose setup
- Email integration with Postmark
- API documentation with drf-spectacular
- CORS support for frontend integration

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

## Getting Started

### 1. Clone the repository

```bash
git clone <repository-url>
cd NgoConnect-backend
```

### 2. Create environment file

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
```

Edit `.env` and set your configuration values:
- Database credentials
- Django SECRET_KEY
- Postmark API key
- Frontend URL
- etc.

### 3. Build and run with Docker Compose

```bash
docker compose build
docker compose up
```

The application will be available at `http://localhost:8000`

### Services

- **app**: Main Django application (port 8000)
- **db**: PostgreSQL database
- **redis**: Redis server (port 6379)
- **celery**: Celery worker for async tasks
- **celery-beat**: Celery beat scheduler

## Development

### Running Commands

Execute Django management commands:

```bash
docker compose exec app python manage.py <command>
```

Examples:
```bash
# Create superuser
docker compose exec app python manage.py createsuperuser

# Make migrations
docker compose exec app python manage.py makemigrations

# Run migrations
docker compose exec app python manage.py migrate

# Collect static files
docker compose exec app python manage.py collectstatic
```

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f app
docker compose logs -f celery
```

### Running Tests

```bash
docker compose exec app python manage.py test
```

## Project Structure

```
NgoConnect-backend/
├── docker-compose.yml       # Docker Compose configuration
├── dockerfile               # Docker image definition
├── requirements.txt         # Python dependencies
├── requirements.dev.txt     # Development dependencies
├── .env                     # Environment variables (not in git)
├── .env.example            # Environment variables template
├── scripts/
│   └── run.sh              # Startup script
└── ngoconnect/
    ├── manage.py           # Django management script
    ├── core/               # Core app with utilities
    │   └── management/
    │       └── commands/
    │           └── wait_for_db.py  # Database wait command
    └── ngoconnect/
        ├── __init__.py     # Celery app initialization
        ├── settings.py     # Django settings
        ├── urls.py         # URL configuration
        ├── wsgi.py         # WSGI configuration
        └── celery.py       # Celery configuration
```

## API Documentation

Once the server is running, API documentation is available at:
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`
- OpenAPI Schema: `http://localhost:8000/api/schema/`

## Environment Variables

See `.env.example` for all available environment variables.

Key variables:
- `DEBUG`: Enable/disable debug mode (0 or 1)
- `SECRET_KEY`: Django secret key
- `DB_*`: Database configuration
- `CELERY_BROKER_URL`: Redis URL for Celery
- `FRONTEND_URL`: Frontend application URL
- `POSTMARK_API_KEY`: Email service API key

## Production Deployment

1. Set `DEBUG=0` in environment
2. Update `SECRET_KEY` with a strong random value
3. Set appropriate `ALLOWED_HOSTS`
4. Configure SSL/HTTPS
5. Use a production-grade WSGI server (uWSGI is included)
6. Set up proper logging and monitoring
7. Regular database backups

## License

[Add your license here]
