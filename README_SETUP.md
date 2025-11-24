# Vessels Setup Guide

## Quick Start

### Option 1: Interactive Setup (Recommended)

Run the interactive setup wizard to configure all API keys:

```bash
python setup.py
```

This will:
- ✅ Ask for each API key one by one
- ✅ Write configuration to `.env` file
- ✅ Auto-configure Agent Zero (skip setup screen)
- ✅ Generate secure secrets automatically

### Option 2: Manual Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your API keys:
   ```bash
   nano .env   # or use your preferred editor
   ```

3. Start Vessels:
   ```bash
   docker-compose up --build
   ```

## What Gets Configured

### Agent Zero (AI Models)
- **OpenAI** - GPT-4 Turbo, GPT-3.5
- **Anthropic** - Claude 3 Opus, Sonnet, Haiku
- **Azure OpenAI** - Enterprise deployments
- **Ollama** - Local LLMs (runs automatically, no keys needed)

### Payment Services
- **TigerBeetle** - Distributed ledger (runs automatically)
- **Mojaloop** - Instant payments for Hawaii
- **RTP/FedNow** - Real-time payments
- **Modern Treasury** - ACH + RTP aggregator

### Voice/Multimodal UX
- **TEN Framework** - Voice pipelines (uses OpenAI Realtime API)

### Distributed AI
- **Petals** - Distributed large model inference (optional)

### P2P Network
- **Nostr** - Decentralized messaging (optional)

## Running Without API Keys

You can run Vessels with just local components:

```bash
# Minimal .env file
OLLAMA_ENABLED=true
OLLAMA_BASE_URL=http://localhost:11434
FALKORDB_HOST=localhost
FALKORDB_PORT=6379
TEN_FRAMEWORK_ENABLED=true
PETALS_ENABLED=false
MOJALOOP_ENABLED=false
```

This uses:
- ✅ Local LLMs via Ollama (no API keys)
- ✅ FalkorDB graph database (no API keys)
- ✅ TigerBeetle ledger (no API keys)
- ✅ TEN Framework (no API keys for local voice)

## Environment Variables Reference

### Required for Agent Zero
At least ONE of these AI providers:
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key
- `OLLAMA_ENABLED=true` - Use local LLMs

### Optional Payment APIs
- `MOJALOOP_API_KEY` - Mojaloop switch access
- `RTP_API_KEY` - RTP provider access
- `MODERN_TREASURY_API_KEY` - Modern Treasury access

### Auto-Generated
These are created automatically by setup:
- `JWT_SECRET` - Payment API security
- `NOSTR_PRIVATE_KEY` - Nostr identity (if enabled)

## Troubleshooting

### "No AI providers configured"
Run `python setup.py` and configure at least one AI provider, or enable Ollama for local LLMs.

### Payment service not starting
Check that TigerBeetle initialized correctly:
```bash
docker-compose logs payment-service
docker-compose logs tigerbeetle
```

### Agent Zero shows setup screen
Delete the Agent Zero cache and restart:
```bash
rm -rf agent_zero_config/
python setup.py
```

## Security Notes

- **Never commit `.env` to git** - It contains secrets
- `.env.example` is safe to commit - It has no secrets
- `setup.py` generates secure random secrets automatically
- API keys are stored only in `.env` (never in code)

## Next Steps

After setup:
1. Start Vessels: `docker-compose up --build`
2. Open browser: http://localhost:5000
3. Payment API: http://localhost:3000/graphql
4. View logs: `docker-compose logs -f`

For more details, see the full documentation.
