# Shoghi Replicant

**Complete Docker-based deployment of Shoghi + Agent Zero**

Shoghi Replicant is a fully containerized, production-ready deployment of the Shoghi AI agent coordination platform combined with Agent Zero meta-coordination engine. Run the entire system with a single command.

---

## 🌟 What is Shoghi Replicant?

Shoghi Replicant packages the complete Shoghi ecosystem into Docker containers:

### **Shoghi Moral Constraint System**
A groundbreaking AI alignment framework that tracks agent behavior in a 12-dimensional phase space:
- **5D Operational Metrics**: Latency, memory usage, task success rate, error frequency, resource efficiency
- **7D Virtue Inference**: Truthfulness, Justice, Trustworthiness, Unity, Service, Detachment, Understanding
- **Moral Geometry**: Bahá'í-derived manifold for virtue-based behavioral constraints
- **Action Gating**: Real-time validation before agent actions execute
- **Attractor Discovery**: DBSCAN clustering identifies behavioral patterns
- **Adaptive Interventions**: Progressive responses to detrimental behavior

### **Agent Zero Coordination Platform**
Meta-coordination engine for dynamic agent orchestration:
- **Grant Discovery & Coordination**: Automated grant finding and application generation
- **Content Generation**: Culturally-aware, context-specific content (Hawaiian, Japanese, Filipino cultures)
- **Voice Interface**: Emotion-aware interaction using Hume.ai
- **Community Memory**: Persistent knowledge storage and retrieval
- **Dynamic Agent Creation**: Natural language → agent instances
- **KALA Value System**: Non-monetary value tracking (1 kala ≈ $1 USD reference)

---

## 🚀 Quick Start

### Prerequisites
- **Docker** (20.10+)
- **Docker Compose** (2.0+)
- 4GB+ RAM recommended
- 10GB+ disk space

### One-Command Installation

```bash
git clone <your-repo-url> shoghi-replicant
cd shoghi-replicant
./start.sh
```

That's it! Shoghi Replicant is now running at **http://localhost:5000**

---

## 📋 What Gets Installed?

The startup script automatically:
1. ✅ Creates `.env` from `.env.example` (if needed)
2. ✅ Builds Docker images
3. ✅ Starts services:
   - **Shoghi** (main application on port 5000)
   - **Redis** (community memory/caching on port 6379)
   - **PostgreSQL** (production database on port 5432)
4. ✅ Sets up persistent volumes for data
5. ✅ Configures health checks

---

## 🎛️ Configuration

### Step 1: Environment Variables

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
nano .env  # or your preferred editor
```

### Step 2: Add Your API Keys

**Required for voice interface:**
```bash
HUME_API_KEY=your-hume-api-key-here
```

**Required for AI features:**
```bash
OPENAI_API_KEY=your-openai-key-here
ANTHROPIC_API_KEY=your-anthropic-key-here
```

**Important:** Generate a strong secret key for production:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```
Add this to `.env`:
```bash
SECRET_KEY=<generated-key-here>
```

### Step 3: Database Choice

**SQLite (Default - Easy Setup):**
```bash
DATABASE_URL=sqlite:////app/data/shoghi.db
```

**PostgreSQL (Production Recommended):**
```bash
DATABASE_URL=postgresql://shoghi:shoghi@postgres:5432/shoghi
```

---

## 🛠️ Usage

### Start Shoghi
```bash
./start.sh
```

### Start with Debug Tools
Includes Redis Commander (port 8081) and pgAdmin (port 8082):
```bash
./start.sh start debug
```

### View Logs
```bash
./start.sh logs
```

### Check Status
```bash
./start.sh status
```

### Stop Shoghi
```bash
./start.sh stop
```

### Restart
```bash
./start.sh restart
```

### Access Container Shell
```bash
./start.sh shell
```

### Clean Everything (removes all data!)
```bash
./start.sh clean
```

### Rebuild from Scratch
```bash
./start.sh rebuild
```

---

## 🌐 Access Points

Once running, access these services:

