# Vessels Platform - Implementation Roadmap

**Version:** 2.0
**Date:** 2025-11-23
**Status:** APPROVED FOR IMPLEMENTATION

---

## Executive Summary

This roadmap provides a concrete, actionable plan for implementing the architecture improvements outlined in `docs/ARCHITECTURE_IMPROVEMENTS.md`, based on the feasibility analysis in `docs/FEASIBILITY_ANALYSIS.md`.

**Timeline:** 16 weeks (4 months)
**Team Size:** 2-3 developers (estimated)
**Priority:** Focus on P0 items (immediate value, high feasibility)

---

## Implementation Phases

### Phase 1: Immediate Wins (Weeks 1-6)

**Objective:** Deliver high-value, low-risk improvements that strengthen the platform's resilience, security, and usability.

**Deliverables:**
- ✅ CRDT-based offline-first memory
- ✅ Adversarially-tested constraint system
- ✅ Automated memory hygiene
- ✅ Quadratic funding allocation
- ✅ Ghost mode for safe agent deployment
- ✅ Visual policy editor for non-technical users

**Success Metrics:**
- Offline sync success rate >99.9%
- Adversarial block rate >95%
- Memory pollution rate <5% after 90 days
- Ghost mode coverage 100% for new agents

---

### Phase 2: Foundational Systems (Weeks 7-12)

**Objective:** Build trust infrastructure and advanced intelligence capabilities.

**Deliverables:**
- ✅ Cryptographic state proofs (software keys)
- ✅ Causal reasoning engine
- ✅ Dynamic constraint calibration
- ✅ Inter-community economic clearing

**Success Metrics:**
- 100% state transitions verifiable
- Causal query accuracy >70%
- Constraint calibration reduces false positives by 20%

---

### Phase 3: Federation & Advanced Features (Weeks 13+)

**Objective:** Enable peer-to-peer sovereignty and cryptographic privacy compliance.

**Deliverables:**
- ✅ Federated knowledge graphs
- ⏸️ Zero-knowledge proofs (research phase)

**Success Metrics:**
- Multi-node federation tested with 3+ communities
- Graph sync latency <5 seconds

---

## Sprint Breakdown

### Sprint 1-2: CRDT Foundation & Adversarial Testing (Weeks 1-2)

#### Sprint 1 (Week 1)

**Milestone:** CRDT Memory Implementation

**Tasks:**
1. **Create CRDT module structure**
   - `vessels/crdt/__init__.py`
   - `vessels/crdt/vector_clock.py`
   - `vessels/crdt/memory.py` (LWW-Element-Set)
   - `vessels/crdt/kala.py` (G-Counter)
   - Assignee: Developer A
   - Estimate: 2 days

2. **Implement LWW-Element-Set for memories**
   - Data structures: `CRDTElement`, `LWWElementSet`
   - Methods: `add()`, `remove()`, `merge()`
   - Unit tests (15+ tests)
   - Assignee: Developer A
   - Estimate: 3 days

3. **Implement G-Counter for Kala accounts**
   - Data structure: `CRDTKalaAccount`
   - Methods: `increment()`, `value()`, `merge()`
   - Unit tests (10+ tests)
   - Assignee: Developer B
   - Estimate: 2 days

4. **Create CRDT sync protocol**
   - `vessels/crdt/sync.py`
   - Methods: `generate_delta()`, `apply_delta()`, `full_sync()`
   - Assignee: Developer B
   - Estimate: 3 days

**Deliverables:**
- CRDT module with unit tests (25+ tests passing)
- Documentation in module docstrings

---

#### Sprint 2 (Week 2)

**Milestone:** Memory & Kala Integration + Adversarial Testing

**Tasks:**
1. **Integrate CRDT into CommunityMemory**
   - Modify `community_memory.py`:
     - Add `backend="crdt"` option
     - Implement `CRDTMemoryBackend` class
     - Migration script from SQLite to CRDT
   - Assignee: Developer A
   - Estimate: 3 days

2. **Integrate CRDT into Kala system**
   - Modify `kala.py`:
     - Add `use_crdt=True` option
     - Implement `CRDTKalaAccount` wrapper
   - Assignee: Developer A
   - Estimate: 2 days

3. **Create adversarial test suite**
   - `vessels/tests/adversarial/__init__.py`
   - `vessels/tests/adversarial/trickster_agents.py`
     - `ActivitySpammer`
     - `CoordinationManipulator`
     - `TruthfulnessGamer`
     - `ResourceHoarder`
     - `ServiceShirker`
   - Assignee: Developer B
   - Estimate: 3 days

