# Vessels Architecture

**Version:** 1.0
**Status:** Living Document
**Last Updated:** 2025-11-21

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Design Principles](#design-principles)
3. [Three-Tier Compute Model](#three-tier-compute-model)
4. [Core Subsystems](#core-subsystems)
5. [Data Flow](#data-flow)
6. [Security & Privacy](#security--privacy)
7. [Integration Points](#integration-points)

---

## Executive Summary

Vessels is a **vendor-neutral, local-first AI agent system** designed for community coordination, knowledge management, and practical task automation. It enforces moral constraints through geometric validation in a 12-dimensional phase space and operates across three compute tiers without dependency on proprietary cloud AI services.

### Key Technologies

- **FalkorDB**: Ultra-fast property graph database for real-time GraphRAG
- **Graphiti**: Temporal knowledge graph engine for agent memory
- **Nostr**: Decentralized event/messaging protocol for discovery
- **On-Device AI**: ExecuTorch, whisper.cpp, Piper/Kokoro for local inference
- **Petals**: Optional distributed large model network

### Core Tenets

1. **No Vendor Lock-In**: Zero dependencies on Apple Intelligence, Google Gemini, or proprietary cloud AI
2. **Local-First**: All personal data stays on device or edge node
3. **Privacy-First**: Explicit opt-in for any external communication
4. **Agent-Centric**: Every entity (person, plant, tool) can have agency
5. **Morally Constrained**: All actions validated through 12D geometric constraints

---

## Design Principles

### 1. Graduated Privacy Model

```
PRIVATE     → No cross-community reads (default)
SHARED      → Read-only to trusted communities
PUBLIC      → Read-only to all servants
FEDERATED   → Read/write coordination space
```

### 2. Multi-Class Agent System

**Community Servants** (Highest Standards)
- Truthfulness ≥ 0.95 (non-negotiable)
- Service ratio ≥ 0.90 (90% service orientation)
- Max extraction: 0.05 (5%)
- No commercial ties
- Gateway role for commercial access

**Commercial Agents** (Transparent Commercial)
- Truthfulness ≥ 0.95 (SAME as servants)
- Disclosure ≥ 0.98 (HIGHER than servants)
- Service ratio ≥ 0.60
- Max extraction: 0.40
- Radical transparency required
- Cannot access servant knowledge directly

**Hybrid Consultants** (Grant-funded specialists)
- Service ratio ≥ 0.75
- Between servant and commercial standards

### 3. 12-Dimensional Moral Phase Space

**5 Operational Dimensions** (directly measured):
- Activity level, Coordination density, Effectiveness, Resource consumption, System health

**7 Virtue Dimensions** (inferred from behavior):
- Truthfulness, Justice, Trustworthiness, Unity, Service, Detachment, Understanding

All agent actions are:
1. Measured in 12D space
2. Validated against moral manifolds
3. Projected to valid states if needed
4. Blocked if projection fails

---

## Three-Tier Compute Model

### Tier 0: Device UX Brain

**Hardware**: Phone, tablet, laptop, Raspberry Pi
**Latency**: < 100ms for interactive tasks
**Privacy**: Everything stays on device

**Capabilities**:
- Speech-to-Text (whisper.cpp)
- Text-to-Speech (Piper / Kokoro-82M)
- Emotional intelligence layer
- Small local LLM (via ExecuTorch)
- Intent classification
- UI rendering
- Sensor integration
- Cached knowledge

**Responsibilities**:
- Natural language understanding
- Emotional state tracking
- Simple reasoning and dialogue
- Privacy-sensitive interactions
- Offline capability

**Communication**:
- Local RPC to Tier 1 (home network)
- No external calls unless explicitly configured

---

### Tier 1: Local Edge Node

**Hardware**: Home server, NUC, Mac Mini, Ubuntu box
**Latency**: < 500ms for complex reasoning
**Privacy**: On your network, under your control

**Capabilities**:
- FalkorDB graph database
- Graphiti temporal knowledge graph
- Mid-sized open models (7B-70B params)
- Agent Zero meta-orchestrator
- Multi-agent coordination
- GraphRAG retrieval
- Vector stores (project + shared)
- Action gating system
- Community memory
- Nostr relay (optional)

**Responsibilities**:
- Core agent runtime
- Knowledge graph management
- Multi-agent task coordination
- Long-context reasoning
- Complex planning
- Cross-agent memory sharing
- Moral constraint validation
- Kala value tracking

**Communication**:
- Receives from Tier 0 devices
- Optionally connects to Tier 2 (Petals)
- Optionally publishes to Nostr relays

---

### Tier 2: Petals Network (Optional)

**Hardware**: Distributed volunteer GPUs worldwide
**Latency**: 2-10 seconds for large model inference
**Privacy**: Use only for non-sensitive, anonymized tasks

**Capabilities**:
- Very large open models (70B-405B params)
- Fine-tuning on community data
- Complex policy synthesis
- Long-document analysis
- Research and planning tasks

**Responsibilities**:
- Tasks requiring massive context windows
- Complex reasoning beyond Tier 1 capacity
- Non-real-time, non-sensitive analysis
- Optional fallback for resource-constrained edge nodes

**Communication**:
- Receives requests from Tier 1 only
- Never directly accessible from Tier 0
- All data sanitized before transmission

**Configuration**:
```python
petals:
  enabled: false  # Default OFF
  allowed_models:
    - "meta-llama/Llama-3.1-70b-hf"
    - "mistralai/Mixtral-8x7B-v0.1"
  max_tokens: 4096
  timeout_seconds: 30
  sanitize_data: true  # Strip PII before sending
```

---

## Core Subsystems

### 1. Knowledge Layer (Graphiti + FalkorDB)

**Location**: Tier 1
**Ports**: FalkorDB on 6379 (Redis protocol)
**Storage**: Docker volume, RDB snapshots every 6 hours

**Architecture**:
```
Knowledge API (vessels/knowledge/)
    ↓
Graphiti Client (temporal KG)
    ↓
FalkorDB (property graph + GraphRAG)
```

**Key Operations**:
```python
# Store episodic memory
knowledge_api.store_episode(
    agent_id="servant.garden_steward",
    episode={
        "timestamp": "2025-11-21T10:30:00Z",
        "content": "Tomato plant in Plot 3 showing blossom end rot",
        "entities": ["tomato_plant_03", "plot_3"],
        "context": {"weather": "hot", "soil_moisture": "low"}
    }
)

# Query context with time awareness
context = knowledge_api.query_context(
    agent_id="servant.garden_steward",
    question="What problems have we seen with tomatoes?",
    time_window="last_30_days",
    k=10
)

# Graph neighborhood traversal
neighbors = knowledge_api.graph_neighborhood(
    node_id="tomato_plant_03",
    depth=2,
    filters={"relationship_types": ["grows_in", "affected_by"]}
)
```

**Schema** (OpenCypher):
```cypher
// Core entity types
(Person)-[:STEWARD_OF]->(Plot)
(Plant)-[:GROWS_IN]->(Plot)
(Harvest)-[:HARVESTED_FROM]->(Plant)
(Harvest)-[:DELIVERED_TO]->(Household)
(Meal)-[:COOKED_IN]->(Kitchen)
(Storage)-[:STORES]->(Food)
(Servant)-[:SERVES]->(Community)
(CommercialAgent)-[:MONITORED_BY]->(Servant)
(Event)-[:OCCURRED_AT]->(Place)

// Temporal properties
{
  start_time: timestamp,
  end_time: timestamp,
  observed_at: timestamp,
  valid_from: timestamp,
  valid_to: timestamp
}
```

**Privacy Filtering**:
- All queries automatically filtered by community access rights
- Cross-community reads require SHARED or PUBLIC privacy level
- Commercial agents have zero read access to servant knowledge

---

### 2. Retrieval Layer (GraphRAG)

**Location**: Tier 1
**Latency Budget**: < 100ms total

**Hybrid Retrieval Strategy**:
1. **Project Vector Store** (~10ms): Per-servant, isolated, fast
2. **Graphiti Graph Traversal** (~20ms): Temporal, relational
3. **Shared Vector Store** (~30ms): Community-wide fallback
4. **Ranking & Fusion** (~10ms): Combine results

**Vector Store Architecture**:
```
Per-Servant (ProjectVectorStore):
  - Format: NumPy .npz (compressed)
  - Embeddings: 384-dim (all-MiniLM-L6-v2)
  - Location: work_dir/projects/{community}/{servant}/vectors/
  - Isolation: No cross-contamination

Community (SharedVectorStore):
  - Shared protocols, universal contacts
  - Deduplicated common knowledge
  - Read-only for servants
```

**Retrieval API**:
```python
# Context retrieval with latency budget
results = retrieval_api.retrieve(
    query="How do we handle blossom end rot?",
    agent_id="servant.garden_steward",
    k=10,
    latency_budget_ms=100,
    strategy="hybrid"  # vector + graph + shared
)

# Results include:
# - Relevant episodes from Graphiti
# - Graph neighborhood context
# - Vector similarity matches
# - Ranked and deduplicated
```

---

### 3. Communication Layer

#### 3.1 Local RPC (Tier 0 ↔ Tier 1)

**Protocol**: WebSocket or HTTP/2
**Port**: 8080 (configurable)
**Encryption**: TLS 1.3 for home network traffic

**API Surface**:
```python
# Tier 0 → Tier 1
tier1_client.send_message(
    agent_id="servant.garden_steward",
    message="What should I plant next week?",
    context={"location": "Plot 5", "season": "spring"}
)

# Tier 1 → Tier 0
response = {
    "agent_id": "servant.garden_steward",
    "message": "Based on soil temp and forecast...",
    "reasoning": [...],
    "confidence": 0.87
}
```

#### 3.2 Nostr (Tier 1 ↔ External)

**Purpose**: Decentralized discovery, offers/needs, community signaling
**Default**: DISABLED
**Configuration**: Explicit opt-in per event type

**Nostr Adapter** (`vessels/communication/nostr_adapter.py`):
```python
class NostrAdapter:
    def __init__(self, relays: List[str], keypair: NostrKeypair):
        self.relays = relays
        self.keypair = keypair
        self.client = NostrClient()

    def publish_event(self, kind: int, content: dict, tags: List[Tuple]):
        """Publish Shoghi event to Nostr relays"""
        event = {
            "kind": kind,
            "content": json.dumps(content),
            "tags": tags,
            "created_at": int(time.time())
        }
        signed = self.keypair.sign(event)
        for relay in self.relays:
            self.client.publish(relay, signed)

    def subscribe(self, filters: List[dict], callback: Callable):
        """Subscribe to Nostr events matching filters"""
        for relay in self.relays:
            self.client.subscribe(relay, filters, callback)
```

**Event Kinds** (NIPs):
```python
# Custom Vessels event kinds (NIP-01)
VESSELS_NODE_STATUS = 30100      # Regular heartbeat
VESSELS_OFFER = 30101            # Resource offer
VESSELS_NEED = 30102             # Resource need
VESSELS_COMMUNITY_METRIC = 30103 # Anonymized participation score
VESSELS_ANNOUNCEMENT = 30104     # Community event announcement

# Privacy model:
# - Node status: Publish only if enabled
# - Offers/needs: Sanitize personal details
# - Metrics: Aggregate and anonymize (k-anonymity ≥ 5)
# - Announcements: Public by design
```

**Configuration**:
```python
nostr:
  enabled: false  # Default OFF
  relays:
    - "wss://relay.damus.io"
    - "wss://relay.nostr.band"
  publish_types:
    - "offers"
    - "needs"
    # NOT status, NOT metrics (too revealing)
  subscribe_filters:
    - {"kinds": [30101, 30102], "authors": ["trusted_pubkey1", "..."]}
```

---

### 4. On-Device UX Layer (Tier 0)

#### 4.1 Speech-to-Text (whisper.cpp)

**Implementation**: `vessels/device/stt.py`

```python
class WhisperSTT:
    """On-device speech recognition via whisper.cpp"""

    def __init__(self, model_path: str, language: str = "en"):
        # Load whisper.cpp model (tiny, base, small, medium, large)
        self.model = load_whisper_model(model_path)
        self.language = language

    def transcribe(self, audio_buffer: bytes, streaming: bool = False):
        """
        Transcribe audio to text

        Args:
            audio_buffer: 16kHz mono PCM audio
            streaming: True for real-time, False for batch

        Returns:
            {
                "text": "transcribed text",
                "confidence": 0.95,
                "language": "en",
                "latency_ms": 120
            }
        """
        start = time.time()
        result = self.model.transcribe(
            audio_buffer,
            language=self.language,
            beam_size=5 if not streaming else 1
        )
        return {
            "text": result.text,
            "confidence": result.avg_logprob,
            "language": result.language,
            "latency_ms": int((time.time() - start) * 1000)
        }
```

**Models**:
- `tiny.en`: 39M params, ~75MB, ~10x realtime on phone
- `base.en`: 74M params, ~140MB, ~6x realtime
- `small.en`: 244M params, ~460MB, ~3x realtime (recommended)

**Platform Support**:
- Android: Via JNI wrapper
- iOS: Via C++ bridge
- Desktop: Direct Python bindings

#### 4.2 Text-to-Speech (Piper + Kokoro)

**Implementation**: `vessels/device/tts.py`

```python
class VesselsTTS:
    """On-device text-to-speech with emotional adaptation"""

    def __init__(self, engine: str = "kokoro"):
        # Kokoro-82M (Apache 2.0) or Piper (MIT)
        if engine == "kokoro":
            self.model = load_kokoro_model("hexgrad/Kokoro-82M")
        else:
            self.model = load_piper_model("en_US-lessac-medium")

    def speak(self, text: str, style: dict = None):
        """
        Generate speech audio

        Args:
            text: Text to synthesize
            style: {
                "speed": 1.0,        # 0.5-2.0
                "pitch": 1.0,        # 0.5-2.0
                "energy": 1.0,       # 0.5-2.0
                "emotion": "neutral" # calm, warm, urgent
            }

        Returns:
            {
                "audio": np.ndarray,  # 22kHz mono
                "duration_ms": 1500,
                "text": "spoken text"
            }
        """
        # Adapt style based on emotional context
        if style and style.get("emotion"):
            self.model.set_emotion_embedding(style["emotion"])

        audio = self.model.synthesize(
            text,
            speed=style.get("speed", 1.0) if style else 1.0,
            pitch=style.get("pitch", 1.0) if style else 1.0
        )

        return {
            "audio": audio,
            "duration_ms": len(audio) / 22050 * 1000,
            "text": text
        }
```

**Emotional Adaptation**:
```python
# Example: Slow down and soften when user is overwhelmed
if emotional_state["arousal"] > 0.7 and emotional_state["valence"] < 0.3:
    style = {"speed": 0.85, "energy": 0.7, "emotion": "calm"}
```

#### 4.3 On-Device LLM (ExecuTorch)

**Implementation**: `vessels/device/local_llm.py`

```python
class DeviceLLM:
    """Small on-device LLM via ExecuTorch"""

    def __init__(self, model_name: str = "Llama-3.2-1B"):
        # Load quantized model optimized for mobile
        self.model = load_executorch_model(
            model_name,
            quantization="q4",  # 4-bit for speed
            device="cpu"        # Or "gpu" on Android/iOS
        )

    def classify_intent(self, text: str) -> dict:
        """Fast intent classification for routing"""
        prompt = f"Classify intent: {text}\nIntent:"
        result = self.model.generate(prompt, max_tokens=10)
        return parse_intent(result)

    def simple_dialogue(self, message: str, history: List[dict]) -> str:
        """Local conversation for simple queries"""
        prompt = format_chat_prompt(history + [{"role": "user", "content": message}])
        response = self.model.generate(prompt, max_tokens=200)
        return response
```

**Models**:
- Llama 3.2 1B (quantized): ~500MB, 20 tok/s on phone
- Phi-3 Mini (quantized): ~800MB, 15 tok/s
- Gemma 2B (quantized): ~1GB, 12 tok/s

**Use Cases**:
- Intent classification (local, <100ms)
- Simple Q&A (device knowledge)
- Emotional state inference
- Command parsing
- NOT for complex reasoning (use Tier 1)

#### 4.4 Emotional Intelligence Layer

**Implementation**: `vessels/device/emotion.py`

```python
class EmotionalIntelligence:
    """Track and respond to user emotional state"""

    def __init__(self):
        # Small classifier (ExecuTorch-compatible)
        self.classifier = load_emotion_model("emotion-classifier-6d")
        self.history = deque(maxlen=10)  # Recent state

    def analyze(self, text: str, prosody: dict = None) -> dict:
        """
        Infer emotional state from text + optional prosody

        Returns:
            {
                "valence": 0.6,      # -1 (negative) to 1 (positive)
                "arousal": 0.3,      # 0 (calm) to 1 (excited)
                "tags": ["content", "focused"],
                "confidence": 0.82
            }
        """
        # Text-based classification
        text_features = self.classifier.encode_text(text)

        # Optional prosody features (pitch, energy, tempo)
        if prosody:
            prosody_features = self.classifier.encode_prosody(prosody)
            combined = np.concatenate([text_features, prosody_features])
        else:
            combined = text_features

        # Infer state
        state = self.classifier.predict(combined)
        self.history.append(state)

        return state

    def adapt_response(self, response: str, state: dict) -> dict:
        """Adapt response style based on emotional state"""

        # User overwhelmed? Simplify and slow down
        if state["arousal"] > 0.7 and state["valence"] < 0.3:
            return {
                "text": simplify_language(response),
                "tts_style": {"speed": 0.85, "emotion": "calm"},
                "verbosity": "low"
            }

        # User engaged and positive? Provide richer detail
        elif state["arousal"] > 0.5 and state["valence"] > 0.5:
            return {
                "text": expand_detail(response),
                "tts_style": {"speed": 1.0, "emotion": "warm"},
                "verbosity": "high"
            }

        # Default: neutral
        else:
            return {
                "text": response,
                "tts_style": {"speed": 1.0, "emotion": "neutral"},
                "verbosity": "medium"
            }
```

**Privacy**:
- Emotional state NEVER leaves device
- No long-term profiling by default
- Used only for real-time interaction adaptation
- Can be disabled entirely in config

---

### 5. Petals Gateway (Tier 2, Optional)

**Implementation**: `vessels/compute/petals_gateway.py`

```python
class PetalsGateway:
    """Optional gateway to distributed large models"""

    def __init__(self, config: dict):
        self.enabled = config.get("enabled", False)
        self.allowed_models = config.get("allowed_models", [])
        self.max_tokens = config.get("max_tokens", 4096)
        self.sanitize = config.get("sanitize_data", True)

        if self.enabled:
            from petals import AutoDistributedModelForCausalLM
            self.client = AutoDistributedModelForCausalLM

    def generate(self, prompt: str, model_name: str, **kwargs) -> dict:
        """
        Generate text using Petals network

        IMPORTANT: Only use for non-sensitive, sanitized content
        """
        if not self.enabled:
            raise RuntimeError("Petals gateway is disabled")

        if model_name not in self.allowed_models:
            raise ValueError(f"Model {model_name} not in allowed list")

        # Sanitize prompt if enabled
        if self.sanitize:
            prompt = self.sanitize_prompt(prompt)

        # Connect to Petals swarm
        model = self.client.from_pretrained(model_name)

        # Generate with timeout
        try:
            result = model.generate(
                prompt,
                max_new_tokens=min(kwargs.get("max_tokens", 512), self.max_tokens),
                temperature=kwargs.get("temperature", 0.7),
                timeout=kwargs.get("timeout", 30)
            )
            return {
                "text": result,
                "model": model_name,
                "sanitized": self.sanitize
            }
        except TimeoutError:
            return {
                "error": "Petals request timed out",
                "fallback": True
            }

    def sanitize_prompt(self, prompt: str) -> str:
        """
        Remove personal identifiers before sending to Petals

        - Replace names with roles
        - Remove addresses, phone numbers
        - Generalize specific details
        """
        # Implement PII detection and masking
        # Use spaCy NER or similar
        sanitized = mask_pii(prompt)
        return sanitized
```

**Routing Policy**:
```python
def should_use_petals(task: dict) -> bool:
    """Decide if task should go to Petals"""

    # Must be explicitly marked as non-sensitive
    if task.get("sensitive", True):
        return False

    # Must benefit from large context
    if task.get("context_length", 0) < 8192:
        return False  # Tier 1 can handle

    # Must not be real-time
    if task.get("latency_requirement_ms", 0) < 2000:
        return False  # Too slow

    # Petals must be enabled
    if not config["petals"]["enabled"]:
        return False

    return True
```

**Example Use Cases** (when enabled):
- Long policy document synthesis
- Complex regulatory analysis
- Multi-community strategic planning
- Large-scale pattern detection
- NOT for: Personal conversations, real-time tasks, sensitive data

---

### 6. LLM Router (Cross-Tier Orchestration)

**Implementation**: `vessels/compute/llm_router.py`

```python
class LLMRouter:
    """
    Route LLM requests to appropriate tier based on:
    - Latency requirement
    - Context size
    - Sensitivity
    - Resource availability
    """

    def __init__(self):
        self.tier0 = DeviceLLM()           # On-device
        self.tier1 = LocalEdgeLLM()        # Home server
        self.tier2 = PetalsGateway(config) # Optional

    async def route(self, request: dict) -> dict:
        """
        Intelligent routing across three tiers

        Args:
            request = {
                "prompt": str,
                "max_tokens": int,
                "latency_requirement_ms": int,
                "sensitive": bool,
                "context_length": int,
                "quality_requirement": float  # 0-1
            }

        Returns:
            {
                "response": str,
                "tier_used": int,  # 0, 1, or 2
                "latency_ms": int,
                "model": str
            }
        """

        # RULE 1: Sensitive data NEVER leaves device/edge
        if request["sensitive"]:
            if request["latency_requirement_ms"] < 200:
                return await self.tier0.generate(request)
            else:
                return await self.tier1.generate(request)

        # RULE 2: Real-time requires local
        if request["latency_requirement_ms"] < 200:
            return await self.tier0.generate(request)
        elif request["latency_requirement_ms"] < 1000:
            return await self.tier1.generate(request)

        # RULE 3: Large context may need Petals
        if request["context_length"] > 32000 and self.tier2.enabled:
            # Try Tier 2, fallback to Tier 1
            try:
                return await self.tier2.generate(request)
            except Exception as e:
                logger.warning(f"Petals failed: {e}, falling back to Tier 1")
                return await self.tier1.generate(request)

        # RULE 4: Default to Tier 1 (edge node)
        return await self.tier1.generate(request)
```

**Decision Matrix**:

| Criteria | Tier 0 (Device) | Tier 1 (Edge) | Tier 2 (Petals) |
|----------|----------------|---------------|-----------------|
| Latency | < 200ms | < 1s | 2-10s |
| Context | < 2K tokens | < 32K tokens | < 128K tokens |
| Sensitive Data | ✅ Yes | ✅ Yes | ❌ No |
| Offline Capable | ✅ Yes | ✅ Yes | ❌ No |
| Model Size | 1-3B params | 7-70B params | 70-405B params |
| Privacy | 🔒 Perfect | 🔒 Perfect | ⚠️ Sanitized |

---

## Data Flow

### Example: User asks "What should I plant next week?"

```
1. Tier 0 (Device UX Brain)
   ├─ STT: Audio → Text (whisper.cpp, 80ms)
   ├─ Emotion: Analyze prosody + text (20ms)
   ├─ Intent: Classify as "garden_planning" (Device LLM, 50ms)
   └─ Route: Send to Tier 1 (Edge Node)

2. Tier 1 (Local Edge Node)
   ├─ Agent Runtime: Route to "servant.garden_steward"
   ├─ Knowledge API:
   │   ├─ Query Graphiti for garden history (20ms)
   │   ├─ Retrieve from project vectors (10ms)
   │   └─ Get graph neighborhood (Plot 5 context) (15ms)
   ├─ LLM: Generate plan with local 70B model (800ms)
   ├─ Action Gating: Validate through 12D constraints (5ms)
   └─ Send response back to Tier 0

3. Tier 0 (Device UX Brain)
   ├─ Adapt response style based on emotion (10ms)
   ├─ TTS: Text → Audio (Kokoro, 200ms)
   └─ Display: Show plan in UI

Total latency: ~1.2 seconds (mostly LLM inference)
Privacy: Zero external calls
```

---

## Security & Privacy

### Data Residency

**Tier 0 (Device)**:
- User conversations
- Emotional state history
- Personal preferences
- Authentication tokens
- NEVER leaves device except via explicit Tier 1 connection

**Tier 1 (Edge Node)**:
- Community knowledge graph
- Agent state and history
- Project files and logs
- Vector embeddings
- Stays on local network unless Nostr/Petals enabled

**Tier 2 (Petals)**:
- Only sanitized, anonymized prompts
- No personal identifiers
- No sensitive community data
- Optional and disabled by default

### Threat Model

**Defended Against**:
- ✅ Cloud surveillance (no proprietary APIs)
- ✅ Data harvesting (local-first architecture)
- ✅ Vendor lock-in (all open source)
- ✅ Unauthorized access (action gating, moral constraints)
- ✅ Commercial exploitation (radical transparency requirements)

**Not Defended Against** (user responsibility):
- Physical device access (use disk encryption)
- Network MITM (use TLS, run local CAs)
- Malicious servants (vet agent code before deployment)

### Access Control

```python
# Example: Servant tries to access another community's data
request = {
    "agent_id": "servant.garden_steward",
    "community_id": "oakland_gardens",
    "query": "Get harvest data from berkeley_gardens"
}

# Knowledge API checks privacy policy
berkeley_policy = get_community_policy("berkeley_gardens")
if berkeley_policy.privacy != CommunityPrivacy.PUBLIC:
    raise PermissionError("Cross-community access denied")

# Commercial agents have even stricter rules
if agent_class == AgentClass.COMMERCIAL:
    raise PermissionError("Commercial agents cannot access servant knowledge")
```

---

## Integration Points

### For New Subsystems

**To integrate a new compute backend**:
1. Implement `vessels/compute/your_backend.py` with `generate()` interface
2. Add routing logic to `llm_router.py`
3. Add config to `config/compute.yaml`
4. Write tests in `vessels/tests/test_compute.py`

**To integrate a new communication protocol**:
1. Implement `vessels/communication/your_protocol.py` with `publish()` / `subscribe()`
2. Register adapter in `communication/protocol_registry.py`
3. Add privacy controls in `communication/sanitizer.py`
4. Add config to `config/communication.yaml`

**To add a new device capability**:
1. Implement `vessels/device/your_capability.py`
2. Expose via `device/device_api.py`
3. Add to device startup sequence in `device/__init__.py`
4. Add tests in `vessels/tests/test_device.py`

---

## Configuration Reference

**`config/vessels.yaml`**:
```yaml
# Core settings
community_id: "oakland_gardens"
deployment_mode: "edge"  # device, edge, cloud (cloud=air-gapped server)

# Compute tiers
compute:
  tier0_enabled: true
  tier1_host: "192.168.1.100"
  tier1_port: 8080
  tier2_enabled: false  # Petals

# Knowledge layer
knowledge:
  falkordb_host: "localhost"
  falkordb_port: 6379
  graphiti_namespace: "oakland_gardens"
  vector_store_type: "hybrid"  # project, shared, hybrid

# Communication
communication:
  local_rpc_enabled: true
  nostr_enabled: false
  nostr_relays:
    - "wss://relay.damus.io"
  nostr_publish_types: []  # Empty = publish nothing

# Device
device:
  stt_model: "whisper-small.en"
  tts_engine: "kokoro"
  local_llm_model: "Llama-3.2-1B"
  emotion_tracking_enabled: true

# Privacy
privacy:
  default_privacy_level: "PRIVATE"
  allow_cross_community_reads: false
  sanitize_external_data: true
  log_sensitive_data: false

# Moral constraints
constraints:
  action_gating_enabled: true
  truthfulness_minimum: 0.95
  service_ratio_minimum: 0.90  # For servants
  block_on_constraint_violation: true
```

---

## Next Steps

1. **Deployment Guide**: See `docs/deployment/` for setup instructions
2. **Agent Development**: See `docs/agents/` for creating new agents
3. **API Reference**: See `docs/api/` for programmatic access
4. **Testing**: See `docs/testing/` for test suite documentation

---

## Changelog

### 2025-11-21 - Initial Version
- Three-tier compute model defined
- FalkorDB + Graphiti integration specified
- Nostr communication layer designed
- On-device AI stack (STT/TTS/LLM) specified
- Petals gateway defined
- LLM router architecture established
