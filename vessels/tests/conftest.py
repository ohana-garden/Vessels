"""
Pytest configuration and fixtures for Vessels tests.

Provides common fixtures for testing:
- Mock FalkorDB client for tests without real database
- Temporary registries for vessel tests
- Test vessels and contexts
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import MagicMock, patch
import os


# Set environment to allow testing without real FalkorDB
os.environ.setdefault("VESSELS_GRAPHITI_ALLOW_MOCK", "1")
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("ALLOW_INSECURE_JWT", "true")


class MockFalkorDBGraph:
    """Mock FalkorDB Graph for testing."""

    def __init__(self, name: str = "test_graph"):
        self.name = name
        self.nodes = {}
        self.queries_executed = []

    def query(self, cypher: str, params: dict = None):
        """Mock query execution."""
        self.queries_executed.append({"cypher": cypher, "params": params})

        # Return mock result set
        result = MagicMock()
        result.result_set = []
        return result


class MockFalkorDBClient:
    """Mock FalkorDB client for testing."""

    def __init__(self, host: str = "localhost", port: int = 6379, **kwargs):
        self.host = host
        self.port = port
        self._graphs = {}

    def get_graph(self, graph_name: str):
        """Get or create mock graph."""
        if graph_name not in self._graphs:
            self._graphs[graph_name] = MockFalkorDBGraph(graph_name)
        return self._graphs[graph_name]

    def health_check(self) -> bool:
        """Mock health check always returns True."""
        return True

    def create_indexes(self):
        """Mock index creation."""
        pass

    def close(self):
        """Mock close."""
        self._graphs.clear()


@pytest.fixture
def mock_falkordb():
    """Provide a mock FalkorDB client."""
    return MockFalkorDBClient()


@pytest.fixture
def mock_falkordb_patched(mock_falkordb):
    """Patch the global FalkorDB client getter."""
    with patch("vessels.database.falkordb_client.get_falkordb_client", return_value=mock_falkordb):
        with patch("vessels.database.falkordb_client.FalkorDBClient", return_value=mock_falkordb):
            yield mock_falkordb


@pytest.fixture
def temp_registry_dir():
    """Create temporary directory for test registry."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def sqlite_registry(temp_registry_dir):
    """Create SQLite-based vessel registry for testing."""
    from vessels.core import SQLiteVesselRegistry
    registry = SQLiteVesselRegistry(registry_dir=temp_registry_dir)
    yield registry
    registry.close()


@pytest.fixture
def mock_registry(mock_falkordb):
    """Create mock FalkorDB-based vessel registry for testing."""
    from vessels.core.falkordb_registry import FalkorDBVesselRegistry
    registry = FalkorDBVesselRegistry(falkor_client=mock_falkordb)
    return registry


@pytest.fixture
def test_vessel(sqlite_registry):
    """Create a test vessel."""
    vessel = sqlite_registry.create_vessel(
        name="Test Vessel",
        community_id="test_community",
        description="A test vessel for unit tests"
    )
    return vessel


@pytest.fixture
def test_context(sqlite_registry, test_vessel):
    """Create a test vessel context."""
    from vessels.core import VesselContext
    return VesselContext(vessel=test_vessel, registry=sqlite_registry)


@pytest.fixture
def mock_action_gate():
    """Create a mock action gate for testing."""
    gate = MagicMock()

    # Default to allowing actions
    result = MagicMock()
    result.allowed = True
    result.reason = "Test allowed"
    result.measured_state = MagicMock()
    result.measured_state.virtue = MagicMock()
    result.measured_state.virtue.to_dict.return_value = {
        "truthfulness": 0.8,
        "justice": 0.7,
        "service": 0.9
    }
    result.measured_state.operational = MagicMock()
    result.measured_state.operational.to_dict.return_value = {
        "activity": 0.6,
        "health": 0.9
    }

    gate.gate_action.return_value = result

    return gate


@pytest.fixture
def mock_community_memory():
    """Create a mock community memory for testing."""
    memory = MagicMock()
    memory.store_knowledge.return_value = "memory_123"
    memory.store_experience.return_value = "memory_456"
    memory.find_similar_memories.return_value = []
    return memory


@pytest.fixture
def sample_manifest_content():
    """Sample manifest content for testing."""
    return {
        "vessels": [
            {
                "id": "test_vessel_1",
                "name": "Test Vessel One",
                "description": "First test vessel",
                "community_ids": ["test_community"],
                "privacy_level": "private",
                "tier_config": {
                    "tier0_enabled": True,
                    "tier0_model": "Llama-3.2-1B",
                    "tier1_enabled": True,
                    "tier2_enabled": False
                }
            },
            {
                "id": "test_vessel_2",
                "name": "Test Vessel Two",
                "description": "Second test vessel",
                "community_ids": ["test_community"],
                "privacy_level": "shared"
            }
        ]
    }


@pytest.fixture
def sample_manifest_file(tmp_path, sample_manifest_content):
    """Create a sample manifest file for testing."""
    import yaml

    manifest_path = tmp_path / "test_manifest.yaml"
    with open(manifest_path, "w") as f:
        yaml.dump(sample_manifest_content, f)

    return manifest_path


# Async test support
@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()