4. **Run adversarial tests against constraints**
   - `vessels/tests/adversarial/test_gaming.py`
   - 20+ test scenarios
   - Fix any discovered loopholes
   - Assignee: Developer B
   - Estimate: 2 days

**Deliverables:**
- CRDT-backed memory and Kala ledgers
- Migration tooling
- Adversarial test suite (20+ tests)
- Loophole fixes (if discovered)

**Review:** End-of-sprint demo + code review

---

### Sprint 3-4: Gardener Agent & Quadratic Funding (Weeks 3-4)

#### Sprint 3 (Week 3)

**Milestone:** Gardener Agent Core Implementation

**Tasks:**
1. **Create memory hygiene module**
   - `vessels/memory/gardener.py`
   - `GardenerAgent` class
   - Scheduling logic (nightly runs)
   - Stats tracking (`GardenerStats`)
   - Assignee: Developer A
   - Estimate: 2 days

2. **Implement pruning logic**
   - `vessels/memory/pruning.py`
   - `prune_low_utility_memories()` method
   - Criteria: access_count < 3, age > 90 days, kala_value < 0.1
   - Archive mechanism
   - Assignee: Developer A
   - Estimate: 2 days

3. **Implement synthesis logic**
   - `vessels/memory/synthesis.py`
   - `synthesize_duplicates()` method
   - DBSCAN clustering (eps=0.05, metric='cosine')
   - Wisdom node creation
   - Assignee: Developer B
   - Estimate: 2 days

4. **Implement fact-checking**
   - `vessels/memory/fact_checking.py`
   - `find_contradictions()` method
   - Flag for human review
   - Assignee: Developer B
   - Estimate: 1 day

**Deliverables:**
- Gardener agent module
- Unit tests (15+ tests)

---

#### Sprint 4 (Week 4)

**Milestone:** Gardener Integration + Quadratic Funding

**Tasks:**
1. **Integrate Gardener into Agent Zero Core**
   - Modify `agent_zero_core.py`:
     - Spawn Gardener on startup
     - Background thread with low priority
     - CPU budget monitoring (<5% average)
   - Assignee: Developer A
   - Estimate: 2 days

2. **Add Gardener observability**
   - Dashboard for Gardener stats
   - Metrics: pruned_count, synthesized_count, contradictions_found
   - Assignee: Developer A
   - Estimate: 1 day

3. **Implement Quadratic Funding allocator**
   - `vessels/economics/quadratic_funding.py`
   - `QuadraticFundingAllocator` class
   - `allocate()` method with QF formula
   - Unit tests (10+ tests, including Sybil attack scenarios)
   - Assignee: Developer B
   - Estimate: 2 days

4. **Create project tracking**
   - `vessels/economics/projects.py`
   - `Project` dataclass
   - Contribution tracking
   - Assignee: Developer B
   - Estimate: 1 day

5. **Governance integration**
   - `vessels/economics/governance.py`
   - Monthly allocation automation
   - Transparency reporting
   - Assignee: Developer B
   - Estimate: 2 days

**Deliverables:**
- Fully integrated Gardener agent
- Quadratic funding allocator
- Governance dashboard

**Review:** End-of-sprint demo + performance testing

---

### Sprint 5-6: Ghost Mode & Visual Policy Editor (Weeks 5-6)

#### Sprint 5 (Week 5)

**Milestone:** Ghost Mode Implementation

**Tasks:**
1. **Add dry-run mode to Action Gate**
   - Modify `vessels/gating/gate.py`:
     - Add `dry_run: bool` parameter to `gate_action()`
     - Skip intervention when `dry_run=True`
     - Return full `GatingResult` with violations
   - Assignee: Developer A
   - Estimate: 1 day

2. **Create Ghost Agent wrapper**
   - `vessels/agents/ghost_mode.py`
   - `GhostAgent` class
   - Simulation logging (`SimulationEntry`)
   - Query shadowing logic
   - Assignee: Developer A
   - Estimate: 2 days

3. **Implement Safety Report generation**
   - `vessels/agents/safety_report.py`
   - `SafetyReport` dataclass
   - Analysis methods (violation breakdown, trends)
   - Recommendation engine (SAFE vs NEEDS_REVIEW)
   - Assignee: Developer A
   - Estimate: 2 days

4. **Create Ghost Mode tests**
   - `vessels/tests/test_ghost_mode.py`
   - Test safety report accuracy
   - Test state isolation
   - Assignee: Developer B
   - Estimate: 1 day

**Deliverables:**
- Ghost mode framework
- Safety reporting
- Unit tests (10+ tests)

