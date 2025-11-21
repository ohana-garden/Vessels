# Vessels Deployment Guide

Complete deployment guide for the Vessels stack with FalkorDB, Graphiti, Nostr, On-Device AI, and Petals integration.

## Table of Contents

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Deployment Modes](#deployment-modes)
6. [Testing](#testing)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### Minimal Setup (5 minutes)

```bash
# Clone repository
git clone https://github.com/ohana-garden/Vessels.git
cd Vessels

# Install dependencies
pip install -r requirements.txt

# Start FalkorDB
docker-compose up -d

# Run tests
pytest vessels/tests/test_integration_new_stack.py

# Start Vessels
python vessels_web_server.py
```

---

## System Requirements

### Tier 0 (Device)

**Minimum:**
- CPU: 2+ cores
- RAM: 2GB
- Storage: 5GB
- OS: Linux, macOS, Windows, Android, iOS

**Recommended:**
- CPU: 4+ cores
- RAM: 4GB
- Storage: 10GB
- GPU: Optional (for faster inference)

### Tier 1 (Edge Node)

**Minimum:**
- CPU: 4+ cores (x86_64 or ARM64)
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps
- OS: Ubuntu 22.04, Debian 12, macOS

**Recommended:**
- CPU: 8+ cores
- RAM: 32GB
- Storage: 256GB NVMe SSD
- GPU: NVIDIA RTX 3060 or better (24GB+ VRAM)
- Network: 1 Gbps

**Hardware Examples:**
- Raspberry Pi 5 (8GB): Minimum config
- Intel NUC 13 Pro: Good balance
- Mac Mini M2 Pro: Excellent performance
- Custom Linux server with RTX 4090: Maximum performance

### Tier 2 (Petals)

**Requirements:**
- Internet connection (for distributed compute)
- No local GPU needed
- Controlled by configuration

---

## Installation

### Step 1: Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/ohana-garden/Vessels.git
cd Vessels

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Core Dependencies

```bash
# Install base requirements
pip install -r requirements.txt

# This installs:
# - FalkorDB client
# - Graphiti
# - Core Python dependencies
```

### Step 3: Install Optional AI Components

#### A. Speech-to-Text (Choose One)

**Option 1: faster-whisper (Recommended)**
```bash
pip install faster-whisper
```

**Option 2: whisper.cpp**
```bash
pip install whispercpp
```

**Option 3: OpenAI Whisper**
```bash
pip install openai-whisper
```

#### B. Text-to-Speech (Choose One or More)

**Piper (Fast, MIT licensed)**
```bash
# Install Piper from releases
# See: https://github.com/rhasspy/piper
pip install piper-tts
```

**Kokoro (High quality, Apache 2.0)**
```bash
# When available:
# pip install kokoro-tts
```

**espeak (Always available fallback)**
```bash
# Linux
sudo apt-get install espeak

# macOS
brew install espeak

# Windows
# Download from: http://espeak.sourceforge.net/
```

#### C. On-Device LLM (Choose One)

**llama.cpp (Recommended)**
```bash
pip install llama-cpp-python
```

**ExecuTorch (When available)**
```bash
# Will be available from PyTorch:
# pip install executorch
```

**Transformers (Fallback)**
```bash
pip install transformers torch
```

#### D. Petals (Optional, Tier 2)

```bash
# ONLY install if you want distributed large model access
pip install petals
```

### Step 4: Start FalkorDB

```bash
# Using Docker Compose (recommended)
docker-compose up -d

# Verify FalkorDB is running
docker ps | grep falkordb

# Test connection
redis-cli -p 6379 PING
```

**Without Docker:**
```bash
# Build from source
git clone https://github.com/FalkorDB/FalkorDB.git
cd FalkorDB
make
redis-server --loadmodule ./bin/linux-x64-release/src/falkordb.so
```

### Step 5: Download AI Models

```bash
# Create model cache directory
mkdir -p ~/.cache/vessels/{whisper,llm,tts}

# Download Whisper model (automatic on first use)
# Or manually:
cd ~/.cache/vessels/whisper
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin

# Download LLM model
# Example: Llama 3.2 1B (quantized)
cd ~/.cache/vessels/llm
# Download from HuggingFace or use llama.cpp to convert
```

---

## Configuration

### 1. Copy Example Config

```bash
cp config/vessels.yaml config/vessels.local.yaml
```

### 2. Edit Configuration

```yaml
# config/vessels.local.yaml

# Set your community ID
community_id: "your_community_name"

# Configure compute tiers
compute:
  tier0:
    enabled: true
    model: "Llama-3.2-1B"

  tier1:
    enabled: true
    host: "localhost"  # Or your edge node IP
    port: 8080

  tier2:
    enabled: false  # Keep disabled unless you need it

# Configure device AI
device:
  stt:
    enabled: true
    model: "small.en"  # Choose based on your hardware

  tts:
    enabled: true
    engine: "piper"  # or "kokoro" when available

  emotion:
    enabled: true

# Privacy settings
privacy:
  default_privacy_level: "PRIVATE"
  sanitize_external_data: true

# Nostr (keep disabled by default)
communication:
  nostr:
    enabled: false
```

### 3. Set Environment Variables

```bash
# .env file
VESSELS_CONFIG=config/vessels.local.yaml
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
LOG_LEVEL=INFO
```

---

## Deployment Modes

### Mode 1: Single Device (Development)

Everything runs on one machine (laptop/desktop).

```yaml
# config/vessels.yaml
deployment_mode: "device"

compute:
  tier0:
    enabled: true
  tier1:
    enabled: false
  tier2:
    enabled: false
```

**Start:**
```bash
python vessels_web_server.py
```

### Mode 2: Device + Edge (Recommended)

Device (phone/tablet) connects to home server (edge node).

**On Edge Node:**
```bash
# Start FalkorDB
docker-compose up -d

# Start Vessels edge service
python vessels_edge_server.py --host 0.0.0.0 --port 8080
```

**On Device:**
```yaml
# config/vessels.yaml
compute:
  tier0:
    enabled: true
  tier1:
    enabled: true
    host: "192.168.1.100"  # Your edge node IP
    port: 8080
```

### Mode 3: Full Stack (Device + Edge + Petals)

Add distributed large model access (optional).

```yaml
# config/vessels.yaml
compute:
  tier2:
    enabled: true
    allowed_models:
      - "meta-llama/Llama-3.1-70b-hf"
    sanitize_data: true
```

### Mode 4: Multi-Community (Production)

Multiple communities sharing infrastructure.

```bash
# Deploy with Docker
docker-compose -f docker-compose.prod.yml up -d

# Nginx reverse proxy for multi-community routing
# See: docs/deployment/nginx.conf
```

---

## Testing

### Unit Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest vessels/tests/test_integration_new_stack.py

# Run with coverage
pytest --cov=vessels --cov-report=html
```

### Integration Tests

```bash
# Test FalkorDB connection
python -c "import redis; r = redis.Redis(port=6379); print(r.ping())"

# Test Graphiti
python -c "from vessels.knowledge import GraphitiClient; print('Graphiti OK')"

# Test device AI components
pytest vessels/tests/test_integration_new_stack.py::TestDeviceSTT
pytest vessels/tests/test_integration_new_stack.py::TestDeviceTTS
pytest vessels/tests/test_integration_new_stack.py::TestDeviceLLM
```

### End-to-End Test

```bash
# Start all services
docker-compose up -d
python vessels_web_server.py &

# Run E2E test
python vessels/tests/e2e_test.py

# Expected output:
# ✓ STT: Audio → Text
# ✓ Emotion: Analyzed state
# ✓ LLM: Generated response
# ✓ TTS: Text → Audio
# ✓ End-to-end latency: <2s
```

---

## Troubleshooting

### FalkorDB Issues

**Problem:** FalkorDB won't start
```bash
# Check logs
docker logs falkordb

# Check port availability
lsof -i :6379

# Restart FalkorDB
docker-compose restart falkordb
```

**Problem:** Out of memory
```bash
# Edit docker-compose.yml
# Increase maxmemory:
command: ["falkordb-server", "--maxmemory", "2gb"]
```

### Model Download Issues

**Problem:** Whisper model download fails
```bash
# Manual download
cd ~/.cache/vessels/whisper
wget https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin

# Verify
ls -lh ggml-small.en.bin
```

**Problem:** LLM model not found
```bash
# Set model path explicitly
export VESSELS_LLM_MODEL_PATH=/path/to/model.gguf

# Or in config:
device:
  local_llm:
    model_path: "/path/to/model.gguf"
```

### Performance Issues

**Problem:** Device tier too slow
```bash
# Use smaller model
device:
  local_llm:
    model: "TinyLlama-1.1B"  # Instead of Llama-3.2-1B

  stt:
    model: "tiny.en"  # Instead of small.en
```

**Problem:** Edge tier latency high
```bash
# Check network
ping <edge-node-ip>

# Check edge node CPU/GPU
ssh <edge-node> "top"
ssh <edge-node> "nvidia-smi"  # If GPU

# Enable GPU acceleration
compute:
  tier1:
    device: "cuda"  # Instead of "cpu"
```

### Petals Issues

**Problem:** Petals requests timing out
```bash
# Increase timeout
compute:
  tier2:
    timeout_seconds: 60  # Instead of 30

# Or disable Petals
compute:
  tier2:
    enabled: false
```

### Privacy Issues

**Problem:** Sensitive data in logs
```bash
# Disable sensitive logging
privacy:
  log_sensitive_data: false

# Check logs
grep -i "personal\|private" logs/vessels.log
```

---

## Production Deployment

### Security Checklist

- [ ] Enable TLS for all network communication
- [ ] Set strong passwords for FalkorDB
- [ ] Disable Nostr unless needed
- [ ] Keep Petals disabled by default
- [ ] Enable action gating and constraint validation
- [ ] Set `log_sensitive_data: false`
- [ ] Use `deployment_mode: "edge"` not "device"
- [ ] Regular backups of FalkorDB snapshots
- [ ] Monitor disk space and memory usage

### Backup & Restore

**Backup FalkorDB:**
```bash
# Trigger snapshot
redis-cli -p 6379 SAVE

# Copy snapshot
cp /var/lib/falkordb/dump.rdb backups/dump-$(date +%Y%m%d).rdb
```

**Restore FalkorDB:**
```bash
# Stop FalkorDB
docker-compose stop falkordb

# Replace snapshot
cp backups/dump-20240101.rdb /var/lib/falkordb/dump.rdb

# Start FalkorDB
docker-compose start falkordb
```

### Monitoring

```bash
# FalkorDB stats
redis-cli -p 6379 INFO

# Vessels stats
curl http://localhost:8080/api/stats

# GPU usage (if applicable)
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv
```

---

## Next Steps

1. **Test Your Deployment**: Run all tests to verify everything works
2. **Configure Privacy**: Review `config/vessels.yaml` privacy settings
3. **Deploy Agents**: See `docs/agents/` for agent development
4. **Set Up Monitoring**: Configure metrics and alerting
5. **Join Community**: Share your experience and get support

---

## Support

- **Documentation**: https://github.com/ohana-garden/Vessels/tree/main/docs
- **Issues**: https://github.com/ohana-garden/Vessels/issues
- **Architecture**: See `docs/architecture/vessels-architecture.md`

---

## License

Vessels is released under the Apache 2.0 license. See LICENSE for details.
