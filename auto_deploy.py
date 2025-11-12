#!/usr/bin/env python3
"""
AUTO DEPLOY SYSTEM
Self-deploying infrastructure that:
- Containerizes everything automatically
- Deploys to cloud/edge as needed
- Scales based on demand
- Includes monitoring, logging, self-healing

SECURITY NOTE: This system requires careful input validation and sanitization.
All user-provided configuration values must be validated before being used in
shell commands, Dockerfiles, or docker-compose configurations.
"""

import json
import logging
import subprocess
import threading
import time
import os
import sys
import shutil
import re
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import uuid
import tempfile
import docker
import requests

logger = logging.getLogger(__name__)


def sanitize_env_var_name(name: str) -> str:
    """
    Sanitize environment variable name to prevent injection.
    Only allows alphanumeric characters and underscores.
    """
    if not re.match(r'^[A-Z_][A-Z0-9_]*$', name):
        raise ValueError(f"Invalid environment variable name: {name}")
    return name


def sanitize_env_var_value(value: str) -> str:
    """
    Sanitize environment variable value to prevent injection.
    Removes potentially dangerous characters and validates format.
    """
    # Check for shell metacharacters and control characters
    dangerous_chars = ['$', '`', '\\', '\n', '\r', ';', '|', '&', '<', '>']
    if any(char in str(value) for char in dangerous_chars):
        raise ValueError(f"Environment variable value contains dangerous characters: {value}")

    # Limit length to prevent resource exhaustion
    if len(str(value)) > 1000:
        raise ValueError(f"Environment variable value too long: {len(value)} characters")

    return str(value)


def sanitize_port_number(port: Any) -> int:
    """
    Validate and sanitize port numbers.
    """
    try:
        port_num = int(port)
        if not (1 <= port_num <= 65535):
            raise ValueError(f"Port number out of range: {port_num}")
        return port_num
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid port number: {port}") from e


def sanitize_resource_value(value: str, resource_type: str) -> str:
    """
    Validate resource specifications (CPU, memory, storage).
    """
    if resource_type in ["cpu", "replicas"]:
        # CPU and replicas should be numeric
        try:
            num = float(value) if resource_type == "cpu" else int(value)
            if num <= 0 or num > 1000:
                raise ValueError(f"Invalid {resource_type} value: {value}")
            return str(value)
        except ValueError as e:
            raise ValueError(f"Invalid {resource_type} format: {value}") from e

    elif resource_type in ["memory", "storage"]:
        # Memory and storage should match pattern like "4Gi", "8GB"
        if not re.match(r'^\d+[KMGT]i?$', value):
            raise ValueError(f"Invalid {resource_type} format: {value}")
        return value

    else:
        raise ValueError(f"Unknown resource type: {resource_type}")


def sanitize_image_name(name: str) -> str:
    """
    Validate Docker image names to prevent injection.
    """
    # Docker image names can contain lowercase letters, digits, and separators
    if not re.match(r'^[a-z0-9][a-z0-9_.-]*$', name):
        raise ValueError(f"Invalid image name: {name}")
    if len(name) > 255:
        raise ValueError(f"Image name too long: {name}")
    return name


class DeploymentType(Enum):
    LOCAL = "local"
    CLOUD = "cloud"
    EDGE = "edge"
    HYBRID = "hybrid"

