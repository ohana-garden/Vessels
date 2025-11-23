# FFmpeg Library Fix

## Issue
CI/CD pipeline failed because the Python `av` package requires FFmpeg development libraries to build.

## Error
```
ERROR: Failed building wheel for av
The system cannot find the path specified: 'avformat'
```

## Root Cause
The `av` package (PyAV) is a Pythonic binding for FFmpeg's libraries. It requires:
- **Build time**: FFmpeg development libraries (`-dev` packages)
- **Runtime**: FFmpeg shared libraries

These were missing from the CI environment and Docker images.

## Fixes Applied

### 1. GitHub Actions CI/CD Workflow
**File**: `.github/workflows/ci.yml`

Added FFmpeg installation step to **all 3 jobs** that install Python dependencies:
- `lint` job
- `type-check` job
- `test` job

```yaml
- name: Install FFmpeg libraries
  run: sudo apt-get update && sudo apt-get install -y ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev
```

This runs **before** the `pip install` step in each job.

### 2. Docker Build
**File**: `Dockerfile.optimized`

#### Builder Stage (for compiling Python packages)
Added development libraries:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    ffmpeg \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libavfilter-dev \
    libswscale-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*
```

#### Runtime Stage (for running the application)
Added shared libraries:
```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    redis-tools \
    curl \
    ffmpeg \
    libavformat58 \
    libavcodec58 \
    libavdevice58 \
    libavutil56 \
    libavfilter7 \
    libswscale5 \
    libswresample3 \
    && rm -rf /var/lib/apt/lists/*
```

**Note**: Runtime stage uses numbered library packages (e.g., `libavformat58`) which are the shared libraries without development headers.

## FFmpeg Libraries Explained

| Library | Purpose |
|---------|---------|
| **avformat** | Container format muxing/demuxing |
| **avcodec** | Audio/video codec encoding/decoding |
| **avdevice** | Device input/output |
| **avutil** | Utility functions |
| **avfilter** | Audio/video filtering |
| **swscale** | Image scaling/color conversion |
| **swresample** | Audio resampling |

## Why is `av` Package Needed?

The `av` package is likely used for:
- **Voice interface**: Processing audio input (Whisper STT)
- **TTS output**: Audio synthesis
- **Video processing**: If processing video content
- **Media streaming**: Real-time audio/video handling

It's a dependency of the Vessels voice interface and TEN Framework integration.

## Verification

### CI/CD Pipeline
The workflow will now:
1. ✅ Install FFmpeg libraries
2. ✅ Install Python dependencies (including `av`)
3. ✅ Run tests that use audio/video processing

### Docker Build
```bash
# Build the image
docker build -f Dockerfile.optimized -t vessels:latest .

# Verify FFmpeg is available
docker run --rm vessels:latest ffmpeg -version

# Verify Python av package
docker run --rm vessels:latest python -c "import av; print(av.__version__)"
```

### Local Development
If running locally without Docker:
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg libavformat-dev libavcodec-dev libavdevice-dev libavutil-dev libavfilter-dev libswscale-dev libswresample-dev

# macOS
brew install ffmpeg

# Then install Python packages
pip install -r requirements-fixed.txt
```

## Commits
1. **ddbe607** - Fix CI: Add FFmpeg libraries installation (CI/CD workflow)
2. **75dd514** - Add FFmpeg libraries to Docker build (Dockerfile)

## Status
✅ **FIXED** - Both CI/CD and Docker builds now include FFmpeg libraries.

The pipeline should now successfully install all dependencies and run tests.
