#!/bin/bash

# Development helper script for running individual services
# Usage: ./dev.sh [service]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_help() {
    echo -e "${BLUE}Development Helper Script${NC}"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  flask         - Run Flask development server"
    echo "  celery        - Run Celery worker"
    echo "  beat          - Run Celery beat scheduler"
    echo "  flower        - Run Flower dashboard"
    echo "  test          - Run setup tests"
    echo "  init-db       - Initialize database"
    echo "  docker        - Start all services with Docker Compose"
    echo "  docker-flower - Start Docker services including Flower"
    echo "  stop          - Stop Docker services"
    echo "  logs          - Show Docker logs"
    echo "  install       - Install Python dependencies"
    echo "  help          - Show this help"
    echo ""
    echo "Examples:"
    echo "  $0 docker       # Start all services"
    echo "  $0 flask        # Run only Flask dev server"
    echo "  $0 test         # Run tests to verify setup"
}

check_env() {
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found. Copying from .env.example...${NC}"
        cp .env.example .env
        echo -e "${GREEN}.env file created. Please review and update if needed.${NC}"
    fi
}

run_flask() {
    echo -e "${GREEN}Starting Flask development server...${NC}"
    check_env
    export FLASK_APP=app
    export FLASK_ENV=development
    python run.py
}

run_celery() {
    echo -e "${GREEN}Starting Celery worker...${NC}"
    check_env
    celery -A tasks.celery worker --loglevel=info
}

run_beat() {
    echo -e "${GREEN}Starting Celery beat scheduler...${NC}"
    check_env
    celery -A scheduler.celery_app beat --loglevel=info
}

run_flower() {
    echo -e "${GREEN}Starting Flower dashboard...${NC}"
    check_env
    celery -A tasks.celery flower --host=0.0.0.0 --port=5555
}

run_test() {
    echo -e "${GREEN}Running setup tests...${NC}"
    python test_setup.py
    echo -e "${GREEN}Running pytest integration test...${NC}"
    python test_pytest_integration.py
}

init_database() {
    echo -e "${GREEN}Initializing database...${NC}"
    check_env
    python init_db.py
}

run_docker() {
    echo -e "${GREEN}Starting all services with Docker Compose...${NC}"
    docker compose up -d
    echo -e "${GREEN}Services started. Check status with: docker compose ps${NC}"
    echo -e "${BLUE}API available at: http://localhost:5000${NC}"
}

run_docker_flower() {
    echo -e "${GREEN}Starting all services including Flower...${NC}"
    docker compose --profile flower up -d
    echo -e "${GREEN}Services started. Check status with: docker compose ps${NC}"
    echo -e "${BLUE}API available at: http://localhost:5000${NC}"
    echo -e "${BLUE}Flower dashboard at: http://localhost:5555${NC}"
}

stop_docker() {
    echo -e "${YELLOW}Stopping Docker services...${NC}"
    docker compose down
    echo -e "${GREEN}Services stopped.${NC}"
}

show_logs() {
    echo -e "${GREEN}Showing Docker logs...${NC}"
    docker compose logs -f
}

install_deps() {
    echo -e "${GREEN}Installing Python dependencies...${NC}"
    pip install -r requirements.txt
    echo -e "${GREEN}Dependencies installed.${NC}"
}

# Main script logic
case "${1:-help}" in
    flask)
        run_flask
        ;;
    celery)
        run_celery
        ;;
    beat)
        run_beat
        ;;
    flower)
        run_flower
        ;;
    test)
        run_test
        ;;
    init-db)
        init_database
        ;;
    docker)
        run_docker
        ;;
    docker-flower)
        run_docker_flower
        ;;
    stop)
        stop_docker
        ;;
    logs)
        show_logs
        ;;
    install)
        install_deps
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo ""
        print_help
        exit 1
        ;;
esac