class DeploymentStatus(Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYING = "deploying"
    RUNNING = "running"
    SCALING = "scaling"
    ERROR = "error"
    STOPPED = "stopped"

@dataclass
class DeploymentConfig:
    """Deployment configuration"""
    name: str
    deployment_type: DeploymentType
    resources: Dict[str, Any]
    scaling: Dict[str, Any]
    monitoring: Dict[str, Any]
    environment: Dict[str, str]
    dependencies: List[str]

@dataclass
class DeploymentInstance:
    """Active deployment instance"""
    id: str
    config: DeploymentConfig
    status: DeploymentStatus
    created_at: datetime
    containers: List[str] = field(default_factory=list)
    endpoints: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

class AutoDeploySystem:
    """Self-deploying infrastructure system"""
    
    def __init__(self):
        self.deployments: Dict[str, DeploymentInstance] = {}
        self.deployment_configs: Dict[str, DeploymentConfig] = {}
        self.monitoring_thread = None
        self.scaling_thread = None
        self.health_check_thread = None
        self.running = False
        self.docker_client = None
        
        self.initialize_deployment_system()
    
    def initialize_deployment_system(self):
        """Initialize the auto-deploy system"""
        self.running = True
        
        # Initialize Docker client
        try:
            self.docker_client = docker.from_env()
            logger.info("Docker client initialized")
        except Exception as e:
            logger.warning(f"Docker not available: {e}")
            self.docker_client = None
        
        # Start monitoring threads
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop)
        self.scaling_thread = threading.Thread(target=self._scaling_loop)
        self.health_check_thread = threading.Thread(target=self._health_check_loop)
        
        self.monitoring_thread.daemon = True
        self.scaling_thread.daemon = True
        self.health_check_thread.daemon = True
        
        self.monitoring_thread.start()
        self.scaling_thread.start()
        self.health_check_thread.start()
        
        logger.info("Auto Deploy System initialized")
    
    def create_deployment_config(self, name: str, deployment_type: DeploymentType,
                               resources: Dict[str, Any] = None,
                               scaling: Dict[str, Any] = None,
                               monitoring: Dict[str, Any] = None,
                               environment: Dict[str, str] = None,
                               dependencies: List[str] = None) -> str:
        """Create deployment configuration"""
        
        # Default configurations
        if resources is None:
            resources = {
                "cpu": "2",
                "memory": "4Gi",
                "storage": "10Gi",
                "replicas": 1
            }
        
        if scaling is None:
            scaling = {
                "min_replicas": 1,
                "max_replicas": 5,
                "cpu_threshold": 70,
                "memory_threshold": 80,
                "scale_up_policy": "immediate",
                "scale_down_policy": "gradual"
            }
        
        if monitoring is None:
            monitoring = {
                "enabled": True,
                "metrics_port": 8080,
                "health_check_path": "/health",
                "log_level": "INFO",
                "alerting": True
            }
        
        if environment is None:
            environment = {
                "PYTHONPATH": "/app",
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "production"
            }
        
        if dependencies is None:
            dependencies = ["python:3.9", "redis", "postgresql"]
        
        config = DeploymentConfig(
            name=name,
            deployment_type=deployment_type,
            resources=resources,
            scaling=scaling,
            monitoring=monitoring,
            environment=environment,
            dependencies=dependencies
        )
        
        config_id = str(uuid.uuid4())
        self.deployment_configs[config_id] = config
        
        logger.info(f"Created deployment config: {name} ({config_id})")
        return config_id
    
    def deploy_shoghi_platform(self, deployment_type: DeploymentType = DeploymentType.LOCAL) -> str:
        """Deploy the complete Shoghi platform"""
        
        # Create deployment configuration
        config_id = self.create_deployment_config(
            name="shoghi-platform",
            deployment_type=deployment_type,
            resources={
                "cpu": "4",
                "memory": "8Gi", 
                "storage": "20Gi",
                "replicas": 2
            },
            scaling={
                "min_replicas": 2,
                "max_replicas": 10,
                "cpu_threshold": 60,
                "memory_threshold": 75
            },
            monitoring={
                "enabled": True,
                "metrics_port": 8080,
                "health_check_path": "/health",
                "log_level": "INFO",
                "alerting": True
            },
            environment={
                "PYTHONPATH": "/app",
                "LOG_LEVEL": "INFO",
                "ENVIRONMENT": "production",
                "SHOGHI_MODE": "full_platform"
            },
            dependencies=["python:3.9", "redis", "postgresql", "nginx"]
        )
        
        # Deploy the platform
        deployment_id = self.deploy_application(config_id)
        
        logger.info(f"Deployed Shoghi platform: {deployment_id}")
        return deployment_id
    
    def deploy_application(self, config_id: str) -> str:
        """Deploy application using configuration"""
        
        if config_id not in self.deployment_configs:
            raise ValueError(f"Configuration {config_id} not found")
        
        config = self.deployment_configs[config_id]
        deployment_id = str(uuid.uuid4())
        
        # Create deployment instance
        deployment = DeploymentInstance(
            id=deployment_id,
            config=config,
            status=DeploymentStatus.BUILDING,
            created_at=datetime.now()
        )
        
        self.deployments[deployment_id] = deployment
        
        # Start deployment process
        deployment_thread = threading.Thread(
            target=self._deploy_process,
            args=(deployment_id,)
        )
        deployment_thread.daemon = True
        deployment_thread.start()
        
        return deployment_id
    
    def _deploy_process(self, deployment_id: str):
        """Deployment process for an application"""
        deployment = self.deployments[deployment_id]
        
        try:
            logger.info(f"Starting deployment: {deployment_id}")
            
            # Step 1: Generate Dockerfile
            dockerfile_content = self._generate_dockerfile(deployment.config)
            
            # Step 2: Create deployment package
            package_path = self._create_deployment_package(deployment.config, dockerfile_content)
            
            # Step 3: Build container
            if self.docker_client:
                deployment.status = DeploymentStatus.BUILDING
                image = self._build_container(package_path, deployment.config.name)
                deployment.containers.append(f"{deployment.config.name}:latest")
            
            # Step 4: Deploy container
            deployment.status = DeploymentStatus.DEPLOYING
            if self.docker_client:
                container = self._run_container(deployment.config)
                deployment.containers.append(container.id)
            
            # Step 5: Setup monitoring
            self._setup_monitoring(deployment)
            
            # Step 6: Configure networking
            endpoints = self._configure_networking(deployment)
            deployment.endpoints = endpoints
            
            # Deployment complete
            deployment.status = DeploymentStatus.RUNNING
            logger.info(f"Deployment completed: {deployment_id}")
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            deployment.status = DeploymentStatus.ERROR
            deployment.metrics["error"] = str(e)
    
    def _generate_dockerfile(self, config: DeploymentConfig) -> str:
        """
        Generate Dockerfile for deployment with proper input validation.

        Raises:
            ValueError: If configuration values fail validation
        """
        # Validate port number
        try:
            metrics_port = sanitize_port_number(config.monitoring['metrics_port'])
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid metrics port in config: {e}")
            raise ValueError(f"Invalid metrics port configuration") from e

        # Validate health check path (basic validation)
        health_check_path = config.monitoring.get('health_check_path', '/health')
        if not re.match(r'^/[a-zA-Z0-9/_-]*$', health_check_path):
            raise ValueError(f"Invalid health check path: {health_check_path}")

        dockerfile = f"""FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

"""

        # Add environment variables with validation
        dockerfile += "# Set environment variables\n"
        for key, value in config.environment.items():
            try:
                safe_key = sanitize_env_var_name(key)
                safe_value = sanitize_env_var_value(value)
                dockerfile += f"ENV {safe_key}={safe_value}\n"
            except ValueError as e:
                logger.warning(f"Skipping invalid environment variable {key}: {e}")
                # Continue with other variables instead of failing completely
                continue

        dockerfile += f"""
# Expose port
EXPOSE {metrics_port}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:{metrics_port}{health_check_path} || exit 1

# Start application
CMD ["python", "shoghi.py", "--mode", "deployed"]
"""

        return dockerfile
    
    def _create_deployment_package(self, config: DeploymentConfig, dockerfile_content: str) -> str:
        """Create deployment package with all necessary files"""
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix="shoghi_deploy_")
        
        # Write Dockerfile
        dockerfile_path = os.path.join(temp_dir, "Dockerfile")
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile_content)
        
        # Write docker-compose.yml
        compose_content = self._generate_docker_compose(config)
        compose_path = os.path.join(temp_dir, "docker-compose.yml")
        with open(compose_path, 'w') as f:
            f.write(compose_content)
        
        # Copy application files (pass config for nginx generation)
        self._copy_application_files(temp_dir, config)

        # Create deployment script
        deploy_script = self._generate_deploy_script(config)
        script_path = os.path.join(temp_dir, "deploy.sh")
        with open(script_path, 'w') as f:
            f.write(deploy_script)
        os.chmod(script_path, 0o755)
        
        return temp_dir
    
    def _generate_docker_compose(self, config: DeploymentConfig) -> str:
        """
        Generate docker-compose configuration with proper input validation.

        Raises:
            ValueError: If configuration values fail validation
        """
        # Validate configuration values
        try:
            metrics_port = sanitize_port_number(config.monitoring['metrics_port'])
            replicas = int(sanitize_resource_value(str(config.resources['replicas']), 'replicas'))
            cpu = sanitize_resource_value(str(config.resources['cpu']), 'cpu')
            memory = sanitize_resource_value(config.resources['memory'], 'memory')
        except (KeyError, ValueError) as e:
            logger.error(f"Invalid resource configuration: {e}")
            raise ValueError(f"Invalid docker-compose configuration") from e

        compose = f"""version: '3.8'

services:
  shoghi-core:
    build: .
    ports:
      - "{metrics_port}:{metrics_port}"
    environment:
"""

        # Add environment variables with validation
        for key, value in config.environment.items():
            try:
                safe_key = sanitize_env_var_name(key)
                safe_value = sanitize_env_var_value(value)
                compose += f"      - {safe_key}={safe_value}\n"
            except ValueError as e:
                logger.warning(f"Skipping invalid environment variable {key}: {e}")
                continue

        compose += f"""    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    deploy:
      replicas: {replicas}
      resources:
        limits:
          cpus: '{cpu}'
          memory: {memory}

  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: shoghi
      POSTGRES_USER: shoghi
      POSTGRES_PASSWORD: shoghi123
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - shoghi-core
    restart: unless-stopped

volumes:
  postgres_data:
"""

        return compose
    
    def _copy_application_files(self, dest_dir: str, config: DeploymentConfig):
        """Copy application files to deployment directory"""
        # Get the current directory (where this script is located)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Copy Python files
        python_files = [
            "shoghi.py",
            "agent_zero_core.py",
            "dynamic_agent_factory.py", 
            "community_memory.py",
            "grant_coordination_system.py",
            "adaptive_tools.py",
            "shoghi_interface.py",
            "universal_connector.py",
            "auto_deploy.py"
        ]
        
        for file in python_files:
            src_path = os.path.join(current_dir, file)
            if os.path.exists(src_path):
                shutil.copy2(src_path, dest_dir)
        
        # Create requirements.txt
        requirements_content = f"""
# Core dependencies
python-dateutil>=2.8.0
requests>=2.26.0
beautifulsoup4>=4.9.0
flask>=2.0.0
jinja2>=3.0.0
pandas>=1.3.0
numpy>=1.21.0
redis>=3.5.0
psycopg2-binary>=2.9.0

# Optional dependencies for enhanced functionality
matplotlib>=3.4.0
seaborn>=0.11.0
docker>=5.0.0

# Development dependencies
pytest>=6.2.0
pytest-cov>=2.12.0
black>=21.0.0
flake8>=3.9.0
"""
        
        req_path = os.path.join(dest_dir, "requirements.txt")
        with open(req_path, 'w') as f:
            f.write(requirements_content)
        
        # Create main entry point
        main_py_content = f"""
#!/usr/bin/env python3
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from shoghi import ShoghiPlatform

def main():
    platform = ShoghiPlatform()
    platform.start()

if __name__ == "__main__":
    main()
"""
        
        main_path = os.path.join(dest_dir, "main.py")
        with open(main_path, 'w') as f:
            f.write(main_py_content)
        
        # Create nginx configuration with validated port
        try:
            metrics_port = sanitize_port_number(config.monitoring['metrics_port'])
        except (KeyError, ValueError) as e:
            logger.warning(f"Invalid metrics port for nginx config, using default 8080: {e}")
            metrics_port = 8080

        nginx_conf = f"""events {{
    worker_connections 1024;
}}

http {{
    upstream shoghi {{
        server shoghi-core:{metrics_port};
    }}

    server {{
        listen 80;
        server_name localhost;

        location / {{
            proxy_pass http://shoghi;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }}

        location /health {{
            proxy_pass http://shoghi/health;
        }}
    }}
}}
"""

        nginx_path = os.path.join(dest_dir, "nginx.conf")
        with open(nginx_path, 'w') as f:
            f.write(nginx_conf)
    
    def _generate_deploy_script(self, config: DeploymentConfig) -> str:
        """Generate deployment script"""
        script = f"""#!/bin/bash
# Shoghi Platform Deployment Script

set -e

echo "🚀 Starting Shoghi Platform deployment..."

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || {{ echo "Docker is required but not installed. Aborting." >&2; exit 1; }}
command -v docker-compose >/dev/null 2>&1 || {{ echo "Docker Compose is required but not installed. Aborting." >&2; exit 1; }}

# Build and deploy
echo "Building containers..."
docker-compose build

echo "Starting services..."
docker-compose up -d

echo "Waiting for services to be ready..."
sleep 30

# Health check
echo "Performing health check..."
for i in {{1..30}}; do
    if curl -f http://localhost:{config.monitoring['metrics_port']}{config.monitoring['health_check_path']} >/dev/null 2>&1; then
        echo "✅ Shoghi Platform is healthy and ready!"
        break
    fi
    echo "Waiting for platform to be ready... ($i/30)"
    sleep 10
done

echo "🎉 Deployment complete!"
echo "Platform available at: http://localhost:{config.monitoring['metrics_port']}"
echo "Health check: http://localhost:{config.monitoring['metrics_port']}{config.monitoring['health_check_path']}"

# Show logs
echo "Recent logs:"
docker-compose logs --tail=20 shoghi-core
"""
        
        return script
    
    def _build_container(self, package_path: str, image_name: str) -> str:
        """Build Docker container"""
        if not self.docker_client:
            raise RuntimeError("Docker client not available")
        
        try:
            # Build image
            image, logs = self.docker_client.images.build(
                path=package_path,
                tag=f"{image_name}:latest",
                rm=True
            )
            
            for log in logs:
                if 'stream' in log:
                    logger.info(log['stream'].strip())
            
            return image.id
            
        except Exception as e:
            logger.error(f"Container build failed: {e}")
            raise
    
    def _run_container(self, config: DeploymentConfig) -> docker.models.containers.Container:
        """Run Docker container"""
        if not self.docker_client:
            raise RuntimeError("Docker client not available")
        
        try:
            # Run container
            container = self.docker_client.containers.run(
                image=f"{config.name}:latest",
                name=f"{config.name}-{int(time.time())}",
                ports={
                    f"{config.monitoring['metrics_port']}/tcp": config.monitoring['metrics_port']
                },
                environment=config.environment,
                restart_policy={"Name": "unless-stopped"},
                detach=True
            )
            
            return container
            
        except Exception as e:
            logger.error(f"Container run failed: {e}")
            raise
    
    def _setup_monitoring(self, deployment: DeploymentInstance):
        """Setup monitoring for deployment"""
        if not deployment.config.monitoring["enabled"]:
            return
        
        # Setup metrics collection
        deployment.metrics = {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "request_count": 0,
            "error_count": 0,
            "uptime": 0,
            "last_updated": datetime.now()
        }
    
    def _configure_networking(self, deployment: DeploymentInstance) -> List[str]:
        """Configure networking for deployment"""
        endpoints = []
        
        # Main application endpoint
        endpoints.append(f"http://localhost:{deployment.config.monitoring['metrics_port']}")
        
        # Health check endpoint
        endpoints.append(f"http://localhost:{deployment.config.monitoring['metrics_port']}{deployment.config.monitoring['health_check_path']}")
        
        return endpoints
    
    def scale_deployment(self, deployment_id: str, replicas: int) -> bool:
        """Scale deployment to specified number of replicas"""
        if deployment_id not in self.deployments:
            return False
        
        deployment = self.deployments[deployment_id]
        
        try:
            deployment.status = DeploymentStatus.SCALING
            
            if self.docker_client:
                # Scale using docker-compose
                compose_file = self._find_compose_file(deployment_id)
                if compose_file:
                    result = subprocess.run(
                        ["docker-compose", "-f", compose_file, "up", "-d", "--scale", f"shoghi-core={replicas}"],
                        capture_output=True,
                        text=True
                    )
                    
                    if result.returncode == 0:
                        deployment.config.resources["replicas"] = replicas
                        deployment.status = DeploymentStatus.RUNNING
                        logger.info(f"Scaled deployment {deployment_id} to {replicas} replicas")
                        return True
            
            deployment.status = DeploymentStatus.ERROR
            return False
            
        except Exception as e:
            logger.error(f"Scaling failed: {e}")
            deployment.status = DeploymentStatus.ERROR
            return False
    
    def get_deployment_status(self, deployment_id: str) -> Optional[Dict[str, Any]]:
        """Get deployment status"""
        if deployment_id not in self.deployments:
            return None
        
        deployment = self.deployments[deployment_id]
        
        return {
            "id": deployment.id,
            "name": deployment.config.name,
            "status": deployment.status.value,
            "created_at": deployment.created_at.isoformat(),
            "containers": deployment.containers,
            "endpoints": deployment.endpoints,
            "metrics": deployment.metrics,
            "uptime": (datetime.now() - deployment.created_at).total_seconds()
        }
    
    def get_all_deployments(self) -> List[Dict[str, Any]]:
        """Get all deployments"""
        return [self.get_deployment_status(deployment_id) for deployment_id in self.deployments]
    
    def stop_deployment(self, deployment_id: str) -> bool:
        """Stop deployment"""
        if deployment_id not in self.deployments:
            return False
        
        deployment = self.deployments[deployment_id]
        
        try:
            if self.docker_client:
                # Stop containers
                for container_id in deployment.containers:
                    try:
                        container = self.docker_client.containers.get(container_id)
                        container.stop()
                        container.remove()
                    except:
                        pass
            
            deployment.status = DeploymentStatus.STOPPED
            logger.info(f"Stopped deployment: {deployment_id}")
            return True
            
        except Exception as e:
            logger.error(f"Stop deployment failed: {e}")
            return False
    
    def _find_compose_file(self, deployment_id: str) -> Optional[str]:
        """Find docker-compose file for deployment"""
        # This would search for the deployment package
        # For now, return None and use direct Docker commands
        return None
    
    def _monitoring_loop(self):
        """Monitor deployments"""
        while self.running:
            try:
                for deployment in self.deployments.values():
                    if deployment.status == DeploymentStatus.RUNNING:
                        self._collect_metrics(deployment)
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
            
            time.sleep(60)  # Monitor every minute
    
    def _scaling_loop(self):
        """Auto-scaling loop"""
        while self.running:
            try:
                for deployment in self.deployments.values():
                    if deployment.status == DeploymentStatus.RUNNING:
                        self._check_scaling_needs(deployment)
                
            except Exception as e:
                logger.error(f"Scaling error: {e}")
            
            time.sleep(300)  # Check scaling every 5 minutes
    
    def _health_check_loop(self):
        """Health check loop"""
        while self.running:
            try:
                for deployment in self.deployments.values():
                    if deployment.status == DeploymentStatus.RUNNING:
                        self._perform_health_check(deployment)
                
            except Exception as e:
                logger.error(f"Health check error: {e}")
            
            time.sleep(30)  # Health check every 30 seconds
    
    def _collect_metrics(self, deployment: DeploymentInstance):
        """Collect metrics for deployment"""
        try:
            if self.docker_client and deployment.containers:
                # Get container stats
                for container_id in deployment.containers:
                    try:
                        container = self.docker_client.containers.get(container_id)
                        stats = container.stats(stream=False)
                        
                        # Calculate CPU usage
                        cpu_delta = stats['cpu_stats']['cpu_usage']['total_usage'] - \
                                   stats['precpu_stats']['cpu_usage']['total_usage']
                        system_delta = stats['cpu_stats']['system_cpu_usage'] - \
                                      stats['precpu_stats']['system_cpu_usage']
                        
                        if system_delta > 0:
                            cpu_usage = (cpu_delta / system_delta) * 100.0
                            deployment.metrics["cpu_usage"] = cpu_usage
                        
                        # Calculate memory usage
                        memory_usage = stats['memory_stats']['usage']
                        memory_limit = stats['memory_stats']['limit']
                        memory_percent = (memory_usage / memory_limit) * 100.0
                        deployment.metrics["memory_usage"] = memory_percent
                        
                        deployment.metrics["last_updated"] = datetime.now()
                        
                    except Exception as e:
                        logger.warning(f"Failed to collect metrics for {container_id}: {e}")
                
        except Exception as e:
            logger.error(f"Metrics collection error: {e}")
    
    def _check_scaling_needs(self, deployment: DeploymentInstance):
        """Check if scaling is needed"""
        try:
            metrics = deployment.metrics
            scaling_config = deployment.config.scaling
            
            if not metrics:
                return
            
            current_replicas = deployment.config.resources.get("replicas", 1)
            
            # Check scale up conditions
            if (metrics.get("cpu_usage", 0) > scaling_config["cpu_threshold"] or
                metrics.get("memory_usage", 0) > scaling_config["memory_threshold"]):
                
                if current_replicas < scaling_config["max_replicas"]:
                    logger.info(f"Scaling up {deployment.id} due to high resource usage")
                    self.scale_deployment(deployment.id, current_replicas + 1)
            
            # Check scale down conditions
            elif (metrics.get("cpu_usage", 0) < scaling_config["cpu_threshold"] * 0.5 and
                  metrics.get("memory_usage", 0) < scaling_config["memory_threshold"] * 0.5):
                
                if current_replicas > scaling_config["min_replicas"]:
                    logger.info(f"Scaling down {deployment.id} due to low resource usage")
                    self.scale_deployment(deployment.id, current_replicas - 1)
                
        except Exception as e:
            logger.error(f"Scaling check error: {e}")
    
    def _perform_health_check(self, deployment: DeploymentInstance):
        """Perform health check on deployment"""
        try:
            # Check if endpoints are responding
            for endpoint in deployment.endpoints:
                try:
                    response = requests.get(endpoint, timeout=5)
                    if response.status_code >= 400:
                        logger.warning(f"Health check failed for {endpoint}: {response.status_code}")
                except Exception as e:
                    logger.warning(f"Health check error for {endpoint}: {e}")
            
            # Update uptime
            deployment.metrics["uptime"] = (datetime.now() - deployment.created_at).total_seconds()
            
        except Exception as e:
            logger.error(f"Health check error: {e}")
    
    def generate_deployment_report(self) -> Dict[str, Any]:
        """Generate comprehensive deployment report"""
        report = {
            "report_time": datetime.now().isoformat(),
            "total_deployments": len(self.deployments),
            "active_deployments": len([d for d in self.deployments.values() if d.status == DeploymentStatus.RUNNING]),
            "deployment_summary": {},
            "resource_usage": {},
            "health_status": {},
            "recommendations": []
        }
        
        # Deployment summary by status
        for status in DeploymentStatus:
            count = len([d for d in self.deployments.values() if d.status == status])
            if count > 0:
                report["deployment_summary"][status.value] = count
        
        # Resource usage
        total_cpu = 0
        total_memory = 0
        for deployment in self.deployments.values():
            if deployment.status == DeploymentStatus.RUNNING:
                total_cpu += float(deployment.config.resources.get("cpu", 0))
                total_memory += float(deployment.config.resources.get("memory", "0").replace("Gi", ""))
        
        report["resource_usage"] = {
            "total_cpu_cores": total_cpu,
            "total_memory_gb": total_memory,
            "deployments": len([d for d in self.deployments.values() if d.status == DeploymentStatus.RUNNING])
        }
        
        # Health status
        healthy = len([d for d in self.deployments.values() if d.status == DeploymentStatus.RUNNING])
        total = len(self.deployments)
        report["health_status"] = {
            "healthy_deployments": healthy,
            "total_deployments": total,
            "health_percentage": (healthy / total * 100) if total > 0 else 0
        }
        
        # Recommendations
        if len(self.deployments) == 0:
            report["recommendations"].append({
                "type": "deployment",
                "message": "No deployments active. Consider deploying the Shoghi platform."
            })
        
        high_resource_deployments = [
            d for d in self.deployments.values() 
            if d.status == DeploymentStatus.RUNNING and d.metrics.get("cpu_usage", 0) > 80
        ]
        
        if len(high_resource_deployments) > 0:
            report["recommendations"].append({
                "type": "scaling",
                "message": f"{len(high_resource_deployments)} deployments showing high resource usage. Consider scaling up."
            })
        
        return report
    
    def shutdown(self):
        """
        Shutdown the deployment system gracefully.

        Stops all background threads and running deployments.
        """
        logger.info("Initiating Auto Deploy System shutdown...")
        self.running = False

        # Wait for threads to finish with timeout
        threads = [
            ("monitoring", self.monitoring_thread),
            ("scaling", self.scaling_thread),
            ("health_check", self.health_check_thread)
        ]

        for thread_name, thread in threads:
            if thread and thread.is_alive():
                logger.info(f"Waiting for {thread_name} thread to finish...")
                thread.join(timeout=10)
                if thread.is_alive():
                    logger.warning(f"{thread_name} thread did not finish within timeout")

        # Stop all deployments
        logger.info("Stopping all active deployments...")
        for deployment_id in list(self.deployments.keys()):
            try:
                self.stop_deployment(deployment_id)
            except Exception as e:
                logger.error(f"Error stopping deployment {deployment_id}: {e}")

        logger.info("Auto Deploy System shutdown complete")

# Global instance
auto_deploy = AutoDeploySystem()

def deploy_shoghi_platform(deployment_type: str = "local") -> str:
    """Deploy the complete Shoghi platform"""
    deployment_type_enum = DeploymentType(deployment_type)
    return auto_deploy.deploy_shoghi_platform(deployment_type_enum)