| Service | URL | Description |
|---------|-----|-------------|
| **Shoghi Web UI** | http://localhost:5000 | Main application interface |
| **Voice Interface** | http://localhost:5000/voice | Emotion-aware voice UI |
| **Redis** | localhost:6379 | Community memory cache |
| **PostgreSQL** | localhost:5432 | Production database |
| **Redis Commander** | http://localhost:8081 | Redis debugging (debug mode) |
| **pgAdmin** | http://localhost:8082 | Database admin (debug mode) |

---

## 📂 Architecture

### Service Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      Shoghi Application                     │
│  ┌────────────────┐  ┌──────────────────────────────────┐  │
│  │  Web Server    │  │  Agent Zero Coordination Engine  │  │
│  │  (Flask)       │  │  - Dynamic agent creation        │  │
│  │  - REST API    │  │  - Message bus                   │  │
│  │  - Voice UI    │  │  - Resource management           │  │
│  └────────────────┘  └──────────────────────────────────┘  │
│                                                             │
│  ┌────────────────┐  ┌──────────────────────────────────┐  │
│  │ Moral System   │  │  Community Features              │  │
│  │  - 12D Phase   │  │  - Grant coordination            │  │
│  │  - Constraints │  │  - Content generation            │  │
│  │  - Gating      │  │  - Memory system                 │  │
│  └────────────────┘  └──────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │              │
           ┌─────────────┘              └──────────────┐
           ▼                                           ▼
    ┌─────────────┐                            ┌──────────────┐
    │   Redis     │                            │  PostgreSQL  │
    │  (Memory)   │                            │  (Database)  │
    └─────────────┘                            └──────────────┘
```

### Directory Structure

```
shoghi-replicant/
├── start.sh                    # One-command startup script
├── Dockerfile                  # Multi-stage production build
├── docker-compose.yml          # Service orchestration
├── .env.example                # Environment configuration template
├── requirements.txt            # Python dependencies
│
├── Core Application Files
│   ├── shoghi.py               # Main platform entry
│   ├── shoghi_web_server.py    # Flask web server
│   ├── agent_zero_core.py      # Agent coordination engine
│   ├── community_memory.py     # Persistent memory system
│   ├── content_generation.py   # Contextual content creation
│   ├── grant_coordination_system.py  # Grant discovery
│   ├── kala.py                 # Value tracking system
│   ├── voice_interface.py      # Voice UI
│   └── ... (additional modules)
│
├── Moral Constraint System
│   └── shoghi/
│       ├── constraints/        # Bahá'í moral manifold
│       ├── measurement/        # 12D phase space tracking
│       ├── gating/             # Action validation
│       ├── phase_space/        # Trajectory & attractor analysis
│       └── intervention/       # Behavioral interventions
│
├── BMAD System (Agent Definitions)
│   └── .bmad/
│       ├── control_manifest.yaml
│       ├── agents/             # Agent definition files
│       ├── specs/              # Architecture docs
│       └── stories/            # User story templates
│
└── Documentation
    ├── README.md               # This file
    ├── SHOGHI_FINAL_COMPLETE.md  # Complete vision doc
    ├── KALA.md                 # KALA value system
    └── CODE_REVIEW_REPORT.md  # Recent code review
```

---

## 🧪 Testing

The Shoghi codebase includes comprehensive test coverage (241 tests, all passing).

### Run Tests in Container

```bash
docker exec -it shoghi-replicant pytest
```

### Run Specific Test Suite

```bash
docker exec -it shoghi-replicant pytest shoghi/tests/
```

### View Test Coverage

```bash
docker exec -it shoghi-replicant pytest --cov=shoghi --cov-report=html
```

---

## 🔒 Security Considerations

### Production Checklist

- [ ] Change `SECRET_KEY` in `.env` to a strong random value
- [ ] Use strong PostgreSQL passwords
- [ ] Restrict API key permissions to minimum necessary
- [ ] Never commit `.env` file to version control
- [ ] Use Docker secrets for sensitive values
- [ ] Enable HTTPS/TLS for production deployments
- [ ] Configure firewall rules to restrict port access
- [ ] Regularly update Docker images and dependencies
- [ ] Review and audit agent behaviors using moral constraint logs
- [ ] Set up monitoring and alerting

---

## 🐛 Troubleshooting

### Container won't start

```bash
# Check Docker status
docker ps -a

