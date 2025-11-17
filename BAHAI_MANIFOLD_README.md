# Bahá'í Moral Manifold System

A topological security system for agent coordination where malicious configurations are **geometrically impossible** rather than explicitly forbidden.

## Core Concept

Traditional security systems use rules to prohibit malicious behavior. This system uses **differential geometry** - malicious states cannot exist because they violate the topology of a 14-dimensional Riemannian manifold based on Bahá'í virtues.

### Key Insight

**Manipulation requires deception** (low truthfulness), but the manifold's topology makes it impossible to maintain high virtues without high truthfulness. This is enforced by the manifold's coupling constraints, not by explicit rules.

## Architecture

### The 14-Dimensional Manifold

**Seven Valleys virtues:**
- Patience, Yearning, Understanding, Detachment, Independence, Awe, Humility

**Four Valleys virtues:**
- Discipline, Intellect, Love, Integration

**Hierarchical virtues (from Bahá'í writings):**
- **Justice** - "most beloved of all things" - Hub node with maximum coupling connectivity
- **Truthfulness** - Foundation - Load-bearing dimension that supports all others
- **Trustworthiness** - "supreme instrument" - Bridge connecting personal to social virtues

### Topological Structure

The hierarchy emerges from **topology**, not arithmetic:

1. **Truthfulness is load-bearing**: Other virtues collapse geometrically without sufficient truthfulness
   - Virtues > 0.6 require Truthfulness ≥ 0.5
   - Virtues > 0.8 require Truthfulness ≥ 0.7

2. **Justice is a hub**: Maximum coupling connectivity creates natural stability
   - Justice > 0.7 requires Truthfulness ≥ 0.7 AND Understanding ≥ 0.6

3. **Trustworthiness is a bridge**: Connects personal spiritual development to social action
   - Trustworthiness > 0.6 requires Truthfulness ≥ 0.5 AND Discipline ≥ 0.5

4. **Standard couplings** create the basic manifold topology:
   - Understanding > 0.7 requires Intellect ≥ 0.6
   - Integration > 0.7 requires Love ≥ 0.6, Discipline ≥ 0.6, AND Intellect ≥ 0.6
   - Detachment > 0.6 requires Independence ≥ 0.5
   - Humility > 0.6 requires Awe ≥ 0.5
   - Yearning > 0.6 requires Patience ≥ 0.5
   - Understanding > 0.6 requires Detachment ≥ 0.5

## Security Property

**Malicious configurations are geometrically impossible:**

```python
# This configuration CANNOT exist on the manifold
manipulation_state = {
    'truthfulness': 0.2,  # Deceptive
    'justice': 0.9,       # Trying to appear just
    'trustworthiness': 0.9  # Trying to appear trustworthy
}

is_valid, violations = manifold.validate_state(manipulation_state)
# is_valid = False
# Multiple violations of topological constraints

# Automatic projection to nearest valid point
corrected = validator.project_to_manifold(manipulation_state)
# Either truthfulness increases OR virtues decrease
# The manipulative configuration is geometrically impossible
```

## Components

### 1. BahaiManifold (`bahai_manifold.py`)

Defines the 14-dimensional manifold and validates states against topological constraints.

```python
from bahai_manifold import BahaiManifold

manifold = BahaiManifold()

# Create a state
state = manifold.create_state(
    truthfulness=0.8,
    justice=0.7,
    understanding=0.7
)

# Validate
is_valid, violations = manifold.validate_state(state)
```

### 2. TopologicalValidator (`topological_validator.py`)

Projects invalid states to the nearest valid point on the manifold.

```python
from topological_validator import TopologicalValidator

validator = TopologicalValidator(manifold)

# Automatically correct invalid states
corrected, was_corrected = validator.validate_and_correct(state)
```

**Correction strategies:**
- `raise_dependencies`: Raise prerequisite virtues to support high virtues
- `lower_dependents`: Lower virtues that lack foundation
- `balanced`: Minimize total change

### 3. PhaseSpaceTracker (`phase_space_tracker.py`)

Tracks agent trajectories through the 14D space over time using SQLite.

```python
from phase_space_tracker import PhaseSpaceTracker

tracker = PhaseSpaceTracker('trajectories.db')

# Record states
tracker.record_state(agent_id, state, timestamp)

# Retrieve trajectory
trajectory = tracker.get_trajectory(agent_id)

# Calculate path length
length = tracker.trajectory_length(trajectory)
```

### 4. AttractorDiscoverer (`attractor_discovery.py`)

Discovers stable regions (attractors) using DBSCAN clustering.

```python
from attractor_discovery import AttractorDiscoverer

discoverer = AttractorDiscoverer(manifold, tracker)

# Discover attractors
attractors = discoverer.discover_from_tracker(eps=0.3, min_samples=5)

# Classify by justice level
classified = discoverer.classify_attractors(attractors)
high_justice = classified['high_justice']  # Most beneficial

# Analyze stability
for attractor in attractors:
    metrics = discoverer.analyze_attractor_stability(attractor)
    print(f"Justice: {metrics['justice']:.2f}")
    print(f"Coupling density: {metrics['coupling_density']:.2f}")
```

## Installation

```bash
pip install numpy scikit-learn
```

## Usage

### Basic Example

```python
from bahai_manifold import BahaiManifold
from topological_validator import TopologicalValidator

# Create manifold
manifold = BahaiManifold()
validator = TopologicalValidator(manifold)

# Attempt to create a manipulative state
state = manifold.create_state(
    truthfulness=0.1,  # Deceptive
    justice=0.9        # Trying to appear just
)

# Validate - this WILL fail
is_valid, violations = manifold.validate_state(state)
print(f"Valid: {is_valid}")  # False

# Automatically project to valid configuration
corrected = validator.project_to_manifold(state)
print(f"Corrected truthfulness: {corrected['truthfulness']:.2f}")
print(f"Corrected justice: {corrected['justice']:.2f}")
```

### Running Examples

```bash
# Run comprehensive examples
python example_usage.py

# Run tests
pytest test_bahai_manifold.py -v
```

## How It Works

### Topological vs. Weighted Metrics

**Traditional approach (weighted metrics):**
```python
# Explicit weighting - can be gamed
score = 0.5 * truthfulness + 0.3 * justice + 0.2 * love
if score > threshold:
    allow_action()
```

**Topological approach (this system):**
```python
# Geometric constraints - cannot be gamed
if justice > 0.7:
    requires(truthfulness >= 0.7 AND understanding >= 0.6)
# Violating this creates an impossible geometry
```

### Why Manipulation Fails

1. **Manipulation requires deception** → Low truthfulness
2. **Low truthfulness violates foundation constraints** → Cannot support high virtues
3. **System automatically projects to valid state** → Either truthfulness increases OR virtues decrease
4. **Geometric impossibility** → Cannot maintain deception + high virtues

### Emergent Hierarchy

The importance of virtues emerges from topology:

- **Truthfulness** has the most dependencies → Load-bearing
- **Justice** has the most couplings → Hub (naturally stable)
- **Trustworthiness** connects personal to social → Bridge

This hierarchy is discovered, not imposed.

### Attractors

High-Justice states form strong attractors because:
1. Justice requires many supporting virtues (hub structure)
2. These virtues reinforce each other through couplings
3. The manifold topology creates a "basin" around high-justice states
4. Agents naturally evolve toward these stable configurations

## Mathematical Foundation

### Manifold Definition

M = {s ∈ ℝ¹⁴ | 0 ≤ sᵢ ≤ 1, C(s) = true}

Where C(s) are the coupling constraints.

### Distance Metric

Standard Euclidean distance (NO weighted metrics):

d(s₁, s₂) = √(Σᵢ(s₁ᵢ - s₂ᵢ)²)

### Projection Algorithm

For invalid state s:
1. Check Truthfulness foundation constraints
2. Check Justice hub constraints
3. Check Trustworthiness bridge constraints
4. Check standard couplings
5. Iterate until valid or max iterations

## Design Principles

1. **Threshold-based, not weighted** - Boolean geometry, not arithmetic
2. **Topology encodes security** - Malicious states are geometrically impossible
3. **Hierarchy emerges** - From coupling structure, not explicit ranking
4. **No explicit rules** - Security is a property of the space itself
5. **Attractors are discovered** - Not predetermined

## Applications

### Agent Coordination

- **Coordination platform**: Agents must maintain valid manifold states
- **Automatic correction**: Invalid states projected to nearest valid point
- **Trajectory analysis**: Track agent development over time
- **Attractor guidance**: Guide agents toward beneficial attractors

### Security

- **Topological security**: Malicious configs geometrically impossible
- **No explicit rules**: Can't game what you can't see
- **Automatic enforcement**: Projection happens automatically
- **Audit trail**: All corrections logged as security events

### Analysis

- **Phase space visualization**: See agent populations in 14D space
- **Attractor discovery**: Find stable beneficial configurations
- **Trajectory clustering**: Group agents by development patterns
- **Emergence detection**: Identify new attractors as they form

## Testing

```bash
# Run all tests
pytest test_bahai_manifold.py -v

# Run specific test
pytest test_bahai_manifold.py::TestBahaiManifold::test_manipulation_state_is_invalid -v

# Run security property test
pytest test_bahai_manifold.py::test_security_property_integration -v
```

## Key Tests

- `test_manipulation_state_is_invalid`: Verifies malicious configs are invalid
- `test_truthfulness_foundation_violation`: Checks load-bearing property
- `test_projection_raises_truthfulness`: Tests automatic correction
- `test_security_property_integration`: End-to-end security verification

## Files

- `bahai_manifold.py` - Manifold definition and constraints (320 lines)
- `topological_validator.py` - Projection algorithm (420 lines)
- `phase_space_tracker.py` - Trajectory tracking with SQLite (280 lines)
- `attractor_discovery.py` - DBSCAN clustering and analysis (380 lines)
- `test_bahai_manifold.py` - Comprehensive tests (380 lines)
- `example_usage.py` - Usage examples (380 lines)

## License

Part of the Shoghi agent coordination platform.

## References

- Bahá'í writings on virtues and their relationships
- Riemannian geometry and manifold theory
- Topological data analysis and persistent homology
- DBSCAN clustering for attractor discovery

## Future Directions

1. **Geodesic paths**: Shortest paths between states on manifold
2. **Persistent homology**: Discover higher-dimensional holes in phase space
3. **Curvature analysis**: Identify regions of high/low curvature
4. **Dynamic constraints**: Constraints that evolve with context
5. **Multi-agent coupling**: Constraints between different agents
