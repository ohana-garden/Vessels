"""
Unit tests for CRDT module.

Tests cover:
- Vector Clock causality tracking
- LWW-Element-Set memory operations
- G-Counter and PN-Counter for Kala
- Sync protocol delta generation/application
"""

import pytest
from datetime import datetime, timedelta
import time

from vessels.crdt.vector_clock import VectorClock, Timestamp
from vessels.crdt.memory import LWWElementSet, CRDTMemory, CRDTElement
from vessels.crdt.kala import GCounter, PNCounter, CRDTKalaAccount
from vessels.crdt.sync import SyncProtocol, Delta, SyncState


class TestVectorClock:
    """Test vector clock causality tracking."""

    def test_initialization(self):
        """Test vector clock initializes correctly."""
        vc = VectorClock(node_id="node1")
        assert vc.node_id == "node1"
        assert vc.clock["node1"] == 0

    def test_increment(self):
        """Test local clock increment."""
        vc = VectorClock(node_id="node1")
        vc.increment()
        assert vc.clock["node1"] == 1
        vc.increment()
        assert vc.clock["node1"] == 2

    def test_update_from_message(self):
        """Test clock update on message receive."""
        vc1 = VectorClock(node_id="node1")
        vc2 = VectorClock(node_id="node2")

        vc1.increment()  # node1: {node1: 1}
        vc2.increment()  # node2: {node2: 1}
        vc2.increment()  # node2: {node2: 2}

        # node1 receives message from node2
        vc1.update(vc2.to_dict())

        # Should have max of each component + local increment
        assert vc1.clock["node1"] == 2  # max(1, 0) + 1
        assert vc1.clock["node2"] == 2  # max(0, 2)

    def test_happens_before(self):
        """Test causality detection."""
        vc1 = VectorClock(node_id="node1")
        vc2 = VectorClock(node_id="node1")

        vc1.increment()  # {node1: 1}
        vc2.clock = vc1.to_dict()  # Copy state
        vc2.increment()  # {node1: 2}

        assert vc1.happens_before(vc2)
        assert not vc2.happens_before(vc1)

    def test_concurrent_events(self):
        """Test concurrent event detection."""
        vc1 = VectorClock(node_id="node1")
        vc2 = VectorClock(node_id="node2")

        vc1.increment()  # {node1: 1, node2: 0}
        vc2.increment()  # {node1: 0, node2: 1}

        assert vc1.concurrent_with(vc2)
        assert vc2.concurrent_with(vc1)
        assert not vc1.happens_before(vc2)
        assert not vc2.happens_before(vc1)

    def test_timestamp_ordering(self):
        """Test timestamp total ordering."""
        vc1 = VectorClock(node_id="node1")
        vc2 = VectorClock(node_id="node2")

        vc1.increment()
        time.sleep(0.01)  # Ensure different wall-clock times
        vc2.increment()

        ts1 = vc1.get_timestamp()
        ts2 = vc2.get_timestamp()

        # Concurrent events ordered by wall-clock time
        assert ts1 < ts2


