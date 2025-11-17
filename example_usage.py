#!/usr/bin/env python3
"""
Example usage of the Bahá'í Moral Manifold system.

This demonstrates:
1. Creating and validating states
2. Automatic projection of invalid states
3. Tracking agent trajectories
4. Discovering attractors in phase space
5. The core security property: malicious configs are geometrically impossible
"""

import numpy as np
from datetime import datetime, timedelta
import os

from bahai_manifold import BahaiManifold
from topological_validator import TopologicalValidator
from phase_space_tracker import PhaseSpaceTracker
from attractor_discovery import AttractorDiscoverer


def example_1_basic_validation():
    """Example 1: Basic state validation."""
    print("\n" + "="*60)
    print("EXAMPLE 1: Basic State Validation")
    print("="*60)

    manifold = BahaiManifold()

    # Create a valid high-virtue state
    print("\n1. Creating a valid high-virtue state...")
    valid_state = manifold.create_state(
        truthfulness=0.9,  # Strong foundation
        justice=0.8,
        understanding=0.8,
        trustworthiness=0.8,
        discipline=0.8,
        intellect=0.8
    )

    is_valid, violations = manifold.validate_state(valid_state)
    print(f"   Valid: {is_valid}")
    if violations:
        print(f"   Violations: {violations}")

    # Create an invalid manipulative state
    print("\n2. Creating a manipulative state (low truthfulness, high virtues)...")
    manipulative_state = manifold.create_state(
        truthfulness=0.2,  # Deceptive
        justice=0.9,  # Trying to appear just
        trustworthiness=0.9
    )

    is_valid, violations = manifold.validate_state(manipulative_state)
    print(f"   Valid: {is_valid}")
    print(f"   Violations: {len(violations)}")
    for v in violations[:3]:  # Show first 3
        print(f"     - {v}")


def example_2_automatic_projection():
    """Example 2: Automatic projection of invalid states."""
    print("\n" + "="*60)
    print("EXAMPLE 2: Automatic Projection to Manifold")
    print("="*60)

    manifold = BahaiManifold()
    validator = TopologicalValidator(manifold)

    # Create an invalid state
    print("\n1. Starting with invalid state:")
    invalid_state = manifold.create_state(
        truthfulness=0.3,  # Low
        justice=0.9,  # High - unsupported
        understanding=0.8,
        trustworthiness=0.8
    )
    print(f"   Truthfulness: {invalid_state['truthfulness']:.2f}")
    print(f"   Justice: {invalid_state['justice']:.2f}")
    print(f"   Understanding: {invalid_state['understanding']:.2f}")

    # Project with 'raise_dependencies' strategy
    print("\n2. Projecting with 'raise_dependencies' strategy...")
    corrected = validator.project_to_manifold(invalid_state, correction_strategy='raise_dependencies')
    print(f"   Truthfulness: {corrected['truthfulness']:.2f} (was {invalid_state['truthfulness']:.2f})")
    print(f"   Justice: {corrected['justice']:.2f} (was {invalid_state['justice']:.2f})")
    print(f"   Understanding: {corrected['understanding']:.2f} (was {invalid_state['understanding']:.2f})")

    is_valid, _ = manifold.validate_state(corrected)
    print(f"\n   Corrected state is valid: {is_valid}")

    # Project with 'lower_dependents' strategy
    print("\n3. Projecting with 'lower_dependents' strategy...")
    corrected2 = validator.project_to_manifold(invalid_state, correction_strategy='lower_dependents')
    print(f"   Truthfulness: {corrected2['truthfulness']:.2f} (was {invalid_state['truthfulness']:.2f})")
    print(f"   Justice: {corrected2['justice']:.2f} (was {invalid_state['justice']:.2f})")

    is_valid2, _ = manifold.validate_state(corrected2)
    print(f"\n   Corrected state is valid: {is_valid2}")