---

#### Sprint 6 (Week 6)

**Milestone:** Visual Policy Editor

**Tasks:**
1. **Create YAML-to-Manifold compiler**
   - `vessels/constraints/compiler.py`
   - `ConstraintCompiler` class
   - `compile()` method (YAML → Manifold)
   - `compile_rule()` for individual constraints
   - Assignee: Developer A
   - Estimate: 3 days

2. **Add coherence validation**
   - `vessels/constraints/validator_ui.py`
   - Check for contradictory constraints
   - Warn on infeasible configurations
   - Assignee: Developer A
   - Estimate: 1 day

3. **Build React frontend**
   - `vessels/web/policy_editor/` (new React app)
   - Components:
     - `PolicyEditor.tsx` (main component)
     - `ConstraintSlider.tsx`
     - `ConstraintRuleEditor.tsx`
     - `ExportButton.tsx`
   - Assignee: Developer B
   - Estimate: 3 days

4. **Create deployment API**
   - Modify `vessels_web_server.py`:
     - `POST /api/policy/deploy` endpoint
     - Hot-reload manifold
     - Validation + error handling
   - Assignee: Developer B
   - Estimate: 1 day

5. **Integration testing**
   - End-to-end tests (UI → YAML → Manifold → Runtime)
   - Assignee: Developer A + B
   - Estimate: 1 day

**Deliverables:**
- Visual policy editor (web UI)
- YAML compiler
- Deployment API
- Integration tests

**Review:** End-of-Phase-1 demo for stakeholders

---

## Phase 1 Summary

**Timeline:** 6 weeks
**Total Story Points:** ~60 (assuming 2 developers, ~5 SP/dev/week)

**Key Achievements:**
- ✅ Offline-first architecture (CRDTs)
- ✅ Hardened constraint system (adversarial testing)
- ✅ Automated memory hygiene (Gardener)
- ✅ Economic maturity (Quadratic Funding)
- ✅ Safe agent deployment (Ghost Mode)
- ✅ Accessible policy configuration (Visual Editor)

**Success Criteria:**
- All unit tests passing (100+ new tests)
- Performance benchmarks met (offline sync <100ms, Gardener <5% CPU)
- Documentation complete (docstrings + user guides)
- Stakeholder demo approval

---

## Phase 2: Foundational Systems (Weeks 7-12)

### Sprint 7-8: Cryptographic State Proofs (Weeks 7-8)

**Milestone:** Tamper-Proof Audit Trail

**Tasks:**

**Week 7:**
1. **Create crypto module structure**
   - `vessels/crypto/__init__.py`
   - `vessels/crypto/state_signing.py`
   - `vessels/crypto/audit_log.py`
   - `vessels/crypto/verification.py`
   - Estimate: 1 day

2. **Implement signature system (software keys)**
   - Use Ed25519 from `cryptography` library
   - Key generation + storage
   - Sign state transitions
   - Estimate: 3 days

3. **Create append-only audit log**
   - Merkle tree implementation
   - SQLite storage with hash chaining
   - Estimate: 3 days

**Week 8:**
4. **Integrate into Action Gate**
   - Modify `vessels/gating/gate.py`:
     - Sign every state transition
     - Append to audit log
   - Estimate: 2 days

5. **Build verification service**
   - `verify_state_history()` method
   - Merkle proof validation
   - Estimate: 2 days

6. **Testing + documentation**
   - Unit tests (15+ tests)
   - Security audit (internal)
   - Documentation
   - Estimate: 3 days

**Deliverables:**
- Cryptographically signed state transitions
- Append-only audit log
- Verification tooling

---

### Sprint 9-10: Causal Reasoning (Weeks 9-10)

**Milestone:** Causal Inference Engine

**Tasks:**

**Week 9:**
1. **Extend graph schema**
   - Modify `vessels/knowledge/schema.py`:
     - Add `CAUSED_BY`, `PREVENTED_BY` relationship types
     - Add `confidence` field to relationships
   - Estimate: 1 day

2. **Implement heuristic causal inference**
   - `vessels/knowledge/causal_inference.py`
   - `SimpleCausalInference` class
   - Methods: `infer_causes()`, `calculate_confidence()`
   - Heuristics: temporal proximity, co-occurrence, domain rules
   - Estimate: 3 days

3. **Build causal query interface**
   - `vessels/knowledge/causal_queries.py`
   - Query methods: `query_causes()`, `query_effects()`
   - Integration with Graphiti client
   - Estimate: 2 days