class TestLWWElementSet:
    """Test Last-Write-Wins Element Set."""

    def test_add_element(self):
        """Test adding elements."""
        lww = LWWElementSet(node_id="node1")

        lww.add("key1", "value1")
        assert lww.get("key1") == "value1"
        assert lww.contains("key1")

    def test_update_element(self):
        """Test updating elements."""
        lww = LWWElementSet(node_id="node1")

        lww.add("key1", "value1")
        time.sleep(0.01)  # Ensure different timestamp
        lww.add("key1", "value2")

        assert lww.get("key1") == "value2"

    def test_remove_element(self):
        """Test element removal (tombstone)."""
        lww = LWWElementSet(node_id="node1")

        lww.add("key1", "value1")
        lww.remove("key1")

        assert not lww.contains("key1")
        assert lww.get("key1") is None

    def test_merge_no_conflicts(self):
        """Test merging without conflicts."""
        lww1 = LWWElementSet(node_id="node1")
        lww2 = LWWElementSet(node_id="node2")

        lww1.add("key1", "value1")
        lww2.add("key2", "value2")

        merged = lww1.merge(lww2)

        assert merged.get("key1") == "value1"
        assert merged.get("key2") == "value2"

    def test_merge_with_conflicts(self):
        """Test merging with conflicts (LWW resolution)."""
        lww1 = LWWElementSet(node_id="node1")
        lww2 = LWWElementSet(node_id="node2")

        lww1.add("key1", "value_from_node1")
        time.sleep(0.01)
        lww2.add("key1", "value_from_node2")

        merged = lww1.merge(lww2)

        # node2's write happened later, should win
        assert merged.get("key1") == "value_from_node2"

    def test_merge_tombstone_wins(self):
        """Test that deletion (tombstone) wins over old writes."""
        lww1 = LWWElementSet(node_id="node1")
        lww2 = LWWElementSet(node_id="node2")

        lww1.add("key1", "value1")
        time.sleep(0.01)
        lww2.remove("key1")  # Later deletion

        merged = lww1.merge(lww2)

        assert not merged.contains("key1")

    def test_merge_commutativity(self):
        """Test merge is commutative: merge(A, B) = merge(B, A)."""
        lww1 = LWWElementSet(node_id="node1")
        lww2 = LWWElementSet(node_id="node2")

        lww1.add("key1", "value1")
        lww2.add("key2", "value2")

        merged_ab = lww1.merge(lww2)
        merged_ba = lww2.merge(lww1)

        assert merged_ab.get("key1") == merged_ba.get("key1")
        assert merged_ab.get("key2") == merged_ba.get("key2")

    def test_merge_associativity(self):
        """Test merge is associative: merge(merge(A,B),C) = merge(A,merge(B,C))."""
        lww1 = LWWElementSet(node_id="node1")
        lww2 = LWWElementSet(node_id="node2")
        lww3 = LWWElementSet(node_id="node3")

        lww1.add("key1", "value1")
        lww2.add("key2", "value2")
        lww3.add("key3", "value3")

        merged_left = lww1.merge(lww2).merge(lww3)
        merged_right = lww1.merge(lww2.merge(lww3))

        assert set(merged_left.keys()) == set(merged_right.keys())
        for key in merged_left.keys():
            assert merged_left.get(key) == merged_right.get(key)

    def test_merge_idempotence(self):
        """Test merge is idempotent: merge(A, A) = A."""
        lww = LWWElementSet(node_id="node1")
        lww.add("key1", "value1")

        merged = lww.merge(lww)

        assert merged.get("key1") == lww.get("key1")
        assert len(merged) == len(lww)

    def test_serialization(self):
        """Test serialization to/from dict."""
        lww = LWWElementSet(node_id="node1")
        lww.add("key1", "value1")
        lww.add("key2", "value2")

        data = lww.to_dict()
        restored = LWWElementSet.from_dict(data)

        assert restored.get("key1") == "value1"
        assert restored.get("key2") == "value2"


class TestCRDTMemory:
    """Test CRDT-backed memory storage."""

    def test_store_and_retrieve_memory(self):
        """Test basic memory operations."""
        memory = CRDTMemory(node_id="node1")

        memory_data = {
            "type": "experience",
            "content": "Food distribution successful",
            "timestamp": datetime.utcnow().isoformat()
        }

        memory.store_memory("mem1", memory_data)
        retrieved = memory.get_memory("mem1")

        assert retrieved == memory_data

    def test_merge_memories(self):
        """Test merging memories from different nodes."""
        memory1 = CRDTMemory(node_id="node1")
        memory2 = CRDTMemory(node_id="node2")

        memory1.store_memory("mem1", {"content": "Memory from node1"})
        memory2.store_memory("mem2", {"content": "Memory from node2"})

        merged = memory1.merge_with(memory2)

        assert merged.get_memory("mem1") is not None
        assert merged.get_memory("mem2") is not None

    def test_delete_memory(self):
        """Test memory deletion."""
        memory = CRDTMemory(node_id="node1")

        memory.store_memory("mem1", {"content": "Test"})
        memory.delete_memory("mem1")

        assert memory.get_memory("mem1") is None


