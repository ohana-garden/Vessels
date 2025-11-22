# Vessels Bridge Extension for TEN Framework

## Overview

The **Vessels Bridge** is a TEN Framework extension that integrates the Vessels agentic platform with real-time voice interactions. It acts as the glue between the TEN audio graph (handling STT/TTS) and the Vessels reasoning layer (Action Gate, Agent Zero).

## Architecture

### TEN Framework Pipeline

```
┌─────────────┐     ┌──────────────┐     ┌────────────────┐     ┌─────────────┐     ┌─────────────┐
│  Microphone │────▶│  Agora RTC   │────▶│  Whisper STT   │────▶│   Vessels   │────▶│ Kokoro TTS  │
│   (Audio)   │     │ (Audio Input)│     │ (Transcription)│     │   Bridge    │     │ (Synthesis) │
└─────────────┘     └──────────────┘     └────────────────┘     └────────────┬┘     └──────┬──────┘
                                                                               │              │
                                                                               │              │
                                                                               ▼              ▼
                                                                    ┌──────────────────┐     │
                                                                    │ VesselsInterface │     │
                                                                    │  (Agent Zero,    │     │
                                                                    │  Action Gate)    │     │
                                                                    └──────────────────┘     │
                                                                                             │
┌─────────────┐     ┌──────────────┐                                                        │
│   Speaker   │◀────│  Agora RTC   │◀───────────────────────────────────────────────────────┘
│   (Audio)   │     │(Audio Output)│
└─────────────┘     └──────────────┘
```

### Component Responsibilities

1. **Agora RTC** - Real-time audio capture and playback
2. **Whisper STT** - Speech-to-text transcription (on-device, local-first)
3. **Vessels Bridge** - This extension! Connects TEN to Vessels logic
4. **Kokoro TTS** - Text-to-speech synthesis (on-device, Apache 2.0 licensed)
5. **VesselsInterface** - Vessels agentic reasoning (Action Gate, Agent Zero, Grant System, etc.)

## Key Features

- **Local-First**: All processing happens on-device (no cloud dependencies for STT/TTS)
- **Real-Time**: Non-blocking architecture using thread pools for Vessels processing
- **Session Management**: Maintains session context across multiple voice interactions
- **Emotional Adaptation**: Ready for emotional TTS modulation based on context
- **Agent Integration**: Direct connection to full Vessels agent ecosystem

## Files

```
ten_packages/extension/vessels_bridge/
├── manifest.json      # TEN extension metadata and I/O schema
├── property.json      # Default configuration properties
├── extension.py       # Main bridge logic (VesselsBridgeExtension class)
├── __init__.py        # Python package initialization
└── README.md          # This file
```

## Configuration

### Properties (property.json)

| Property       | Type   | Default           | Description                           |
|----------------|--------|-------------------|---------------------------------------|
| `user_id`      | string | `"default_user"`  | User identifier for Vessels           |
| `community_id` | string | `"default_community"` | Community identifier           |
| `vessel_id`    | string | `""`              | Optional vessel ID                    |
| `context`      | string | `"voice_interface"` | Context for agent processing       |
| `language`     | string | `"en"`            | Language code                         |
| `log_level`    | string | `"info"`          | Logging level (debug/info/warning/error) |

### Environment Variables (used in graph.json)

```bash
# Agora RTC credentials
export AGORA_APP_ID="your_app_id"
export AGORA_CHANNEL="vessels_voice"
export AGORA_TOKEN="your_token"

# Vessels configuration
export VESSELS_USER_ID="user_123"
export VESSELS_COMMUNITY_ID="ohana_puna"
export VESSELS_VESSEL_ID=""  # Optional

# Logging
export LOG_LEVEL="info"
```

## How It Works

### Flow: User speaks → Agent responds

1. **Audio Capture**: User speaks into microphone
   - Agora RTC captures audio stream
   - Sends PCM audio frames to Whisper STT

2. **Speech-to-Text**: Whisper transcribes audio
   - Processes audio in real-time
   - Sends `text_data` frames to Vessels Bridge
   - Includes flags: `is_final`, `end_of_segment`

3. **Vessels Processing**: Bridge receives text
   - Filters for `is_final=true` (ignores interim results)
   - Spawns thread to call `VesselsInterface.process_message()`
   - Passes user_id, message, context, vessel_id
   - **Crucial**: This is where Agent Zero/Action Gate process the request

