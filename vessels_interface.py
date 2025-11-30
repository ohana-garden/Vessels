#!/usr/bin/env python3
"""
VESSELS INTERFACE
Natural language interface for the Vessels platform.
All requests are processed through AgentZeroCore.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

from agent_zero_core import agent_zero
from community_memory import community_memory

logger = logging.getLogger(__name__)


class VesselsInterface:
    """
    Natural language interface for Vessels platform.

    All processing is delegated to AgentZeroCore (agent_zero).
    """

    def __init__(self, llm_call: Optional[callable] = None):
        """
        Initialize Vessels Interface.

        Args:
            llm_call: Optional function to call LLM. Signature: llm_call(prompt: str) -> str
        """
        self.llm_call = llm_call

        # Configure Agent Zero with LLM capability
        if self.llm_call:
            agent_zero.set_llm_call(self.llm_call)

        logger.info("VesselsInterface initialized with AgentZeroCore")

    def process(self, user_input: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Process user input through AgentZeroCore.

        Args:
            user_input: Natural language input from user
            user_id: User identifier

        Returns:
            Response dictionary with results
        """
        interaction_id = str(uuid.uuid4())

        try:
            # Process through Agent Zero
            result = agent_zero.process_request(user_input, user_id=user_id)

            # Store in community memory
            community_memory.store_experience(
                agent_id=user_id,
                experience={
                    "interaction_id": interaction_id,
                    "content": user_input,
                    "result": str(result)[:500],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )

            return {
                "id": interaction_id,
                "status": "success",
                "response": result,
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error processing request: {e}")
            return {
                "id": interaction_id,
                "status": "error",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }

    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "agent_zero": "active" if agent_zero.running else "idle",
            "agents": len(agent_zero.agents),
            "memory_entries": len(community_memory.memory_store)
        }


# Global instance
vessels_interface = VesselsInterface()