class TestGCounter:
    """Test Grow-only Counter."""

    def test_increment(self):
        """Test counter increment."""
        counter = GCounter(node_id="node1")

        counter.increment(5.0)
        assert counter.value() == 5.0

        counter.increment(3.0)
        assert counter.value() == 8.0

    def test_negative_increment_fails(self):
        """Test that negative increments are rejected."""
        counter = GCounter(node_id="node1")

        with pytest.raises(ValueError):
            counter.increment(-1.0)

    def test_merge(self):
        """Test merging counters."""
        counter1 = GCounter(node_id="node1")
        counter2 = GCounter(node_id="node2")

        counter1.increment(10.0)
        counter2.increment(5.0)

        merged = counter1.merge(counter2)

        assert merged.value() == 15.0

    def test_merge_takes_max_per_node(self):
        """Test merge takes max increment per node."""
        counter1 = GCounter(node_id="node1")
        counter2 = GCounter(node_id="node1")  # Same node ID

        counter1.increment(10.0)
        counter2.increment(5.0)

        merged = counter1.merge(counter2)

        # Should take max(10, 5) = 10, not sum
        assert merged.value() == 10.0

    def test_merge_commutativity(self):
        """Test merge is commutative."""
        counter1 = GCounter(node_id="node1")
        counter2 = GCounter(node_id="node2")

        counter1.increment(10.0)
        counter2.increment(5.0)

        assert counter1.merge(counter2).value() == counter2.merge(counter1).value()


class TestPNCounter:
    """Test Positive-Negative Counter."""

    def test_increment_and_decrement(self):
        """Test increment and decrement."""
        counter = PNCounter(node_id="node1")

        counter.increment(10.0)
        assert counter.value() == 10.0

        counter.decrement(3.0)
        assert counter.value() == 7.0

    def test_merge(self):
        """Test merging PN counters."""
        counter1 = PNCounter(node_id="node1")
        counter2 = PNCounter(node_id="node2")

        counter1.increment(10.0)
        counter1.decrement(2.0)

        counter2.increment(5.0)
        counter2.decrement(1.0)

        merged = counter1.merge(counter2)

        # (10 + 5) - (2 + 1) = 12
        assert merged.value() == 12.0


class TestCRDTKalaAccount:
    """Test CRDT-backed Kala account."""

    def test_credit_and_balance(self):
        """Test crediting Kala."""
        account = CRDTKalaAccount("user1", node_id="node1")

        account.credit(10.0, "Time contribution")
        assert account.balance() == 10.0

        account.credit(5.0, "Skill contribution")
        assert account.balance() == 15.0

    def test_debit_and_balance(self):
        """Test debiting Kala."""
        account = CRDTKalaAccount("user1", node_id="node1")

        account.credit(10.0, "Credit")
        account.debit(3.0, "Debit")

        assert account.balance() == 7.0

    def test_transaction_history(self):
        """Test transaction logging."""
        account = CRDTKalaAccount("user1", node_id="node1")

        account.credit(10.0, "Credit 1")
        account.debit(3.0, "Debit 1")
        account.credit(5.0, "Credit 2")

        history = account.transaction_history()

        assert len(history) == 3
        assert history[0].transaction_type == "credit"
        assert history[1].transaction_type == "debit"

    def test_merge_accounts(self):
        """Test merging Kala accounts."""
        account1 = CRDTKalaAccount("user1", node_id="node1")
        account2 = CRDTKalaAccount("user1", node_id="node2")

        account1.credit(10.0, "Node 1 credit")
        account2.credit(5.0, "Node 2 credit")

        merged = account1.merge_with(account2)

        assert merged.balance() == 15.0
        assert len(merged.transaction_history()) == 2

    def test_merge_different_accounts_fails(self):
        """Test that merging different accounts fails."""
        account1 = CRDTKalaAccount("user1", node_id="node1")
        account2 = CRDTKalaAccount("user2", node_id="node2")

        with pytest.raises(ValueError):
            account1.merge_with(account2)

    def test_serialization(self):
        """Test account serialization."""
        account = CRDTKalaAccount("user1", node_id="node1")
        account.credit(10.0, "Test credit")

        data = account.to_dict()
        restored = CRDTKalaAccount.from_dict(data)

        assert restored.balance() == account.balance()
        assert len(restored.transaction_history()) == len(account.transaction_history())


