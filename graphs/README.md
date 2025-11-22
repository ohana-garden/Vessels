# Vessels TEN Framework Graphs

This directory contains TEN Framework graph definitions for the Vessels platform.

## What is a TEN Graph?

A TEN graph is a declarative JSON configuration that defines how extensions (nodes) are connected in a real-time processing pipeline. Think of it as a visual programming language for multimodal AI applications.

## Available Graphs

### `vessels_edge_agent.json`

**Purpose**: Real-time voice interface with local STT/TTS and Vessels agentic reasoning.

**Pipeline**:
```
Microphone → Agora RTC → Whisper STT → Vessels Bridge → Kokoro TTS → Agora RTC → Speaker
                                              ↓
                                       VesselsInterface
                                              ↓
                                     (Agent Zero, Action Gate)
```

**Use Cases**:
- Voice-first community coordination
- Spoken grant discovery
- Real-time elder care support
- Hands-free agent interaction

**Local-First**: All processing happens on-device (except optional Agora relay).

## Graph Components

### Nodes (Extensions)

Each graph contains one or more extensions:

1. **agora_rtc**
   - **Role**: Audio input/output via Agora Real-Time Communication
   - **Input**: Microphone audio
   - **Output**: Speaker audio
   - **Config**: `app_id`, `channel`, `token`, `uid`

2. **whisper_stt**
   - **Role**: Speech-to-text transcription (Whisper.cpp)
   - **Input**: PCM audio frames from Agora
   - **Output**: `text_data` frames with transcription
   - **Config**: `model`, `language`, `vad_enabled`, `streaming`

3. **vessels_bridge**
   - **Role**: Bridge TEN graph to Vessels agentic platform
   - **Input**: `text_data` from STT
   - **Output**: `text_data` to TTS (agent response)
   - **Config**: `user_id`, `community_id`, `vessel_id`, `context`

4. **kokoro_tts**
   - **Role**: Text-to-speech synthesis (Kokoro-82M)
   - **Input**: `text_data` from Vessels Bridge
   - **Output**: PCM audio frames to Agora
   - **Config**: `voice`, `sample_rate`, `speed`, `pitch`, `emotion`

### Connections

Connections define data flow between extensions:

```json
{
  "extension": "whisper_stt",
  "data": [{
    "name": "text_data",
    "dest": [{
      "extension": "vessels_bridge"
    }]
  }]
}
```

This means: "Send `text_data` from `whisper_stt` to `vessels_bridge`"

## Running a Graph

### Prerequisites

1. **Install TEN Framework**
   ```bash
   pip install ten-framework
   ```

2. **Install Extension Dependencies**
   ```bash
   # Whisper STT
   pip install faster-whisper

   # Kokoro TTS (or fallback)
   pip install kokoro-tts
   # OR
   pip install piper-tts

   # Agora RTC
   # Download from https://docs.agora.io/
   ```

3. **Set Environment Variables**
   ```bash
   export AGORA_APP_ID="your_app_id"
   export AGORA_CHANNEL="vessels_voice"
   export AGORA_TOKEN="your_token"
   export VESSELS_USER_ID="user_123"
   export VESSELS_COMMUNITY_ID="ohana_puna"
   ```

### Launch Graph

```bash
# From Vessels root directory
ten_framework run --graph graphs/vessels_edge_agent.json
```

### Connect Client

Use TEN client SDK or Agora RTC client to connect and interact.

## Graph Configuration

### Using Environment Variables

Graphs support environment variable substitution:

```json
{
  "property": {
    "user_id": "${VESSELS_USER_ID:-default_user}"
  }
}
```

Format: `${VAR_NAME:-default_value}`

### Extension Groups

Extensions can be grouped for parallel processing:

```json
{
  "extension_group": "default"
}
```

Currently using single `"default"` group for sequential processing.

## Development

### Creating a New Graph

1. Copy `vessels_edge_agent.json` as template
2. Modify nodes (add/remove/configure extensions)
3. Update connections (define data flow)
4. Test with: `ten_framework run --graph graphs/your_graph.json`

### Debugging Graphs

Enable debug logging:

```bash
export LOG_LEVEL=debug
ten_framework run --graph graphs/vessels_edge_agent.json
```

Visualize graph (if TEN provides visualization tools):

```bash
ten_framework visualize --graph graphs/vessels_edge_agent.json
```

### Graph Validation

Validate graph schema:

```bash
ten_framework validate --graph graphs/vessels_edge_agent.json
```

## Architecture Patterns

### Pattern 1: Linear Pipeline

```
A → B → C → D
```

Simple sequential processing (used in `vessels_edge_agent.json`).

### Pattern 2: Parallel Processing

```
A → B ↘
      → D
A → C ↗
```

Multiple paths process data concurrently.

### Pattern 3: Feedback Loop

```
A → B → C
    ↑   ↓
    └───┘
```

Extension output feeds back to earlier stage (useful for iterative reasoning).

## Best Practices

1. **Keep Graphs Simple**: Start with linear pipelines, add complexity as needed
2. **Use Environment Variables**: Make graphs reusable across deployments
3. **Local-First**: Prefer on-device extensions over cloud APIs
4. **Error Handling**: Extensions should fail gracefully
5. **Resource Management**: Consider CPU/memory constraints per node

## Troubleshooting

### Graph Won't Start

- Check all extensions are installed: `ten_framework list-extensions`
- Validate environment variables are set
- Check logs for missing dependencies

### Audio Not Working

- Verify Agora credentials (`AGORA_APP_ID`, `AGORA_TOKEN`)
- Check microphone permissions
- Test audio devices: `arecord -l` (Linux), `system_profiler SPAudioDataType` (macOS)

### STT Not Transcribing

- Check Whisper model is downloaded (~460MB for `small.en`)
- Verify VAD threshold (`vad_threshold: 0.5`)
- Increase `beam_size` for better accuracy (slower)

### TTS Not Speaking

- Check Kokoro model is loaded
- Verify audio output device
- Test with espeak fallback: `espeak "test"`

## Future Graphs

Potential additions:

1. **vessels_multimodal_agent.json**
   - Add video processing (camera → vision model)
   - Screen sharing and visual context

2. **vessels_translator.json**
   - Multi-language support (Hawaiian, Spanish, etc.)
   - Real-time translation extension

3. **vessels_emotional_agent.json**
   - Emotion detection from voice
   - Adaptive TTS based on user state

4. **vessels_collaborative.json**
   - Multi-user support
   - Spatial audio for group coordination

## References

- [TEN Framework Docs](https://github.com/TEN-framework/TEN-framework)
- [Graph Schema Reference](https://docs.ten-framework.io/graph-schema)
- [Extension Development](https://docs.ten-framework.io/extensions)

## License

Apache 2.0