4. **Agent Response**: Vessels returns response
   - Response text extracted from result
   - Bridge creates `text_data` frame
   - Sends to Kokoro TTS

5. **Text-to-Speech**: Kokoro synthesizes audio
   - Generates PCM audio frames
   - Sends to Agora RTC for playback

6. **Audio Playback**: User hears response
   - Agora RTC plays audio through speaker

### Code: Key Methods

#### `on_start()`
Initializes VesselsInterface and loads configuration from TEN properties.

#### `on_data()`
Receives `text_data` from STT. Checks `is_final` flag and spawns processing thread.

#### `_process_vessels_message()`
Runs in thread pool. Calls `vessels_interface.process_message()` and sends response to TTS.

#### `_send_text_to_tts()`
Creates TEN `text_data` frame and sends to next extension in graph.

## Integration Points

### Input: From Whisper STT

```python
{
  "text": "I need help finding grants for elder care",
  "is_final": true,
  "stream_id": 12345,
  "end_of_segment": true
}
```

### Processing: Vessels Interface Call

```python
response = vessels_interface.process_message(
    user_id="user_123",
    message="I need help finding grants for elder care",
    context={
        "community_id": "ohana_puna",
        "language": "en",
        "context": "voice_interface",
        "mode": "voice_first",
        "source": "ten_framework"
    },
    vessel_id=None
)
```

### Output: To Kokoro TTS

```python
{
  "text": "I'll help you find grants for elder care. Let me search for relevant opportunities in your area."
}
```

## Thread Safety

The bridge uses a **ThreadPoolExecutor** to handle Vessels processing:

- TEN event loop stays non-blocking (real-time audio can't be interrupted)
- Vessels processing (which may take seconds) runs in background thread
- Thread pool size: 4 workers (configurable)
- Responses sent back to TEN event loop via `ten_env.send_data()`

## Session Management

The bridge maintains session continuity:

```python
# Session ID preserved across multiple turns
context["session_id"] = self.session_id

# Updated after each Vessels response
self.session_id = response.get("session_id")
```

This allows Agent Zero to maintain conversational context.

## Error Handling

- **Empty transcriptions**: Silently ignored
- **Interim results**: Filtered (only `is_final=true` processed)
- **Vessels errors**: Caught, logged, fallback message sent to user
- **TTS send errors**: Logged but don't crash extension

## Usage

### 1. Deploy TEN Graph

```bash
# From Vessels root directory
ten_framework run --graph graphs/vessels_edge_agent.json
```

### 2. Connect Client

Use TEN client SDK or Agora RTC client to connect to the agent.

### 3. Speak

Talk to the agent! Your voice is:
1. Transcribed by Whisper
2. Processed by Vessels agents
3. Synthesized by Kokoro
4. Played back to you

## Development

### Testing the Extension

```python
# Test VesselsInterface integration
python3 -c "
from vessels_interface import vessels_interface

response = vessels_interface.process_message(
    user_id='test_user',
    message='Find grants for elder care',
    context={'mode': 'voice_first'}
)

print(response['response'])
"
```

### Debugging

Set `LOG_LEVEL=debug` to see detailed flow:

```bash
export LOG_LEVEL=debug
ten_framework run --graph graphs/vessels_edge_agent.json
```

Look for:
- `"Received text_data: text='...', is_final=True"`
- `"Calling VesselsInterface.process_message"`
- `"Vessels response: '...'"`
- `"Sending text to TTS"`

## Future Enhancements

1. **Emotional TTS Adaptation**
   - Detect user emotion from Vessels context
   - Adapt TTS voice parameters (speed, pitch, energy)
   - Use `VesselsTTS.adapt_to_emotion()`

2. **Interruption Handling**
   - Allow user to interrupt agent mid-response
   - Cancel pending TTS synthesis
   - Clear response queue

3. **Multi-User Support**
   - Handle multiple concurrent users
   - Separate session contexts
   - Resource pooling

4. **Metrics & Monitoring**
   - Track latency (STT → Vessels → TTS)
   - Monitor agent performance
   - Export telemetry

## License

Apache 2.0 (same as Vessels platform)

## References

- [TEN Framework Documentation](https://github.com/TEN-framework/TEN-framework)
- [Vessels Platform](https://github.com/ohana-garden/Vessels)
- [Whisper.cpp](https://github.com/ggerganov/whisper.cpp)
- [Kokoro-82M TTS](https://huggingface.co/hexgrad/Kokoro-82M)
- [Agora RTC](https://docs.agora.io/)
