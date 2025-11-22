# Story: Gating enforced for tool execution

## Summary
Tool calls and commercial introductions must flow through the action gate so that constraint violations are recorded and blocked when necessary.

## Acceptance Criteria
- Adaptive tool executions invoke the gate before running handlers when a gate is configured.
- Blocked gate decisions prevent the tool handler from executing and return an error reason.
- Allowed gate decisions persist security events and transitions via the trajectory tracker when available.