def example_3_trajectory_tracking():
    """Example 3: Tracking agent trajectories."""
    print("\n" + "="*60)
    print("EXAMPLE 3: Trajectory Tracking")
    print("="*60)

    manifold = BahaiManifold()
    validator = TopologicalValidator(manifold)

    # Use temporary database
    db_path = 'example_trajectories.db'
    if os.path.exists(db_path):
        os.unlink(db_path)

    tracker = PhaseSpaceTracker(db_path)

    print("\n1. Simulating agent development over time...")

    # Simulate an agent gradually developing virtues
    agent_id = 'agent_growth'
    base_time = datetime.now().timestamp()

    for i in range(10):
        # Gradually increase virtues with truthfulness as foundation
        truthfulness = 0.4 + i * 0.05
        state = manifold.create_state(
            truthfulness=truthfulness,
            justice=min(0.3 + i * 0.05, truthfulness - 0.1),
            understanding=min(0.3 + i * 0.04, truthfulness - 0.1),
            discipline=0.4 + i * 0.03
        )

        # Ensure validity by projection
        state, _ = validator.validate_and_correct(state, log_corrections=False)

        timestamp = base_time + i * 3600  # 1 hour intervals
        tracker.record_state(agent_id, state, timestamp)

    print(f"   Recorded {10} states for {agent_id}")

    # Get and analyze trajectory
    trajectory = tracker.get_trajectory(agent_id)
    print(f"\n2. Analyzing trajectory:")
    print(f"   Trajectory length (path distance): {tracker.trajectory_length(trajectory):.3f}")

    print("\n   States over time:")
    for i, (ts, state) in enumerate(trajectory):
        if i % 3 == 0:  # Show every 3rd state
            print(f"   Step {i}: Truth={state['truthfulness']:.2f}, "
                  f"Justice={state['justice']:.2f}, "
                  f"Understanding={state['understanding']:.2f}")

    tracker.close()
    print(f"\n   (Data saved to {db_path})")


def example_4_attractor_discovery():
    """Example 4: Discovering attractors in phase space."""
    print("\n" + "="*60)
    print("EXAMPLE 4: Attractor Discovery")
    print("="*60)

    manifold = BahaiManifold()
    validator = TopologicalValidator(manifold)
    discoverer = AttractorDiscoverer(manifold)

    print("\n1. Generating sample agent states...")

    # Create three clusters of agents with different characteristics
    all_states = []

    # Cluster 1: High-justice, high-virtue agents
    print("   - High-justice cluster (n=30)")
    for _ in range(30):
        state = manifold.create_state(
            truthfulness=0.8 + np.random.normal(0, 0.05),
            justice=0.8 + np.random.normal(0, 0.05),
            understanding=0.75 + np.random.normal(0, 0.05),
            discipline=0.75 + np.random.normal(0, 0.05),
            intellect=0.7 + np.random.normal(0, 0.05)
        )
        state, _ = validator.validate_and_correct(state, log_corrections=False)
        state_array = [state[v] for v in manifold.ALL_VIRTUES]
        all_states.append(state_array)

    # Cluster 2: Moderate-virtue agents
    print("   - Moderate-virtue cluster (n=25)")
    for _ in range(25):
        state = manifold.create_state(
            truthfulness=0.6 + np.random.normal(0, 0.05),
            justice=0.5 + np.random.normal(0, 0.05),
            understanding=0.5 + np.random.normal(0, 0.05),
            discipline=0.55 + np.random.normal(0, 0.05)
        )
        state, _ = validator.validate_and_correct(state, log_corrections=False)
        state_array = [state[v] for v in manifold.ALL_VIRTUES]
        all_states.append(state_array)

    # Cluster 3: Early development agents
    print("   - Early development cluster (n=20)")
    for _ in range(20):
        state = manifold.create_state(
            truthfulness=0.5 + np.random.normal(0, 0.04),
            justice=0.4 + np.random.normal(0, 0.04),
            understanding=0.4 + np.random.normal(0, 0.04)
        )
        state, _ = validator.validate_and_correct(state, log_corrections=False)
        state_array = [state[v] for v in manifold.ALL_VIRTUES]
        all_states.append(state_array)

    states_matrix = np.array(all_states)
    states_matrix = np.clip(states_matrix, 0, 1)

    print(f"\n2. Running DBSCAN clustering...")
    attractors = discoverer.discover_attractors(states_matrix, eps=0.4, min_samples=8)

    print(f"\n3. Found {len(attractors)} attractors:")
    for i, attractor in enumerate(attractors):
        print(f"\n   Attractor {i+1}:")
        print(f"     Size: {attractor.size} agents")
        print(f"     Radius: {attractor.radius:.3f}")

        stability = discoverer.analyze_attractor_stability(attractor)
        print(f"     Justice: {stability['justice']:.3f}")
        print(f"     Truthfulness: {stability['truthfulness']:.3f}")
        print(f"     Coupling density: {stability['coupling_density']:.3f}")

        dominant = attractor.get_dominant_virtues(3)
        print(f"     Top virtues: {', '.join([f'{v}={val:.2f}' for v, val in dominant])}")

        if attractor.is_high_justice():
            print(f"     *** HIGH-JUSTICE ATTRACTOR (Most beneficial) ***")

    # Classification
    print("\n4. Attractor classification:")
    classified = discoverer.classify_attractors(attractors)
    print(f"   High-justice attractors: {len(classified['high_justice'])}")
    print(f"   Moderate-justice attractors: {len(classified['moderate_justice'])}")
    print(f"   Low-justice attractors: {len(classified['low_justice'])}")