# View detailed logs
./start.sh logs

# Check Docker daemon
docker info
```

### Database connection errors

```bash
# Verify PostgreSQL is running
docker exec -it shoghi-postgres pg_isready

# Check database credentials in .env
cat .env | grep POSTGRES
```

### Redis connection issues

```bash
# Test Redis connection
docker exec -it shoghi-redis redis-cli ping

# View Redis logs
docker logs shoghi-redis
```

### Port already in use

Edit `.env` to use different ports:
```bash
SHOGHI_PORT=5001
REDIS_PORT=6380
POSTGRES_PORT=5433
```

### Out of disk space

```bash
# Clean up old Docker data
docker system prune -a

# Remove Shoghi volumes (WARNING: deletes all data!)
./start.sh clean
```

---

## 📊 Monitoring & Observability

### View Container Stats

```bash
docker stats shoghi-replicant
```

### Access Redis Metrics

```bash
docker exec -it shoghi-redis redis-cli INFO
```

### PostgreSQL Performance

```bash
docker exec -it shoghi-postgres psql -U shoghi -c "SELECT * FROM pg_stat_activity;"
```

### Application Logs

```bash
# Real-time log streaming
./start.sh logs

# Save logs to file
docker logs shoghi-replicant > shoghi.log 2>&1
```

---

## 🌍 Deployment Options

### Local Development
```bash
./start.sh
```

### Production Single Server
```bash
# Use PostgreSQL and strong security settings
# Edit .env with production values
FLASK_ENV=production ./start.sh
```

### Cloud Deployment (AWS/GCP/Azure)

1. Build and push image:
```bash
docker build -t your-registry/shoghi-replicant:latest .
docker push your-registry/shoghi-replicant:latest
```

2. Deploy using your cloud provider's container service:
   - AWS ECS/Fargate
   - GCP Cloud Run
   - Azure Container Instances

3. Use managed databases:
   - AWS RDS PostgreSQL
   - Google Cloud SQL
   - Azure Database for PostgreSQL

### Kubernetes

See `k8s/` directory (coming soon) for Kubernetes manifests.

---

## 🤝 Contributing

We welcome contributions! See the main [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `docker exec -it shoghi-replicant pytest`
5. Commit: `git commit -m "Add amazing feature"`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

---

## 📚 Additional Documentation

- **[SHOGHI_FINAL_COMPLETE.md](SHOGHI_FINAL_COMPLETE.md)** - Complete vision and design
- **[KALA.md](KALA.md)** - KALA value system documentation
- **[CODE_REVIEW_REPORT.md](CODE_REVIEW_REPORT.md)** - Recent code review findings
- **[shoghi/README.md](shoghi/README.md)** - Moral constraint system docs

---

## 🙏 Credits

**Shoghi Replicant** is developed by [Ohana Garden](https://github.com/ohana-garden)

Named after Shoghi Effendi, Guardian of the Bahá'í Faith, whose emphasis on systematic coordination and moral principles inspired this platform's architecture.

---

## 📜 License

[Add your license here - MIT, Apache 2.0, etc.]

---

## 💬 Support

- **Issues**: [GitHub Issues](https://github.com/ohana-garden/shoghi/issues)
- **Discussions**: [GitHub Discussions](https://github.com/ohana-garden/shoghi/discussions)
- **Email**: [Add contact email]

---

## 🎯 Roadmap

- [ ] Kubernetes deployment manifests
- [ ] Grafana/Prometheus monitoring integration
- [ ] Multi-language support for UI
- [ ] Enhanced BMAD agent marketplace
- [ ] Integration with additional LLM providers
- [ ] Advanced moral constraint visualization dashboard
- [ ] Distributed deployment support
- [ ] WebAssembly agent runtime

---

**Built with ❤️ by the Ohana Garden community**
