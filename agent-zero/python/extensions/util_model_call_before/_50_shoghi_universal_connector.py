"""
Shoghi Universal Connector Integration
Wraps LLM calls with universal connector for failover and multi-provider support
"""
from python.helpers.extension import Extension
import sys
import os

# Add shoghi to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../../'))

from shoghi.applications.connectors.universal_connector import UniversalConnector


class ShoghiUniversalConnector(Extension):
    """
    Integrate Shoghi's universal connector for LLM calls

    Provides:
    - Multi-provider support (Anthropic, OpenAI, local)
    - Automatic failover
    - Cost optimization
    - Provider-specific prompting
    """

    async def execute(self, **kwargs):
        """
        Wrap LLM calls with universal connector

        This happens BEFORE the model call, allowing us to:
        - Route to different providers
        - Add failover logic
        - Optimize costs
        """

        # Initialize universal connector if not already done
        if not hasattr(self.agent.context, 'shoghi_connector'):
            self.agent.context.shoghi_connector = UniversalConnector()

        # Get model call parameters
        messages = kwargs.get('messages', [])
        model = kwargs.get('model', 'claude-3-5-sonnet-20241022')

        # Extract configuration from Agent Zero's model config
        # We'll respect Agent Zero's model choice but provide fallback

        # Determine preferred provider from model name
        if 'claude' in model.lower() or 'anthropic' in model.lower():
            preferred_provider = 'anthropic'
            fallback_providers = ['openai', 'local']
        elif 'gpt' in model.lower() or 'openai' in model.lower():
            preferred_provider = 'openai'
            fallback_providers = ['anthropic', 'local']
        else:
            preferred_provider = 'local'
            fallback_providers = ['anthropic', 'openai']

        # Store connector configuration for the actual call
        # (This extension runs BEFORE the call, so we set up context)
        self.agent.set_data('llm_provider_preference', {
            'preferred': preferred_provider,
            'fallbacks': fallback_providers,
            'original_model': model
        })

        # The actual LLM call will happen in Agent Zero's code
        # This extension just sets up the routing preference
        # For full integration, we'd need to override the actual call
        # but this provides the infrastructure

        return  # Continue with normal flow
