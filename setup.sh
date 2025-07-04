#!/bin/bash

# FBX to MDL Converter Setup Script
# This script helps set up the environment for the FBX to MDL converter

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if running as root
check_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root"
        exit 1
    fi
}

# Check system requirements
check_system() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "This script is designed for Linux systems"
        exit 1
    fi
    
    # Check for required commands
    local required_commands=("curl" "wget" "git" "docker")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            log_error "$cmd is required but not installed"
            exit 1
        fi
    done
    
    log_success "System requirements check passed"
}

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p docker
    mkdir -p data/{uploads,outputs,wine}
    mkdir -p nginx
    
    log_success "Directories created"
}

# Download studiomdl.exe (placeholder function)
setup_studiomdl() {
    log_info "Setting up studiomdl.exe..."
    
    if [[ ! -f "docker/studiomdl.exe" ]]; then
        log_warning "studiomdl.exe not found in docker/ directory"
        log_info "You need to manually copy studiomdl.exe from the GoldSrc SDK"
        log_info "Please follow these steps:"
        echo "  1. Download the Half-Life SDK from Valve"
        echo "  2. Extract and locate studiomdl.exe"
        echo "  3. Copy it to: $(pwd)/docker/studiomdl.exe"
        echo "  4. Run this script again"
        
        read -p "Do you have studiomdl.exe ready? (y/N): " -n 1 -r
        echo
        
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            log_error "studiomdl.exe is required for the conversion process"
            exit 1
        fi
        
        # Check again
        if [[ ! -f "docker/studiomdl.exe" ]]; then
            log_error "studiomdl.exe still not found in docker/ directory"
            exit 1
        fi
    fi
    
    # Make executable
    chmod +x docker/studiomdl.exe
    log_success "studiomdl.exe configured"
}

# Create nginx configuration
create_nginx_config() {
    log_info "Creating nginx configuration..."
    
    cat > nginx/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream fbx_converter {
        server fbx-to-mdl-converter:5000;
    }
    
    server {
        listen 80;
        server_name localhost;
        
        client_max_body_size 100M;
        
        location / {
            proxy_pass http://fbx_converter;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # WebSocket support for real-time updates
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            
            # Timeouts for long conversion processes
            proxy_connect_timeout 300s;
            proxy_send_timeout 300s;
            proxy_read_timeout 300s;
        }
    }
}
EOF
    
    log_success "Nginx configuration created"
}

# Create environment file
create_env_file() {
    log_info "Creating environment file..."
    
    # Generate a secret key
    SECRET_KEY=$(openssl rand -hex 32)
    
    cat > .env << EOF
# FBX to MDL Converter Environment Configuration
SECRET_KEY=${SECRET_KEY}
FLASK_ENV=production
WINEPREFIX=/root/.wine
WINEARCH=win32

# Rate limiting (requests per hour per IP)
RATE_LIMIT_MAX_REQUESTS=5
RATE_LIMIT_TIME_WINDOW=3600

# File size limits (in bytes)
MAX_FILE_SIZE=104857600

# Processing timeouts (in seconds)
BLENDER_TIMEOUT=300
STUDIOMDL_TIMEOUT=120
EOF
    
    log_success "Environment file created"
}

# Build Docker image
build_docker_image() {
    log_info "Building Docker image..."
    
    if ! docker build -t fbx-to-mdl-converter .; then
        log_error "Failed to build Docker image"
        exit 1
    fi
    
    log_success "Docker image built successfully"
}

# Test the setup
test_setup() {
    log_info "Testing the setup..."
    
    # Start the container in test mode
    log_info "Starting container for testing..."
    
    if docker-compose up -d fbx-to-mdl-converter; then
        log_info "Waiting for container to start..."
        sleep 10
        
        # Test health endpoint
        if curl -f http://localhost:5000/health &> /dev/null; then
            log_success "Health check passed"
        else
            log_error "Health check failed"
            docker-compose logs fbx-to-mdl-converter
            exit 1
        fi
        
        # Stop test container
        docker-compose down
        log_success "Setup test completed successfully"
    else
        log_error "Failed to start container"
        exit 1
    fi
}

# Main menu
show_menu() {
    echo
    echo "=== FBX to MDL Converter Setup ==="
    echo "1. Full setup (recommended for first-time users)"
    echo "2. Build Docker image only"
    echo "3. Create configuration files only"
    echo "4. Test existing setup"
    echo "5. Start application"
    echo "6. Stop application"
    echo "7. View logs"
    echo "8. Clean up (remove containers and images)"
    echo "0. Exit"
    echo
}

# Full setup
full_setup() {
    log_info "Starting full setup..."
    
    check_root
    check_system
    create_directories
    setup_studiomdl
    create_nginx_config
    create_env_file
    build_docker_image
    test_setup
    
    log_success "Full setup completed!"
    log_info "You can now start the application with: ./setup.sh"
    log_info "Or use option 5 from the menu"
}

# Start application
start_application() {
    log_info "Starting FBX to MDL Converter..."
    
    if docker-compose up -d; then
        log_success "Application started successfully"
        log_info "Access the application at: http://localhost:5000"
        log_info "View logs with: ./setup.sh (option 7)"
    else
        log_error "Failed to start application"
        exit 1
    fi
}

# Stop application
stop_application() {
    log_info "Stopping FBX to MDL Converter..."
    docker-compose down
    log_success "Application stopped"
}

# View logs
view_logs() {
    log_info "Viewing application logs (Ctrl+C to exit)..."
    docker-compose logs -f fbx-to-mdl-converter
}

# Clean up
cleanup() {
    log_warning "This will remove all containers, images, and volumes"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Cleaning up..."
        docker-compose down -v
        docker rmi fbx-to-mdl-converter 2>/dev/null || true
        log_success "Cleanup completed"
    fi
}

# Main script logic
main() {
    # If no arguments, show menu
    if [[ $# -eq 0 ]]; then
        # Check if setup has been run before
        if [[ -f ".env" && -f "docker/studiomdl.exe" ]]; then
            # Quick start
            start_application
            return
        fi
        
        while true; do
            show_menu
            read -p "Choose an option: " choice
            case $choice in
                1) full_setup ;;
                2) build_docker_image ;;
                3) create_nginx_config && create_env_file ;;
                4) test_setup ;;
                5) start_application ;;
                6) stop_application ;;
                7) view_logs ;;
                8) cleanup ;;
                0) exit 0 ;;
                *) log_error "Invalid option" ;;
            esac
            echo
            read -p "Press Enter to continue..."
        done
    fi
    
    # Handle command line arguments
    case "$1" in
        "setup") full_setup ;;
        "start") start_application ;;
        "stop") stop_application ;;
        "logs") view_logs ;;
        "clean") cleanup ;;
        "test") test_setup ;;
        *)
            echo "Usage: $0 [setup|start|stop|logs|clean|test]"
            echo "Run without arguments for interactive menu"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"