class TestSyncProtocol:
    """Test sync protocol."""

    def test_initialization(self):
        """Test sync protocol initialization."""
        protocol = SyncProtocol(node_id="node1")

        assert protocol.node_id == "node1"
        assert protocol.local_version["memory"] == 0
        assert protocol.local_version["kala"] == 0

    def test_generate_delta(self):
        """Test delta generation."""
        protocol = SyncProtocol(node_id="node1")

        # Increment version to simulate changes
        protocol.increment_version("memory")

        state = {"key1": "value1"}
        delta = protocol.generate_delta("node2", "memory", state)

        assert delta is not None
        assert delta.source_node_id == "node1"
        assert delta.target_node_id == "node2"
        assert delta.delta_type == "memory"
        assert delta.version == 1

    def test_no_delta_when_synced(self):
        """Test no delta generated when already synced."""
        protocol = SyncProtocol(node_id="node1")

        # Simulate prior sync
        protocol.version_vectors["node2"] = {"memory": 0}

        state = {"key1": "value1"}
        delta = protocol.generate_delta("node2", "memory", state)

        assert delta is None  # Already synced

    def test_increment_version(self):
        """Test version increment."""
        protocol = SyncProtocol(node_id="node1")

        assert protocol.local_version["memory"] == 0

        protocol.increment_version("memory")
        assert protocol.local_version["memory"] == 1

    def test_get_sync_state(self):
        """Test sync state checking."""
        protocol = SyncProtocol(node_id="node1")

        # Unsynced (never synced before)
        assert protocol.get_sync_state("node2", "memory") == SyncState.UNSYNCED

        # Synced
        protocol.version_vectors["node2"] = {"memory": 0}
        assert protocol.get_sync_state("node2", "memory") == SyncState.SYNCED

        # Unsynced (new changes)
        protocol.increment_version("memory")
        assert protocol.get_sync_state("node2", "memory") == SyncState.UNSYNCED

    def test_full_sync_required(self):
        """Test full sync detection."""
        protocol = SyncProtocol(node_id="node1")

        # Full sync required for new peer
        assert protocol.full_sync_required("node2")

        # Full sync NOT required after sync
        protocol.version_vectors["node2"] = {"memory": 0, "kala": 0}
        assert not protocol.full_sync_required("node2")

        # Full sync required if version gap too large
        protocol.local_version["memory"] = 150
        assert protocol.full_sync_required("node2")


class TestCRDTProperties:
    """Test CRDT mathematical properties."""

    def test_lww_eventual_consistency(self):
        """
        Test eventual consistency: If all updates stop,
        all replicas converge to same state.
        """
        lww1 = LWWElementSet(node_id="node1")
        lww2 = LWWElementSet(node_id="node2")
        lww3 = LWWElementSet(node_id="node3")

        # Simulate concurrent updates
        lww1.add("key1", "value_from_1")
        time.sleep(0.01)
        lww2.add("key2", "value_from_2")
        time.sleep(0.01)
        lww3.add("key3", "value_from_3")

        # Merge in different orders
        merged_123 = lww1.merge(lww2).merge(lww3)
        merged_321 = lww3.merge(lww2).merge(lww1)
        merged_213 = lww2.merge(lww1).merge(lww3)

        # All should converge to same state
        assert set(merged_123.keys()) == set(merged_321.keys()) == set(merged_213.keys())
        for key in merged_123.keys():
            assert merged_123.get(key) == merged_321.get(key) == merged_213.get(key)

    def test_gcounter_monotonicity(self):
        """Test G-Counter never decreases."""
        counter = GCounter(node_id="node1")

        values = []
        for i in range(10):
            counter.increment(1.0)
            values.append(counter.value())

        # Verify strictly increasing
        for i in range(1, len(values)):
            assert values[i] > values[i-1]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
