# Shoghi Replicant - Quick Start Guide

Get Shoghi up and running in 60 seconds!

## Prerequisites

- Docker 20.10+ installed
- Docker Compose 2.0+ installed
- 4GB+ RAM available
- 10GB+ disk space

## Installation Steps

### 1. Clone the Repository

```bash
git clone <your-repo-url> shoghi-replicant
cd shoghi-replicant
```

### 2. Configure Environment (Optional)

For basic testing, you can skip this step. For production or advanced features:

```bash
cp .env.example .env
nano .env  # Edit to add your API keys
```

### 3. Start Shoghi

**Single command to start everything:**

```bash
./start.sh
```

That's it! Wait for the containers to start (first run takes a few minutes to download images).

## Verify Installation

Once started, you should see:

```
[SUCCESS] Shoghi Replicant is running!

╔═══════════════════════════════════════════════════════════╗
║                    ACCESS INFORMATION                     ║
╚═══════════════════════════════════════════════════════════╝
  Shoghi Web Interface:  http://localhost:5000
  Redis:                 localhost:6379
  PostgreSQL:            localhost:5432
```

## Access the Application

Open your browser and navigate to:

**http://localhost:5000**

You should see the Shoghi voice-first UI!

## Common Commands

```bash
# View logs
./start.sh logs

# Check status
./start.sh status

# Stop Shoghi
./start.sh stop

# Restart
./start.sh restart

# Start with debug tools (Redis Commander, pgAdmin)
./start.sh start debug
```

## What to Do Next

1. **Test the Voice Interface**: Click "Allow" when prompted for microphone access
2. **Explore Grant Discovery**: Say "Find grants for community programs"
3. **Check System Status**: Visit http://localhost:5000/health
4. **View Debug Tools** (if started with debug profile):
   - Redis Commander: http://localhost:8081
   - pgAdmin: http://localhost:8082

## Adding API Keys

For full functionality, you'll need API keys:

1. **Hume.ai** (voice emotion detection): https://www.hume.ai/
2. **OpenAI** (GPT models): https://platform.openai.com/api-keys
3. **Anthropic** (Claude models): https://console.anthropic.com/

Add them to `.env`:

```bash
HUME_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here
ANTHROPIC_API_KEY=your-key-here
```

Then restart:

```bash
./start.sh restart
```

## Troubleshooting

### Port 5000 already in use?

Edit `.env`:

```bash
SHOGHI_PORT=5001
```

### Container won't start?

View logs:

```bash
./start.sh logs
```

### Need to reset everything?

```bash
./start.sh clean
./start.sh
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Explore the [moral constraint system](shoghi/README.md)
- Check out [KALA.md](KALA.md) for the value tracking system
- Review [SHOGHI_FINAL_COMPLETE.md](SHOGHI_FINAL_COMPLETE.md) for the complete vision

## Support

Having issues? Check the [Troubleshooting section](README.md#-troubleshooting) in the README or open an issue on GitHub.

---

**Happy coordinating! 🌺**
