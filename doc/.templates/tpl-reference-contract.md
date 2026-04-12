
<!--
LLM INSTRUCTION BLOCK
MOTIVATION: This file is the strict, machine-readable truth for data structures and external boundaries. It is highly technical and DESCRIPTIVE.
CONTENTS: Data Transfer Objects (DTOs), Database Schemas, REST endpoints, and SSE Streaming Protocols.
DO'S:
- DO use exact data types (e.g., `str`, `int`, `Optional[datetime]`).
- DO note which fields are nullable, unique, or indexed.
- DO provide a raw JSON/Code example of the payload.
- DO explicitly define SSE event types if documenting a streaming endpoint.
DON'TS:
- DO NOT explain the UI or user journey here.
-->

# 💾 Data Contract: [Entity / Integration Name]

**Type:** [Database Schema | REST API | SSE Stream | Internal DTO]
**Source of Truth:** `src/features/[feature_name]/domain/models.py`

## 1. Schema Definition: `[ModelName]`

| Field Name | Type | Required | Default | Description / Constraints |
| :--- | :--- | :---: | :--- | :--- |
| `id` | `UUID` | Yes | Auto | Primary Key |
| `[field_name]` | `[type]` | [Yes/No] | `[val]` | [What does this represent?] |

## 2. Validation Rules
*   **[Field Name]:** [e.g., Must be greater than 0, Must match Regex `^[A-Z]+$`]

## 3. SSE Streaming Protocol (If Applicable)
**Endpoint:** `[GET/POST] /api/v1/...`
**Content-Type:** `text/event-stream`

| Event Name | Payload Schema (JSON) | Trigger Condition |
| :--- | :--- | :--- |
| `[event_name]` | `{"type": "...", "data": ...}` | [When is this yielded?] |

**Example Stream:**
```text
data: {"event": "start", "data": {"id": "123"}}
data: {"event": "chunk", "data": {"text": "Hello"}}
data: {"event": "done", "data": {"tokens": 42}}
```
