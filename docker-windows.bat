@echo off
REM ============================================================================
REM Vessels Platform - Windows Docker Desktop Launcher
REM ============================================================================

echo.
echo ================================================
echo   VESSELS - Single Container Deployment
echo   Windows Docker Desktop
echo ================================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo Docker is running...
echo.

REM Parse command
set COMMAND=%1
if "%COMMAND%"=="" set COMMAND=run

if "%COMMAND%"=="build" goto build
if "%COMMAND%"=="run" goto run
if "%COMMAND%"=="stop" goto stop
if "%COMMAND%"=="logs" goto logs
if "%COMMAND%"=="shell" goto shell
if "%COMMAND%"=="clean" goto clean

echo Unknown command: %COMMAND%
echo.
echo Usage: docker-windows.bat [build^|run^|stop^|logs^|shell^|clean]
echo.
echo   build  - Build the Vessels Docker image
echo   run    - Run Vessels container (default)
echo   stop   - Stop the Vessels container
echo   logs   - Show container logs
echo   shell  - Open shell in running container
echo   clean  - Remove container and image
echo.
pause
exit /b 1

:build
echo Building Vessels Docker image...
echo This may take several minutes on first build...
echo.
docker build -t vessels:latest .
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)
echo.
echo ✓ Build complete!
echo.
echo Next step: Run with "docker-windows.bat run"
echo.
pause
exit /b 0

:run
echo Checking for existing container...
docker ps -a --filter "name=vessels-platform" --format "{{.Names}}" | findstr "vessels-platform" >nul
if %errorlevel% equ 0 (
    echo Stopping existing container...
    docker stop vessels-platform >nul 2>&1
    docker rm vessels-platform >nul 2>&1
)

echo Starting Vessels Platform...
echo.

docker run -d ^
    --name vessels-platform ^
    -p 5000:5000 ^
    -p 6379:6379 ^
    -v vessels-data:/data/falkordb ^
    -v vessels-workdir:/app/work_dir ^
    --restart unless-stopped ^
    vessels:latest

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to start container!
    echo.
    echo Did you build the image first?
    echo Run: docker-windows.bat build
    echo.
    pause
    exit /b 1
)

echo.
echo ✓ Vessels Platform is starting...
echo.
echo Waiting for services to be ready...
timeout /t 5 >nul

echo.
echo ================================================
echo   VESSELS PLATFORM IS RUNNING
echo ================================================
echo.
echo Web Interface: http://localhost:5000
echo FalkorDB:      localhost:6379
echo.
echo Container name: vessels-platform
echo.
echo Useful commands:
echo   docker-windows.bat logs   - View logs
echo   docker-windows.bat shell  - Open shell
echo   docker-windows.bat stop   - Stop container
echo.
pause
exit /b 0

:stop
echo Stopping Vessels Platform...
docker stop vessels-platform
docker rm vessels-platform
echo.
echo ✓ Container stopped and removed
echo.
pause
exit /b 0

:logs
echo Showing Vessels logs (Ctrl+C to exit)...
echo.
docker logs -f vessels-platform
exit /b 0

:shell
echo Opening shell in Vessels container...
echo.
docker exec -it vessels-platform /bin/bash
exit /b 0

:clean
echo This will remove the Vessels container and image.
echo Data volumes will be preserved.
echo.
set /p CONFIRM="Are you sure? (yes/no): "
if not "%CONFIRM%"=="yes" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Removing container...
docker stop vessels-platform >nul 2>&1
docker rm vessels-platform >nul 2>&1

echo Removing image...
docker rmi vessels:latest

echo.
echo ✓ Cleanup complete
echo.
echo To remove data volumes as well, run:
echo   docker volume rm vessels-data vessels-workdir
echo.
pause
exit /b 0
