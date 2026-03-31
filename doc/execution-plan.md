<!--
LLM INSTRUCTION BLOCK
MOTIVATION: This is a TEMPORAL document. It acts as the Agile board, sprint tracker, and immediate context prompt for AI coding agents.
CONTENTS: Active sprint goals, TDD tasks, test status, and commit hashes.
DO'S:
- DO update the "Status" and "Commits" lines immediately after completing an atomic task.
- DO read this file first to understand your current micro-goal before writing any code.
- DO strictly follow the 3-Tier Integration Testing Strategy (FastAPI TestClient, Fake LLMs, In-Memory DB).
DON'TS:
- DO NOT put permanent architectural decisions here (put them in docs/2-architecture).
-->

# 🏃‍♂️ Active Execution Plan

**Current Phase:** [e.g., MVP Development]
**Overall Status:** [e.g., Sprint 1 in progress]

---

## 🎯 Active Sprint: [Sprint Number & Name]
*   **Goal:** [What is the business value of this sprint?]
*   **Status:** [Not Started | In Progress | Blocked | COMPLETE]

### TDD Tasks (Execute in order)
1.  [ ] **Task 1: Write Integration Tests** 
    *   *Requirement:* Use FastAPI `TestClient`.
    *   *Requirement:* Override external interfaces (e.g., `ILLMService`) with a Fake/Mock. DO NOT hit real APIs.
    *   *Requirement:* Use an in-memory SQLite database fixture.
    *   *Deliverables:* `tests/integration/test_[feature].py`
    *   *Status:* [Pending | X/X Tests Passing]

2.  [ ] **Task 2: Implement Core Logic (Domain & Application)**
    *   *Requirement:* Implement the Use Case and Domain models to make Task 1 pass.
    *   *Deliverables:* `src/features/[feature]/domain/...`, `src/features/[feature]/use_cases/...`
    *   *Status:* [Pending]

3.  [ ] **Task 3: Implement Infrastructure Adapters**
    *   *Requirement:* Write the concrete implementations (e.g., SQLAlchemy Repos, OpenAI Adapters).
    *   *Deliverables:* `src/features/[feature]/infrastructure/...`
    *   *Status:* [Pending]

---

## 📦 Backlog (Upcoming Sprints)
*   **Sprint [X+1]:** [Brief description of next priority]

---

## ✅ Completed Sprints (Archive)
*   **Sprint [X-1]:** [Name] - COMPLETE (Commits: `abc1234`)
```