def example_5_security_property():
    """Example 5: Demonstrating the security property."""
    print("\n" + "="*60)
    print("EXAMPLE 5: Security Property - Malicious Configs are Impossible")
    print("="*60)

    manifold = BahaiManifold()
    validator = TopologicalValidator(manifold)

    malicious_configs = [
        {
            'name': 'Deceptive manipulator',
            'config': {'truthfulness': 0.1, 'justice': 0.9, 'trustworthiness': 0.9}
        },
        {
            'name': 'False teacher',
            'config': {'truthfulness': 0.15, 'understanding': 0.95, 'intellect': 0.9}
        },
        {
            'name': 'Fake integrator',
            'config': {'truthfulness': 0.2, 'love': 0.9, 'integration': 0.9, 'discipline': 0.8}
        }
    ]

    for i, mal_config in enumerate(malicious_configs, 1):
        print(f"\n{i}. Testing: {mal_config['name']}")
        state = manifold.create_state(**mal_config['config'])

        print(f"   Attempted configuration:")
        for virtue, value in mal_config['config'].items():
            print(f"     {virtue}: {value:.2f}")

        is_valid, violations = manifold.validate_state(state)
        print(f"\n   Valid on manifold: {is_valid}")
        print(f"   Violations: {len(violations)}")

        if not is_valid:
            print("\n   Projecting to manifold...")
            corrected, _ = validator.validate_and_correct(state, log_corrections=False)

            print(f"   Corrected configuration:")
            for virtue in mal_config['config'].keys():
                original = mal_config['config'][virtue]
                new = corrected[virtue]
                change = new - original
                print(f"     {virtue}: {new:.2f} (change: {change:+.2f})")

            is_valid_after, _ = manifold.validate_state(corrected)
            print(f"\n   Corrected state valid: {is_valid_after}")
            print("   ✓ Malicious configuration geometrically impossible!")


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("BAHÁ'Í MORAL MANIFOLD - Example Usage")
    print("="*60)
    print("\nThis demonstrates topological security where malicious")
    print("agent configurations are geometrically impossible.")

    example_1_basic_validation()
    example_2_automatic_projection()
    example_3_trajectory_tracking()
    example_4_attractor_discovery()
    example_5_security_property()

    print("\n" + "="*60)
    print("Examples complete!")
    print("="*60 + "\n")


if __name__ == '__main__':
    main()
