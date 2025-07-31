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
- 🆕 **Auto-Geocoding** - Automatically calculate coordinates using Google/OpenStreetMap APIs
- 🆕 **Real-time Dashboard** - Monitor ETL operations with statistics and charts
- 🆕 **Data Versioning** - Track changes with attraction history and rollback capability
- 🆕 **Automated Backups** - Database snapshots with pg_dump and rollback functionality
- 🆕 **Load Balancing** - Multi-worker setup with nginx for scaling

## Project Structure

```
/
├── app/
│   ├── __init__.py          # Flask application factory
│   ├── config.py            # Configuration settings
│   ├── models.py            # SQLAlchemy models (Attraction, AttractionHistory, SyncStatistics)
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── attractions.py   # API routes
│   │   └── dashboard.py     # Dashboard routes
│   ├── services/            # Business logic services
│   │   ├── __init__.py
│   │   ├── geocoding.py     # Geocoding service (Google/OSM)
│   │   ├── versioning.py    # Data versioning service
│   │   └── backup.py        # Database backup service
│   └── templates/
│       └── dashboard.html   # Dashboard web interface
├── extractors/              # Data extraction modules
├── transformers/            # Data transformation modules
├── loaders/                 # Data loading modules
├── tasks.py                 # Celery background tasks
├── scheduler.py             # Celery beat scheduler configuration
├── nginx.conf              # Nginx load balancer configuration
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
   # Edit .env file with your API keys and settings
   ```

2. **Start all services:**
   ```bash
   docker-compose up -d
   ```

3. **Start with load balancing and scaling:**
   ```bash
   # Start with nginx load balancer
   docker-compose --profile loadbalancer up -d
   
   # Start with specialized workers
   docker-compose --profile scaling up -d
   
   # Scale web services
   docker-compose up -d --scale web=3
   ```

4. **Services will be available at:**
   - **Flask API**: http://localhost:5000
   - **Dashboard**: http://localhost:5000/api/dashboard
   - **Load Balancer**: http://localhost:80 (when using nginx profile)
   - **PostgreSQL**: localhost:5432
   - **Redis**: localhost:6379

5. **Optional - Start Flower dashboard:**
   ```bash
   docker-compose --profile flower up -d flower
   ```
   - **Flower Dashboard**: http://localhost:5555

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

### Dashboard
```http
GET /api/dashboard/
GET /api/dashboard/stats
GET /api/dashboard/health
GET /api/dashboard/attractions/recent
GET /api/dashboard/versions/{attraction_id}
```

### Root Information
```http
GET /
```

## New Features

### 1. Auto-Geocoding System

Automatically converts location names to coordinates using Google Geocoding API or OpenStreetMap.

**Environment Variables:**
```env
GOOGLE_GEOCODING_API_KEY=your-google-api-key-here
USE_GOOGLE_GEOCODING=true
GEOCODING_TIMEOUT=10
```

**Features:**
- Supports both Google Maps API and OpenStreetMap Nominatim
- Rate limiting to respect API limits
- Automatic province extraction from attraction titles
- Batch geocoding with configurable delays
- Marks geocoded attractions with `geocoded=true` flag

### 2. Real-time Dashboard

Web-based monitoring interface for ETL operations and system health.

**Accessible at:** `/api/dashboard/`

**Features:**
- Live statistics with auto-refresh every 30 seconds
- 30-day sync history with interactive charts
- Today's sync performance metrics
- Success rate and processing time analytics
- Recent attractions with version counts
- Geocoding coverage statistics

### 3. Data Versioning System

Automatic versioning of attraction data with history tracking and rollback capability.

**Features:**
- Automatic version creation before updates
- Complete history tracking in `attractions_history` table
- Version rollback functionality
- Configurable version retention (default: 10 versions)
- Weekly cleanup of old versions

### 4. Automated Backup System

Database backup and restore functionality with automated scheduling.

**Environment Variables:**
```env
BACKUP_DIR=/tmp/db_backups
BACKUP_RETENTION_DAYS=7
AUTO_BACKUP_BEFORE_SYNC=true
```

**Features:**
- Daily automated backups at 12:30 AM
- Pre-sync backups before ETL operations
- Automated cleanup of old backups
- PostgreSQL pg_dump integration
- Backup restore functionality

### 5. Load Balancing & Scaling

Multi-worker architecture with nginx load balancer support.

**Worker Types:**
- **General Workers**: Handle default tasks
- **Heavy Workers**: ETL operations, geocoding (low concurrency)
- **Light Workers**: Cleanup, backup tasks (high concurrency)

**Scaling Commands:**
```bash
# Scale web servers
docker-compose up -d --scale web=3

# Start specialized workers
docker-compose --profile scaling up -d

# Start with load balancer
docker-compose --profile loadbalancer up -d
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

# Geocoding
GOOGLE_GEOCODING_API_KEY=your-google-api-key-here
USE_GOOGLE_GEOCODING=true

# Backup
BACKUP_DIR=/tmp/db_backups
AUTO_BACKUP_BEFORE_SYNC=true
```

## Scheduled Tasks

- **Daily Data Sync**: 1:00 AM - Fetch data from external API
- **Daily Geocoding**: 2:00 AM - Geocode attractions without coordinates
- **Daily Backup**: 12:30 AM - Create database backup before sync
- **Weekly Cleanup**: Sunday 3:00 AM - Clean up old versions and backups

## Docker Commands

```bash
# Start all services
docker-compose up -d

# Start with load balancing
docker-compose --profile loadbalancer up -d

# Start with specialized workers
docker-compose --profile scaling up -d

# Scale web services
docker-compose up -d --scale web=3

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Rebuild images
docker-compose build

# Start with Flower dashboard
docker-compose --profile flower up -d
```

## Development

### Adding New Features

1. **Database Models**: Add to `app/models.py`
2. **API Routes**: Add to `app/routes/`
3. **Background Tasks**: Add to `tasks.py`
4. **Scheduled Jobs**: Update `scheduler.py`
5. **Services**: Add business logic to `app/services/`

### Testing

```bash
# Test setup and configuration
python test_setup.py

# Run new feature tests
python -m pytest test_new_features.py -v

# Run all tests
python -m pytest -v

# Health check
curl http://localhost:5000/api/health

# Dashboard stats
curl http://localhost:5000/api/dashboard/stats
```

## Production Deployment

1. **Update environment variables** for production
2. **Set up SSL/TLS** with reverse proxy (nginx recommended)
3. **Configure monitoring** with proper logging and health checks
4. **Set up backup retention** and off-site storage
5. **Configure load balancing** with multiple web instances
6. **Set up API keys** for geocoding services

## Monitoring

- **Real-time Dashboard**: Monitor sync operations and system health
- **Flower Dashboard**: Monitor Celery tasks and workers
- **Flask Logs**: Application and error logging
- **Database Health**: Connection and query monitoring
- **Redis Health**: Cache and broker monitoring
- **Backup Status**: Automated backup monitoring

## Troubleshooting

### Common Issues

1. **Database Connection Error**: Ensure PostgreSQL is running and credentials are correct
2. **Celery Worker Not Starting**: Check Redis connection and broker URL
3. **External API Timeout**: Verify network connectivity and API availability
4. **Geocoding API Limits**: Check API key limits and rate limiting
5. **Backup Failures**: Verify pg_dump availability and permissions
6. **Docker Build Issues**: Check Dockerfile and requirements.txt

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs web
docker-compose logs celery_worker
docker-compose logs db

# View dashboard logs
docker-compose logs web | grep dashboard
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Update documentation
6. Test thoroughly
7. Submit a pull request

## License

This project is licensed under the MIT License.