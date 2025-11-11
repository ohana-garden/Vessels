#!/bin/bash
# Shoghi Platform Deployment Script

set -e

echo "🌺 SHOGHI PLATFORM DEPLOYMENT"
echo "=============================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed."
        exit 1
    fi
    
    # Check pip
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed."
        exit 1
    fi
    
    # Check if Docker is available (optional)
    if command -v docker &> /dev/null; then
        print_success "Docker found - container deployment available"
        DOCKER_AVAILABLE=true
    else
        print_warning "Docker not found - local deployment only"
        DOCKER_AVAILABLE=false
    fi
    
    print_success "Prerequisites check complete"
}

# Setup Python environment
setup_python_env() {
    print_status "Setting up Python environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    print_status "Installing Python dependencies..."
    pip install -r requirements.txt
    
    print_success "Python environment setup complete"
}

# Test platform components
test_platform() {
    print_status "Testing platform components..."
    
    # Test basic import
    print_status "Testing core module imports..."
    python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from agent_zero_core import agent_zero
    from dynamic_agent_factory import agent_factory
    from community_memory import community_memory
    from grant_coordination_system import grant_system
    from adaptive_tools import adaptive_tools
    from shoghi_interface import shoghi_interface
    from auto_deploy import auto_deploy
    from universal_connector import universal_connector
    print('✅ All core modules imported successfully')
except Exception as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)
"
    
    print_success "Platform components test complete"
}

# Deploy based on mode
deploy_platform() {
    local mode=${1:-"development"}
    
    print_status "Deploying Shoghi Platform in $mode mode..."
    
    case $mode in
        "development")
            deploy_development
            ;;
        "production")
            deploy_production
            ;;
        "deployed")
            deploy_deployed
            ;;
        *)
            print_error "Unknown deployment mode: $mode"
            print_status "Available modes: development, production, deployed"
            exit 1
            ;;
    esac
}

# Development deployment
deploy_development() {
    print_status "Starting Shoghi Platform in development mode..."
    
    # Run the platform
    print_status "Starting interactive mode..."
    python3 shoghi.py --mode development
}

# Production deployment
deploy_production() {
    print_status "Starting Shoghi Platform in production mode..."
    
    # Check if we should use Docker
    if [ "$DOCKER_AVAILABLE" = true ]; then
        print_status "Building Docker containers..."
        docker-compose build
        
        print_status "Starting services..."
        docker-compose up -d
        
        print_status "Waiting for services to be ready..."
        sleep 30
        
        # Health check
        print_status "Performing health check..."
        if curl -f http://localhost:8080/health >/dev/null 2>&1; then
            print_success "Shoghi Platform is healthy and ready!"
            print_status "Platform available at: http://localhost:8080"
        else
            print_warning "Health check failed - checking logs..."
            docker-compose logs --tail=50
        fi
    else
        print_status "Starting in local production mode..."
        nohup python3 shoghi.py --mode production > shoghi.log 2>&1 &
        SHOGHI_PID=$!
        echo $SHOGHI_PID > shoghi.pid
        print_success "Shoghi Platform started (PID: $SHOGHI_PID)"
    fi
}

# Deployed deployment (cloud/edge)
deploy_deployed() {
    print_status "Deploying Shoghi Platform to cloud/edge..."
    
    if [ "$DOCKER_AVAILABLE" = false ]; then
        print_error "Docker is required for deployed mode"
        exit 1
    fi
    
    # Use the auto-deploy system
    python3 -c "
from auto_deploy import deploy_shoghi_platform
print('🚀 Deploying Shoghi Platform...')
deployment_id = deploy_shoghi_platform('cloud')
print(f'✅ Deployment complete: {deployment_id}')
"
}