**Week 10:**
4. **Integrate with Graphiti**
   - Modify `vessels/knowledge/graphiti_client.py`:
     - Add causal query methods
     - Store inferred causal relationships
   - Estimate: 2 days

5. **Testing**
   - Unit tests (20+ tests)
   - Historical data analysis (validate inference quality)
   - Estimate: 3 days

**Deliverables:**
- Causal reasoning engine
- Graph schema extensions
- Query interface

---

### Sprint 11-12: Dynamic Calibration & Inter-Community Clearing (Weeks 11-12)

**Milestone:** Adaptive Constraints + Economic Coordination

**Tasks:**

**Week 11:**
1. **Build outcome tracking infrastructure**
   - `vessels/constraints/feedback.py`
   - `OutcomeFeedback` dataclass
   - `OutcomeFeedbackStore` (SQLite)
   - Estimate: 2 days

2. **Create feedback UI**
   - Simple rating interface (1-5 stars)
   - API endpoint: `POST /api/feedback`
   - Estimate: 2 days

3. **Implement calibration logic**
   - `vessels/constraints/calibration.py`
   - `ManifoldCalibrator` class
   - Correlation analysis (scipy)
   - Flagging mechanism
   - Estimate: 3 days

**Week 12:**
4. **Build inter-community clearing house**
   - `vessels/economics/clearing_house.py`
   - `InterCommunityClearingHouse` class
   - Swap matching algorithm
   - Estimate: 3 days

5. **Integration testing**
   - Multi-community swap scenarios
   - Trust verification
   - Estimate: 2 days

**Deliverables:**
- Dynamic constraint calibration
- Inter-community economic clearing
- Feedback UI

**Review:** End-of-Phase-2 demo

---

## Phase 3: Federation & Advanced Features (Weeks 13+)

### Sprint 13-15: Federated Knowledge Graphs (Weeks 13-15)

**Milestone:** Peer-to-Peer Sovereignty

**Tasks:**

**Week 13:**
1. **Design federation protocol**
   - Subscription model (which sub-graphs to sync)
   - Merkle tree verification
   - Delta sync (not full graph)
   - Estimate: 2 days

2. **Implement graph diff algorithm**
   - Custom or extend Graphiti
   - Generate deltas for sync
   - Estimate: 3 days

**Week 14:**
3. **Build sync manager**
   - `vessels/federation/sync_manager.py`
   - Methods: `subscribe()`, `sync()`, `verify()`
   - Estimate: 4 days

4. **Implement Merkle verification**
   - `vessels/federation/merkle_verification.py`
   - Verify graph integrity
   - Estimate: 3 days

**Week 15:**
5. **Multi-node testing**
   - Deploy 3+ Vessels instances
   - Test cross-community sync
   - Measure latency (<5s target)
   - Estimate: 3 days

6. **Documentation**
   - Federation setup guide
   - Security considerations
   - Estimate: 2 days

**Deliverables:**
- Federated knowledge graphs
- Multi-node tested with 3+ communities

---

### Sprint 16+: Zero-Knowledge Proofs (Research Phase)

**Milestone:** Privacy Compliance Proofs (or Attestation Alternative)

**Decision Point:** Week 16

**Option A: ZKP Implementation (4+ weeks)**
- Research zk-SNARK libraries
- Design privacy circuits
- Prototype + testing
- Requires cryptography expertise

**Option B: Attestation Service (2 weeks)**
- Third-party audit service
- Signed certificates
- Trust-based (interim solution)

**Recommendation:** Start with Option B (attestation), plan Option A for future release.

---

## Resource Allocation

### Developer Roles

**Developer A (Backend Focus):**
- CRDT implementation
- Memory/Kala integration
- Gardener agent
- Ghost mode
- Cryptographic proofs
- Causal reasoning

**Developer B (Full-Stack):**
- CRDT sync protocol
- Adversarial testing
- Quadratic funding
- Visual policy editor (React)
- Inter-community clearing

**Developer C (Optional, Weeks 7+):**
- Frontend polish
- Documentation
- Testing support
- DevOps (deployment automation)

---

## Dependencies & Blockers

### External Dependencies

**New Dependencies to Add:**
```
# Phase 1
scikit-learn>=1.0.0  # For DBSCAN clustering (Gardener)

# Phase 2
pymerkle>=4.0.0  # For Merkle trees (crypto proofs, federation)

# Phase 3
# TBD based on ZKP decision
```

**No Blockers Identified** for Phase 1 (Weeks 1-6).

**Potential Blockers for Phase 2+:**
- Outcome feedback UI requires user testing (may need UX designer)
- Federation protocol requires network testing environment (3+ nodes)

