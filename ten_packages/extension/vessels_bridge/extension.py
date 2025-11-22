#!/usr/bin/env python3
"""
Vessels Bridge Extension for TEN Framework

This extension bridges the TEN real-time audio graph with the Vessels agentic logic.
It receives transcribed text from STT, processes it through the Vessels interface,
and sends the response to TTS.

Flow:
  Agora RTC (Audio In) -> Whisper STT -> [Vessels Bridge] -> Kokoro TTS -> Agora RTC (Audio Out)
                                              ↓
                                      VesselsInterface
                                              ↓
                                      Action Gate / Agent Zero
"""

import asyncio
import logging
import sys
import os
from typing import Dict, Any, Optional
from pathlib import Path
import threading

# Add parent directories to path to import Vessels modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ten import (
    TenEnv,
    Cmd,
    Data,
    AudioFrame,
    VideoFrame,
)

# Import Vessels components
from vessels_interface import VesselsInterface

# Configure logging
logger = logging.getLogger(__name__)


class VesselsBridgeExtension(TenEnv):
    """
    TEN Extension that bridges real-time audio graph with Vessels agentic logic.

    This extension:
    1. Receives text_data from STT (Whisper)
    2. Passes text to VesselsInterface.process_message()
    3. Gets response from Vessels agents
    4. Sends response text to TTS (Kokoro)
    """

    def __init__(self, name: str):
        super().__init__(name)
        self.vessels_interface: Optional[VesselsInterface] = None
        self.user_id: str = "default_user"
        self.community_id: str = "default_community"
        self.vessel_id: str = ""
        self.context: str = "voice_interface"
        self.language: str = "en"
        self.session_id: Optional[str] = None

        # Thread pool for blocking operations
        self.executor = None

        logger.info(f"VesselsBridgeExtension initialized: {name}")

    def on_init(self, ten_env: TenEnv) -> None:
        """
        Called when extension is initialized.
        Load configuration properties.
        """
        logger.info("VesselsBridgeExtension.on_init called")
        ten_env.on_init_done()

    def on_start(self, ten_env: TenEnv) -> None:
        """
        Called when extension starts.
        Initialize VesselsInterface and read properties.
        """
        logger.info("VesselsBridgeExtension.on_start called")

        try:
            # Read properties from TEN environment
            self.user_id = ten_env.get_property_string("user_id") or "default_user"
            self.community_id = ten_env.get_property_string("community_id") or "default_community"
            self.vessel_id = ten_env.get_property_string("vessel_id") or ""
            self.context = ten_env.get_property_string("context") or "voice_interface"
            self.language = ten_env.get_property_string("language") or "en"

            # Set log level
            log_level = ten_env.get_property_string("log_level") or "info"
            logging.basicConfig(
                level=getattr(logging, log_level.upper(), logging.INFO),
                format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )

            logger.info(f"Configuration loaded: user_id={self.user_id}, "
                       f"community_id={self.community_id}, "
                       f"vessel_id={self.vessel_id}, "
                       f"context={self.context}, "
                       f"language={self.language}")

            # Initialize VesselsInterface
            self.vessels_interface = VesselsInterface()
            logger.info("VesselsInterface initialized successfully")

            # Create thread pool executor for blocking operations
            from concurrent.futures import ThreadPoolExecutor
            self.executor = ThreadPoolExecutor(max_workers=4)
            logger.info("Thread pool executor created")

            ten_env.on_start_done()
            logger.info("VesselsBridgeExtension started successfully")

        except Exception as e:
            logger.error(f"Error in on_start: {e}", exc_info=True)
            ten_env.on_start_done()

    def on_stop(self, ten_env: TenEnv) -> None:
        """
        Called when extension stops.
        Cleanup resources.
        """
        logger.info("VesselsBridgeExtension.on_stop called")

        try:
            # Shutdown vessels interface if it exists
            if self.vessels_interface:
                self.vessels_interface.shutdown()
                logger.info("VesselsInterface shutdown complete")

            # Shutdown executor
            if self.executor:
                self.executor.shutdown(wait=True)
                logger.info("Thread pool executor shutdown complete")

        except Exception as e:
            logger.error(f"Error in on_stop: {e}", exc_info=True)
        finally:
            ten_env.on_stop_done()

    def on_deinit(self, ten_env: TenEnv) -> None:
        """
        Called when extension is deinitialized.
        """
        logger.info("VesselsBridgeExtension.on_deinit called")
        ten_env.on_deinit_done()

    def on_cmd(self, ten_env: TenEnv, cmd: Cmd) -> None:
        """
        Handle incoming commands.

        Supports:
        - flush: Flush any pending state
        """
        cmd_name = cmd.get_name()
        logger.info(f"Received command: {cmd_name}")

        try:
            if cmd_name == "flush":
                # Flush any pending state
                logger.info("Flushing state")
                # Reset session if needed
                self.session_id = None

            # Send command result
            cmd_result = Cmd.create("response")
            cmd_result.set_property_string("status", "ok")
            ten_env.return_result(cmd_result, cmd)

        except Exception as e:
            logger.error(f"Error handling command {cmd_name}: {e}", exc_info=True)
            cmd_result = Cmd.create("response")
            cmd_result.set_property_string("status", "error")
            cmd_result.set_property_string("message", str(e))
            ten_env.return_result(cmd_result, cmd)

    def on_data(self, ten_env: TenEnv, data: Data) -> None:
        """
        Handle incoming data from STT.

        Expected data format from Whisper STT:
        {
            "text": "user's spoken message",
            "is_final": true/false,
            "stream_id": 12345,
            "end_of_segment": true/false
        }

        Only process when is_final=true to avoid processing interim results.
        """
        try:
            # Get data properties
            text = data.get_property_string("text")
            is_final = data.get_property_bool("is_final")

            logger.debug(f"Received text_data: text='{text}', is_final={is_final}")

            # Only process final transcriptions
            if not is_final:
                logger.debug("Skipping interim transcription")
                return

            # Validate text
            if not text or not text.strip():
                logger.debug("Empty text, skipping")
                return

            text = text.strip()
            logger.info(f"Processing final transcription: '{text}'")

            # Process the message through Vessels in a thread pool to avoid blocking
            # the real-time TEN event loop
            self.executor.submit(self._process_vessels_message, ten_env, text)

        except Exception as e:
            logger.error(f"Error in on_data: {e}", exc_info=True)

    def _process_vessels_message(self, ten_env: TenEnv, text: str) -> None:
        """
        Process message through Vessels interface.

        This runs in a thread pool to avoid blocking the TEN event loop.

        Args:
            ten_env: TEN environment
            text: User's message text
        """
        try:
            # Prepare context
            context = {
                "community_id": self.community_id,
                "language": self.language,
                "context": self.context,
                "mode": "voice_first",
                "source": "ten_framework"
            }

            # Add session_id to context for continuity
            if self.session_id:
                context["session_id"] = self.session_id

            logger.info(f"Calling VesselsInterface.process_message with user_id={self.user_id}")

            # Call Vessels interface
            # This may block while Agent Zero processes the request
            response = self.vessels_interface.process_message(
                user_id=self.user_id,
                message=text,
                context=context,
                vessel_id=self.vessel_id if self.vessel_id else None
            )

            # Extract response text
            response_text = response.get("response", "")

            if not response_text:
                logger.warning("Empty response from Vessels, using fallback")
                response_text = "I'm processing your request. One moment please."

            logger.info(f"Vessels response: '{response_text[:100]}...'")

            # Send response text to TTS
            self._send_text_to_tts(ten_env, response_text)

            # Update session_id if provided
            if "session_id" in response:
                self.session_id = response["session_id"]
                logger.debug(f"Updated session_id: {self.session_id}")

        except Exception as e:
            logger.error(f"Error processing Vessels message: {e}", exc_info=True)

            # Send error response to user
            error_text = "I encountered an issue processing your request. Please try again."
            self._send_text_to_tts(ten_env, error_text)

    def _send_text_to_tts(self, ten_env: TenEnv, text: str) -> None:
        """
        Send text data to TTS for speech synthesis.

        Args:
            ten_env: TEN environment
            text: Text to synthesize
        """
        try:
            logger.info(f"Sending text to TTS: '{text[:100]}...'")

            # Create text_data frame
            text_data = Data.create("text_data")
            text_data.set_property_string("text", text)

            # Send to next extension in graph (TTS)
            ten_env.send_data(text_data)

            logger.debug("Text sent to TTS successfully")

        except Exception as e:
            logger.error(f"Error sending text to TTS: {e}", exc_info=True)

    def on_audio_frame(self, ten_env: TenEnv, frame: AudioFrame) -> None:
        """
        Handle incoming audio frames.
        Not used in this extension (audio is handled by Agora RTC + STT).
        """
        pass

    def on_video_frame(self, ten_env: TenEnv, frame: VideoFrame) -> None:
        """
        Handle incoming video frames.
        Not used in this extension.
        """
        pass


# TEN Framework expects a register_addon_as_extension function
def register_addon_as_extension(ten_env: TenEnv) -> None:
    """
    Register this extension with TEN Framework.
    """
    logger.info("Registering VesselsBridgeExtension")
    ten_env.register_addon_as_extension("vessels_bridge", VesselsBridgeExtension)
