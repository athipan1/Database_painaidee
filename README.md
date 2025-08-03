# Database Painaidee - Flask Backend API

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.3+-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-12+-blue.svg)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**ไปไหนดี** - ระบบจัดการข้อมูลสถานที่ท่องเที่ยวด้วย AI และ Big Data

🚀 A comprehensive Flask backend application for managing Thai attraction data with PostgreSQL, Celery, Redis, and AI-powered features. Perfect for tourism applications, travel platforms, and location-based services.

### 🚀 Try it now:
[![Deploy on HF Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/deploy-to-spaces-md.svg)](https://huggingface.co/spaces/new?template=athipan1/Database_painaidee) [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/athipan1/Database_painaidee/blob/main/Database_Painaidee_Colab.ipynb)

## Table of Contents
- [About This Project](#about-this-project)
- [Features](#features) 
- [Prerequisites](#prerequisites)
- [🚀 Quick Deployment Options](#-quick-deployment-options)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [API Endpoints](#api-endpoints)
- [New Features](#new-features)
- [Environment Variables](#environment-variables)
- [Scheduled Tasks](#scheduled-tasks)
- [Development](#development)
- [Production Deployment](#production-deployment)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## About This Project

**Database Painaidee** is a production-ready Flask backend system designed for Thai tourism applications. It provides comprehensive attraction data management with AI-powered features, real-time analytics, and automated ETL processes.

**Key Use Cases:**
- Tourism mobile apps and websites
- Travel recommendation platforms  
- Location-based marketing systems
- Government tourism analytics
- Travel agency management systems

### Architecture Overview
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Flask API     │    │   Background    │
│   (Mobile/Web)  │◄──►│   (REST/AI)     │◄──►│   Workers       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   PostgreSQL    │    │     Redis       │
                       │   (Data Store)  │    │   (Queue/Cache) │
                       └─────────────────┘    └─────────────────┘
```

## Features

### Core Infrastructure
- ✅ **Flask REST API** with comprehensive attraction data management
- ✅ **PostgreSQL Integration** with SQLAlchemy ORM and automatic deduplication
- ✅ **Background Processing** using Celery + Redis for async operations
- ✅ **Scheduled Jobs** - Automated daily data sync and maintenance (Cron)
- ✅ **Docker Compose** setup for easy deployment and scaling
- ✅ **Modular Architecture** with clean separation of concerns

### Advanced Features  
- 🆕 **AI-Powered Intelligence** - Keyword extraction, content improvement, recommendations
- 🆕 **Behavior Analytics** - User tracking, pattern analysis, predictive insights  
- 🆕 **Auto-Geocoding** - Automatic coordinate calculation via Google/OpenStreetMap APIs
- 🆕 **Real-time Dashboard** - Live monitoring with statistics and interactive charts
- 🆕 **Data Versioning** - Complete change tracking with rollback capabilities
- 🆕 **Automated Backups** - Database snapshots with pg_dump and restore functionality
- 🆕 **Load Balancing** - Multi-worker nginx setup for high availability

### Monitoring & Operations
- 🔧 **Flower Dashboard** support for Celery task monitoring
- 🔧 **Health Checks** - Comprehensive system status monitoring  
- 🔧 **Error Handling** - Robust error tracking and recovery
- 🔧 **API Documentation** - Complete endpoint documentation

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

## Prerequisites

Before running this application, ensure you have:

- **Docker & Docker Compose** (recommended for easy setup)
- **Python 3.8+** (for local development)
- **PostgreSQL 12+** (if running without Docker)
- **Redis 6+** (for background tasks)
- **Git** (for cloning the repository)

Optional for enhanced features:
- **Google Geocoding API Key** (for location services)
- **nginx** (for production load balancing)

## 🚀 Quick Deployment Options

Choose your preferred deployment method to get started quickly:

### 🤗 Deploy on Hugging Face Spaces (Permanent)
Deploy a permanent demo version with web interface:

[![Deploy on HF Spaces](https://huggingface.co/datasets/huggingface/badges/raw/main/deploy-to-spaces-md.svg)](https://huggingface.co/spaces/new?template=athipan1/Database_painaidee)

**Features:**
- 🌐 **Permanent public access** - Available 24/7
- 🖥️ **Web interface** with Gradio
- 🔍 **Interactive search** for Thai attractions
- 📱 **Mobile-friendly** responsive design
- 🆓 **Free hosting** on Hugging Face infrastructure

**Steps to deploy:**
1. Click the "Deploy to Spaces" button above
2. Sign in to your Hugging Face account
3. Name your Space and set it to public
4. The app will automatically build and deploy
5. Access your live demo at `https://huggingface.co/spaces/[your-username]/[space-name]`

### 📓 Run on Google Colab with ngrok (Temporary)
Run the full API temporarily with public access:

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/athipan1/Database_painaidee/blob/main/Database_Painaidee_Colab.ipynb)

**Features:**
- ⚡ **Full API functionality** - All endpoints available
- 🌐 **Public access** via ngrok tunnel
- 🗃️ **Complete database** with PostgreSQL
- 🔄 **Background tasks** with Celery + Redis
- 📊 **Real-time dashboard** included
- 🧪 **Perfect for testing** and development

**Steps to run:**
1. Click "Open in Colab" button above
2. Run all cells in sequence (Runtime → Run all)
3. Get your public ngrok URL from the output
4. Access the API immediately at the provided URL
5. Use the dashboard at `[ngrok-url]/api/dashboard/`

**Note:** Colab deployment is temporary and will end when the session closes.

---

## Quick Start

### Using Docker Compose (Recommended)

1. **Clone and setup environment:**
   ```bash
   git clone https://github.com/athipan1/Database_painaidee.git
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

### Core Attractions API
```http
GET /api/attractions              # Get all attractions
POST /api/attractions/sync        # Manual sync from external API
GET /api/health                   # Health check
```

### Dashboard & Monitoring
```http
GET /api/dashboard/               # Dashboard web interface  
GET /api/dashboard/stats          # Dashboard statistics
GET /api/dashboard/health         # System health status
GET /api/dashboard/attractions/recent  # Recent attractions
GET /api/dashboard/versions/{id}  # Attraction version history
```

### AI Features
```http
POST /api/ai/keywords/extract     # Extract keywords from attraction/text
POST /api/ai/keywords/batch-extract  # Batch keyword extraction
GET /api/ai/recommendations/{user_id}  # AI-powered recommendations
POST /api/ai/interactions         # Track user interactions
GET /api/ai/trends/analyze        # Trend analysis
GET /api/ai/trends/heatmap        # Geographic heatmaps
POST /api/ai/content/improve      # Content improvement
POST /api/ai/conversation/chat    # Conversational AI
```

### Behavior Intelligence
```http
POST /api/behavior/track          # Track user behavior
GET /api/behavior/analyze/{user_id}     # User behavior analysis
GET /api/behavior/recommendations/{user_id}  # Behavior-based recommendations
GET /api/behavior/trends          # Behavioral trends
GET /api/behavior/heatmap         # User activity heatmaps
GET /api/behavior/stats           # System statistics
```

### Root Information
```http
GET /                             # API information and available endpoints
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

Configure the application by copying `.env.example` to `.env` and updating the values:

### Required Variables
```env
# Flask Application
FLASK_ENV=development
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=postgresql://user:password@db:5432/painaidee_db
POSTGRES_DB=painaidee_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# Redis Configuration  
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

### Optional Variables
```env
# External API Settings
EXTERNAL_API_URL=https://jsonplaceholder.typicode.com/posts
API_TIMEOUT=30

# Pagination
PAGINATION_ENABLED=true
PAGINATION_PAGE_SIZE=20
PAGINATION_MAX_PAGES=100

# Geocoding (Optional - for location services)
GOOGLE_GEOCODING_API_KEY=your-google-api-key-here
USE_GOOGLE_GEOCODING=true
GEOCODING_TIMEOUT=10

# Backup Configuration
BACKUP_DIR=/tmp/db_backups
BACKUP_RETENTION_DAYS=7
AUTO_BACKUP_BEFORE_SYNC=true

# Development Settings
DEBUG=True
TESTING=False
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
# Run basic setup and configuration tests
python test_setup.py

# Run comprehensive test suite
python -m pytest -v

# Test specific components
python -m pytest test_new_features.py -v          # Core features
python -m pytest test_ai_features.py -v           # AI functionality  
python -m pytest test_behavior_intelligence.py -v # User behavior analytics
python -m pytest test_etl.py -v                   # ETL processes
python -m pytest test_pagination.py -v            # Pagination features

# Test API endpoints
curl http://localhost:5000/api/health              # Health check
curl http://localhost:5000/api/dashboard/stats     # Dashboard statistics
curl http://localhost:5000/                        # API information
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

## Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Ensure PostgreSQL is running: `docker-compose ps db`
   - Check credentials in `.env` file match `docker-compose.yml`
   - Verify database URL format: `postgresql://user:password@host:port/database`

2. **Celery Worker Not Starting**
   - Check Redis connection: `docker-compose ps redis`
   - Verify `CELERY_BROKER_URL` in environment variables
   - Restart services: `docker-compose restart celery_worker`

3. **External API Timeout/Connection Issues**
   - Check network connectivity and API availability
   - Verify `EXTERNAL_API_URL` configuration
   - Increase `API_TIMEOUT` value in `.env`

4. **Geocoding API Failures**
   - Verify Google Geocoding API key is valid and has quota
   - Check `GOOGLE_GEOCODING_API_KEY` in `.env`
   - Monitor API usage limits in Google Cloud Console

5. **AI Features Not Working**
   - Install optional AI dependencies if needed
   - Check system memory for large model processing
   - Verify fallback methods are working

6. **Docker Build/Container Issues**
   - Clear Docker cache: `docker system prune -f`
   - Rebuild images: `docker-compose build --no-cache`
   - Check Docker logs: `docker-compose logs [service_name]`

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

We welcome contributions to Database Painaidee! Here's how to get started:

### Development Setup
1. Fork the repository
2. Clone your fork locally
3. Create a virtual environment: `python -m venv venv`
4. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
5. Install dependencies: `pip install -r requirements.txt`
6. Copy `.env.example` to `.env` and configure

### Making Changes
1. Create a feature branch: `git checkout -b feature/your-feature-name`
2. Make your changes with clear, focused commits
3. Add tests for new functionality
4. Update documentation as needed
5. Ensure all tests pass: `python -m pytest`

### Submitting Changes
1. Push your changes to your fork
2. Create a Pull Request with a clear description
3. Ensure CI tests pass
4. Respond to code review feedback

### Areas for Contribution
- 🔧 API endpoint improvements
- 🤖 AI/ML model enhancements  
- 📊 Dashboard features
- 🌐 Internationalization (i18n)
- 📚 Documentation improvements
- 🧪 Test coverage expansion

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.