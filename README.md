# Database Painaidee - Flask Backend API

🚀 A Flask backend application for managing attraction data with PostgreSQL, Celery, and Redis.

## Features

- ✅ **Flask API** with `/attractions` endpoint for external data fetching
- ✅ **PostgreSQL Integration** with SQLAlchemy ORM and data deduplication
- ✅ **Background Tasks** using Celery + Redis
- ✅ **Scheduled Jobs** - Daily data sync at 1:00 AM (Cron schedule)
- ✅ **Docker Compose** setup for easy deployment
- ✅ **Modular Structure** with clean separation of concerns
- ✅ **Flower Dashboard** support for Celery monitoring

## Project Structure

```
/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── config.py            # Configuration settings
│   ├── models.py            # SQLAlchemy models
│   └── routes/
│       ├── __init__.py
│       └── attractions.py   # API routes
├── tasks.py                 # Celery background tasks
├── scheduler.py             # Celery beat scheduler configuration
├── requirements.txt         # Python dependencies
├── .env.example            # Environment variables template
├── docker-compose.yml      # Docker Compose configuration
├── Dockerfile              # Docker image configuration
├── run.py                  # Development server entry point
└── README.md              # This file
```

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and setup environment:**
   ```bash
   git clone <repository-url>
   cd Database_painaidee
   cp .env.example .env
   # Edit .env file with your settings if needed
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Services will be available at:**
   - **Flask API**: http://localhost:5000
   - **PostgreSQL**: localhost:5432
   - **Redis**: localhost:6379

4. **Optional - Start Flower dashboard:**
   ```bash
   docker-compose --profile flower up -d flower
   ```
   - **Flower Dashboard**: http://localhost:5555

### Manual Setup (Development)

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL and Redis locally**

3. **Copy environment file:**
   ```bash
   cp .env.example .env
   # Edit .env with your local database and Redis URLs
   ```

4. **Run Flask development server:**
   ```bash
   python run.py
   ```

5. **Run Celery worker (separate terminal):**
   ```bash
   celery -A tasks.celery worker --loglevel=info
   ```

6. **Run Celery beat scheduler (separate terminal):**
   ```bash
   celery -A scheduler.celery_app beat --loglevel=info
   ```

## API Endpoints

### Health Check
```http
GET /api/health
```

### Get All Attractions
```http
GET /api/attractions
```

### Manual Sync from External API
```http
POST /api/attractions/sync
```

### Root Information
```http
GET /
```

## Environment Variables

Key environment variables (see `.env.example` for all options):

```env
# Flask
FLASK_ENV=development
SECRET_KEY=your-secret-key

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/painaidee_db

# Redis
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0

# External API
EXTERNAL_API_URL=https://jsonplaceholder.typicode.com/posts
```

## Scheduled Tasks

- **Daily Data Sync**: Automatically fetches attraction data from external API at 1:00 AM daily
- **Data Deduplication**: Prevents duplicate entries based on external ID

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild images
docker-compose build

# Start with Flower dashboard
docker-compose --profile flower up -d

# Scale celery workers
docker-compose up -d --scale celery_worker=3
```

## Development

### Adding New Features

1. **Database Models**: Add to `app/models.py`
2. **API Routes**: Add to `app/routes/`
3. **Background Tasks**: Add to `tasks.py`
4. **Scheduled Jobs**: Update `scheduler.py`

### Testing API

```bash
# Health check
curl http://localhost:5000/api/health

# Get attractions
curl http://localhost:5000/api/attractions

# Manual sync
curl -X POST http://localhost:5000/api/attractions/sync
```

## Production Deployment

1. **Update environment variables** for production
2. **Use production WSGI server** (Gunicorn is already configured)
3. **Set up SSL/TLS** with reverse proxy (nginx recommended)
4. **Configure monitoring** with proper logging and health checks

## Monitoring

- **Flower Dashboard**: Monitor Celery tasks and workers
- **Flask Logs**: Application and error logging
- **Database Health**: Connection and query monitoring
- **Redis Health**: Cache and broker monitoring

## Troubleshooting

### Common Issues

1. **Database Connection Error**: Ensure PostgreSQL is running and credentials are correct
2. **Celery Worker Not Starting**: Check Redis connection and broker URL
3. **External API Timeout**: Verify network connectivity and API availability
4. **Docker Build Issues**: Check Dockerfile and requirements.txt

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs celery_worker
docker-compose logs db
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.