# Show platform status
show_status() {
    print_status "Checking Shoghi Platform status..."
    
    if [ -f "shoghi.pid" ]; then
        local pid=$(cat shoghi.pid)
        if ps -p $pid > /dev/null 2>&1; then
            print_success "Shoghi Platform is running (PID: $pid)"
        else
            print_warning "Shoghi Platform is not running (stale PID file)"
            rm -f shoghi.pid
        fi
    else
        print_warning "Shoghi Platform is not running"
    fi
    
    # Show detailed status if platform is available
    if python3 -c "import sys; sys.path.insert(0, '.'); from shoghi import ShoghiPlatform; print('Platform available')" 2>/dev/null; then
        print_status "Detailed platform status:"
        python3 shoghi.py --status
    fi
}

# Stop platform
stop_platform() {
    print_status "Stopping Shoghi Platform..."
    
    if [ -f "shoghi.pid" ]; then
        local pid=$(cat shoghi.pid)
        if ps -p $pid > /dev/null 2>&1; then
            print_status "Stopping process (PID: $pid)..."
            kill $pid
            rm -f shoghi.pid
            print_success "Shoghi Platform stopped"
        else
            print_warning "Process not found (stale PID file)"
            rm -f shoghi.pid
        fi
    else
        print_warning "No PID file found - platform may not be running"
    fi
    
    # Stop Docker containers if they exist
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f "docker-compose.yml" ]; then
        print_status "Stopping Docker containers..."
        docker-compose down
        print_success "Docker containers stopped"
    fi
}

# Show logs
show_logs() {
    if [ -f "shoghi.log" ]; then
        print_status "Recent logs:"
        tail -50 shoghi.log
    else
        print_warning "No log file found"
    fi
    
    # Show Docker logs if available
    if [ "$DOCKER_AVAILABLE" = true ] && [ -f "docker-compose.yml" ]; then
        print_status "Docker logs:"
        docker-compose logs --tail=20
    fi
}

# Clean up
cleanup() {
    print_status "Cleaning up..."
    
    # Remove temporary files
    rm -f shoghi.pid
    rm -f shoghi.log
    
    # Clean Python cache
    find . -type f -name "*.pyc" -delete
    find . -type d -name "__pycache__" -delete
    
    # Clean Docker containers and images if requested
    if [ "$1" = "--docker" ] && [ "$DOCKER_AVAILABLE" = true ]; then
        print_status "Cleaning Docker resources..."
        docker system prune -f
    fi
    
    print_success "Cleanup complete"
}

# Show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --mode MODE        Deployment mode (development, production, deployed)"
    echo "  --status           Show platform status"
    echo "  --stop             Stop the platform"
    echo "  --logs             Show platform logs"
    echo "  --cleanup          Clean up temporary files"
    echo "  --cleanup --docker Clean up including Docker resources"
    echo "  --help             Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --mode development    # Start in interactive development mode"
    echo "  $0 --mode production     # Start in production mode"
    echo "  $0 --status              # Check platform status"
    echo "  $0 --stop                # Stop the platform"
    echo "  $0 --logs                # Show recent logs"
}

# Main execution
main() {
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            --mode)
                MODE="$2"
                shift 2
                ;;
            --status)
                ACTION="status"
                shift
                ;;
            --stop)
                ACTION="stop"
                shift
                ;;
            --logs)
                ACTION="logs"
                shift
                ;;
            --cleanup)
                ACTION="cleanup"
                shift
                if [[ $# -gt 0 && $1 == "--docker" ]]; then
                    CLEANUP_DOCKER=true
                    shift
                fi
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                show_usage
                exit 1
                ;;
        esac
    done
    
    # Default action
    if [ -z "$ACTION" ]; then
        ACTION="deploy"
    fi
    
    # Execute action
    case $ACTION in
        "deploy")
            check_prerequisites
            setup_python_env
            test_platform
            deploy_platform ${MODE:-"development"}
            ;;
        "status")
            show_status
            ;;
        "stop")
            stop_platform
            ;;
        "logs")
            show_logs
            ;;
        "cleanup")
            cleanup ${CLEANUP_DOCKER:+--docker}
            ;;
    esac
}

# Run main function
main "$@"