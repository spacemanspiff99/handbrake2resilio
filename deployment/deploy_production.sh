#!/bin/bash

# Production Deployment Script for HandBrake2Resilio
# Deploys to Ubuntu host with security and resource management

set -euo pipefail

# Configuration
TARGET_HOST="akun@192.168.10.18"
TARGET_DIR="/opt/handbrake2resilio"
BACKUP_DIR="/opt/handbrake2resilio/backups"
LOG_FILE="/tmp/handbrake2resilio_deploy_$(date +%Y%m%d_%H%M%S).log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $*" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING:${NC} $*" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR:${NC} $*" | tee -a "$LOG_FILE"
}

# Check if we're in the right directory
if [[ ! -f "docker-compose.production.yml" ]]; then
    error "This script must be run from the handbrake2resilio directory"
    exit 1
fi

# Check if JWT_SECRET_KEY is set
if [[ -z "${JWT_SECRET_KEY:-}" ]]; then
    warn "JWT_SECRET_KEY not set. Generating a secure key..."
    export JWT_SECRET_KEY=$(openssl rand -base64 32)
    log "Generated JWT_SECRET_KEY: ${JWT_SECRET_KEY:0:10}..."
fi

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if target directories exist
    if ! ssh "$TARGET_HOST" "test -d /mnt/tv && test -d /mnt/movies && test -d /mnt/archive"; then
        error "Required directories not found on target host"
        log "Please ensure /mnt/tv, /mnt/movies, and /mnt/archive exist on $TARGET_HOST"
        exit 1
    fi
    
    log "Prerequisites check passed"
}

# Function to backup existing deployment
backup_existing() {
    log "Creating backup of existing deployment..."
    
    if ssh "$TARGET_HOST" "test -d $TARGET_DIR"; then
        BACKUP_NAME="handbrake2resilio_backup_$(date +%Y%m%d_%H%M%S)"
        ssh "$TARGET_HOST" "mkdir -p $BACKUP_DIR && cp -r $TARGET_DIR $BACKUP_DIR/$BACKUP_NAME"
        log "Backup created: $BACKUP_DIR/$BACKUP_NAME"
    else
        log "No existing deployment found, skipping backup"
    fi
}

# Function to build and push Docker image
build_and_push() {
    log "Building production Docker image..."
    
    # Build the image
    docker build -f Dockerfile.production -t handbrake2resilio:production .
    
    if [[ $? -eq 0 ]]; then
        log "Docker image built successfully"
    else
        error "Failed to build Docker image"
        exit 1
    fi
}

# Function to deploy to target host
deploy_to_target() {
    log "Deploying to target host: $TARGET_HOST"
    
    # Create target directory
    ssh "$TARGET_HOST" "mkdir -p $TARGET_DIR"
    
    # Copy necessary files
    log "Copying files to target host..."
    scp docker-compose.production.yml "$TARGET_HOST:$TARGET_DIR/docker-compose.yml"
    scp Dockerfile.production "$TARGET_HOST:$TARGET_DIR/Dockerfile"
    scp requirements.production.txt "$TARGET_HOST:$TARGET_DIR/requirements.txt"
    scp app_improved.py "$TARGET_HOST:$TARGET_DIR/"
    scp config.py "$TARGET_HOST:$TARGET_DIR/"
    scp auth.py "$TARGET_HOST:$TARGET_DIR/"
    scp job_queue.py "$TARGET_HOST:$TARGET_DIR/"
    scp handbrake2resilio.sh "$TARGET_HOST:$TARGET_DIR/"
    scp docker-entrypoint.sh "$TARGET_HOST:$TARGET_DIR/"
    
    # Copy frontend files
    ssh "$TARGET_HOST" "mkdir -p $TARGET_DIR/ui-frontend"
    scp -r ui-frontend/* "$TARGET_HOST:$TARGET_DIR/ui-frontend/"
    
    # Create necessary directories
    ssh "$TARGET_HOST" "mkdir -p $TARGET_DIR/logs $TARGET_DIR/data $TARGET_DIR/ssl"
    
    # Set proper permissions
    ssh "$TARGET_HOST" "chmod +x $TARGET_DIR/*.sh"
    
    log "Files copied successfully"
}

# Function to start services
start_services() {
    log "Starting services on target host..."
    
    # Stop existing containers
    ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose down --remove-orphans" || true
    
    # Start new containers
    ssh "$TARGET_HOST" "cd $TARGET_DIR && JWT_SECRET_KEY=$JWT_SECRET_KEY docker-compose up -d"
    
    if [[ $? -eq 0 ]]; then
        log "Services started successfully"
    else
        error "Failed to start services"
        exit 1
    fi
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait for services to start
    sleep 30
    
    # Check if containers are running
    if ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose ps | grep -q 'Up'"; then
        log "Containers are running"
    else
        error "Containers are not running"
        ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose logs"
        exit 1
    fi
    
    # Check health endpoint
    if curl -f "http://$TARGET_HOST:8080/health" > /dev/null 2>&1; then
        log "Health check passed"
    else
        error "Health check failed"
        exit 1
    fi
    
    log "Deployment verification completed successfully"
}

# Function to show deployment status
show_status() {
    log "Deployment Status:"
    echo "=================="
    echo "Target Host: $TARGET_HOST"
    echo "Target Directory: $TARGET_DIR"
    echo "Backup Directory: $BACKUP_DIR"
    echo "Log File: $LOG_FILE"
    echo ""
    echo "Services:"
    ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose ps"
    echo ""
    echo "Health Check:"
    curl -s "http://$TARGET_HOST:8080/health" | jq . 2>/dev/null || echo "Health check not available"
}

# Main deployment function
main() {
    log "Starting production deployment..."
    log "Target: $TARGET_HOST"
    log "Log file: $LOG_FILE"
    
    # Run deployment steps
    check_prerequisites
    backup_existing
    build_and_push
    deploy_to_target
    start_services
    verify_deployment
    
    log "Production deployment completed successfully!"
    show_status
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "status")
        show_status
        ;;
    "logs")
        ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose logs -f"
        ;;
    "restart")
        log "Restarting services..."
        ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose restart"
        ;;
    "stop")
        log "Stopping services..."
        ssh "$TARGET_HOST" "cd $TARGET_DIR && docker-compose down"
        ;;
    "backup")
        backup_existing
        ;;
    *)
        echo "Usage: $0 {deploy|status|logs|restart|stop|backup}"
        echo ""
        echo "Commands:"
        echo "  deploy  - Deploy to production (default)"
        echo "  status  - Show deployment status"
        echo "  logs    - Show container logs"
        echo "  restart - Restart services"
        echo "  stop    - Stop services"
        echo "  backup  - Create backup of existing deployment"
        exit 1
        ;;
esac 