---

## Success Metrics (Tracked per Sprint)

### Development Velocity
- **Story Points Completed** (target: 10 SP/week for 2 devs)
- **Test Coverage** (target: >80% for new code)
- **Code Review Turnaround** (target: <24 hours)

### Quality Metrics
- **Bugs per Sprint** (target: <3 critical bugs)
- **Performance Regressions** (target: 0)
- **Documentation Coverage** (target: 100% for public APIs)

### User-Facing Metrics (Phase 1 End)
- **Offline Sync Success Rate** (target: >99.9%)
- **Adversarial Block Rate** (target: >95%)
- **Memory Pollution Rate** (target: <5% after 90 days)
- **Ghost Mode Coverage** (target: 100% for new agents)
- **Policy Editor Adoption** (target: >80% of policy changes via GUI)

---

## Risk Management

### High-Priority Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| **CRDT performance degradation** | MEDIUM | HIGH | Benchmark with 10,000+ memories; optimize merge algorithms; consider sharding |
| **Adversarial tests miss real exploits** | MEDIUM | HIGH | Continuous fuzzing; bug bounty program (Phase 2); external security audit |
| **Gardener over-prunes important memories** | MEDIUM | MEDIUM | Human review for high-Kala memories; undo mechanism; conservative thresholds initially |
| **Visual editor enables harmful policies** | LOW | HIGH | Policy validation layer; community review period (24 hours); rollback mechanism |
| **Developer availability** | MEDIUM | HIGH | Cross-training; documentation; modular design (tasks can be reassigned) |

### Contingency Plans

**If CRDT performance is insufficient:**
- Fallback: Keep SQLite as primary, use CRDT only for cross-community sync
- Timeline impact: +1 week

**If adversarial testing discovers major loopholes:**
- Immediate fix (pause other work)
- Post-mortem to understand how it was missed
- Timeline impact: +1-2 weeks (depends on severity)

**If developer bandwidth reduced:**
- Prioritize P0 items only
- Defer Visual Policy Editor to Phase 2
- Timeline impact: Extend Phase 1 by 2 weeks

---

## Communication Plan

### Weekly Standups (Every Monday)
- Progress updates
- Blockers discussion
- Next week planning

### Sprint Reviews (Every 2 Weeks)
- Demo to stakeholders
- Feedback collection
- Adjust priorities if needed

### Phase Reviews (Weeks 6, 12, 16)
- Major demo
- Go/no-go decision for next phase
- Retrospective

### Documentation
- **Daily:** Inline code comments + docstrings
- **Weekly:** Update CHANGELOG.md
- **Per Sprint:** User-facing docs (if new features)

---

## Deployment Strategy

### Staging Environment
- Deploy after every sprint
- Run integration tests
- Performance benchmarking

### Production Rollout (Phase 1 End, Week 7)
- **Week 6:** Staging deployment
- **Week 7:** Gradual rollout
  - Day 1: Single test community
  - Day 3: 3 communities
  - Day 7: All communities (if no critical issues)
- **Monitoring:** 24/7 for first week

### Rollback Plan
- Keep previous version deployed (blue-green)
- Rollback trigger: >5% error rate or critical bug
- Rollback time: <15 minutes

---

## Post-Implementation

### Maintenance (Ongoing)
- **Bug fixes:** As reported
- **Performance tuning:** Monthly reviews
- **Dependency updates:** Quarterly

### Future Enhancements (Post-Week 16)
- Mobile app (offline-first with CRDT sync)
- Advanced ZKP circuits (if research successful)
- Multi-language support
- Governance voting UI (extends Quadratic Funding)

---

## Conclusion

This roadmap provides a clear, actionable plan for delivering transformative improvements to the Vessels platform. By focusing on high-feasibility, high-value features in Phase 1 (Weeks 1-6), we establish a strong foundation for more advanced capabilities in Phases 2 and 3.

**Key Success Factors:**
- ✅ Modular implementation (features are independent)
- ✅ Continuous testing (adversarial + unit + integration)
- ✅ Incremental deployment (low risk)
- ✅ Clear success metrics (data-driven decisions)

**Next Steps:**
1. ✅ Approve this roadmap
2. ✅ Set up project tracking (GitHub Projects or similar)
3. ✅ Assign developers to sprints
4. ✅ **BEGIN SPRINT 1** (CRDT Foundation)

---

**Roadmap Status:** READY FOR IMPLEMENTATION
**Sprint 1 Start Date:** 2025-11-25 (Proposed)
**Phase 1 Target Completion:** 2026-01-06 (6 weeks)
