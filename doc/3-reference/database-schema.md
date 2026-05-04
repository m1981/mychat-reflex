# Database Schema Reference

**Database**: SQLite (via Reflex `rx.Model` / SQLModel)
**ORM**: SQLModel + SQLAlchemy (managed by Reflex)
**Migration Tool**: Alembic (revision `da92f255a8fe` is the current baseline)
**Last Updated**: 2026-05-04

> **⚠ Reading this document**
> Every SQL block here is **descriptive of the live schema produced by Alembic**, not a hand-written DDL contract. The authoritative source is `alembic/versions/da92f255a8fe_.py`. If they disagree, the migration wins — please open a PR to update this file.

---

## Schema Overview

SQLModel (which Reflex uses under the hood for `rx.Model`) generates **singular, lower-case, no-underscore** table names by default. The actual tables in `reflex.db` are:

```
chatfolder        -- Folders that group conversations
conversation      -- Chat conversations (aggregate root)
message           -- Individual chat messages
alembic_version   -- Alembic bookkeeping
```

There is **no** `reflex_user` table in this project (no auth yet).

---

## 1. `conversation`

**Purpose**: Stores chat conversation metadata.

**Live schema (from migration `da92f255a8fe`)**:

```sql
CREATE TABLE conversation (
    id          VARCHAR NOT NULL,
    title       VARCHAR NOT NULL,
    folder_id   VARCHAR,                  -- nullable FK to chatfolder.id
    created_at  DATETIME NOT NULL,
    updated_at  DATETIME NOT NULL,
    PRIMARY KEY (id),
    FOREIGN KEY (folder_id) REFERENCES chatfolder(id)
);
```

**Columns**:
- `id` (VARCHAR, PK): UUID4 string generated in application code (`uuid4()` in `ChatState.create_new_chat`).
- `title` (VARCHAR, NOT NULL): Display name. Application default is `"New Chat"`.
- `folder_id` (VARCHAR, FK, nullable): Reference to `chatfolder.id`.
- `created_at` (DATETIME, NOT NULL): Set in Python via `default_factory=lambda: datetime.now(timezone.utc)`.
- `updated_at` (DATETIME, NOT NULL): Same default; bumped in `ChatState.handle_send_message` after each AI reply.

**Relationships**:
- Has many `message` rows (one-to-many via `message.conversation_id`).
- Belongs to zero or one `chatfolder` (many-to-one via `folder_id`).

**Cascade behaviour**:
- The migration declares plain foreign keys with **no `ON DELETE` rules**. Cascading on conversation/folder deletion is **not** enforced at the DB level today — it must be handled in application code, or added in a future migration.

**`rx.Model` definition** (`mychat_reflex/features/chat/models.py`):
```python
class Conversation(rx.Model, table=True):
    id: str = Field(primary_key=True)
    title: str = "New Chat"
    folder_id: Optional[str] = Field(default=None, foreign_key="chatfolder.id")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def is_in_folder(self) -> bool:
        return self.folder_id is not None
```

> **Note on `default_factory`**: the older pattern `created_at: datetime = datetime.utcnow()` evaluates **once at class-definition time**, so every row would get the same timestamp. `default_factory=lambda: datetime.now(timezone.utc)` evaluates per-insert and is timezone-aware.

---

## 2. `message`

**Purpose**: Stores individual chat messages (user, assistant, or system turns).

**Live schema**:

```sql
CREATE TABLE message (
    id              VARCHAR NOT NULL,
    conversation_id VARCHAR NOT NULL,
    role            VARCHAR NOT NULL,    -- "user" | "assistant" | "system" (enforced in app)
    content         VARCHAR NOT NULL,
    created_at      DATETIME NOT NULL,
    model_used      VARCHAR,             -- e.g., "claude-sonnet-4-5", "gpt-4o"
    avatar_url      VARCHAR,
    PRIMARY KEY (id),
    FOREIGN KEY (conversation_id) REFERENCES conversation(id)
);
```

**Columns**:
- `id` (VARCHAR, PK): UUID4 string (`uuid4()` in `ChatState`).
- `conversation_id` (VARCHAR, FK, NOT NULL): Parent conversation.
- `role` (VARCHAR, NOT NULL): One of `"user"`, `"assistant"`, `"system"`. **Validation lives in application code only** — there is no DB-level CHECK constraint.
- `content` (VARCHAR, NOT NULL): Plain text. The UI renders it as Markdown with Shiki code-highlighting (see `features/chat/ui.py`), but the DB only sees a string.
- `created_at` (DATETIME, NOT NULL): App-side default (`datetime.now(timezone.utc)`).
- `model_used` (VARCHAR, nullable): LLM identifier for assistant messages; `NULL` for user/system messages.
- `avatar_url` (VARCHAR, nullable): User profile picture URL (assistant uses an icon, not this column).

**Relationships**:
- Belongs to one `conversation` (many-to-one via `conversation_id`).

**Business rules** (enforced in application layer):
- `role` ∈ {`user`, `assistant`, `system`}.
- User messages have `model_used = NULL`.
- Assistant messages should populate `model_used`.
- Messages are ordered by `created_at` within a conversation.

**`rx.Model` definition**:
```python
class Message(rx.Model, table=True):
    id: str = Field(primary_key=True)
    conversation_id: str = Field(foreign_key="conversation.id")
    role: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_used: Optional[str] = None
    avatar_url: Optional[str] = None

    @property
    def is_user(self) -> bool: return self.role == "user"

    @property
    def is_assistant(self) -> bool: return self.role == "assistant"

    @property
    def timestamp_formatted(self) -> str:
        return self.created_at.strftime("%I:%M %p %d %b %Y")
```

---

## 3. `chatfolder`

**Purpose**: Organizational folders for grouping conversations.

**Live schema**:

```sql
CREATE TABLE chatfolder (
    id          VARCHAR NOT NULL,
    name        VARCHAR NOT NULL,
    created_at  DATETIME NOT NULL,
    PRIMARY KEY (id)
);
```

**Columns**:
- `id` (VARCHAR, PK): UUID4 string.
- `name` (VARCHAR, NOT NULL): Folder display name (e.g., "Job offers", "ESP32 projects").
- `created_at` (DATETIME, NOT NULL): App-side `default_factory`.

**Relationships**:
- Has many `conversation` rows (one-to-many via `conversation.folder_id`).

**Business rules**:
- Folder name uniqueness is **not** enforced (no unique constraint). If desired, enforce it in application code or add a migration.
- Empty folders are allowed.
- Deleting a folder with conversations attached: today the FK has no `ON DELETE` rule, so SQLite will refuse the delete unless `folder_id`s are first NULLed by the application.

**`rx.Model` definition**:
```python
class ChatFolder(rx.Model, table=True):
    id: str = Field(primary_key=True)
    name: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

> **Location note**: All three models (`Message`, `Conversation`, `ChatFolder`) currently live in `features/chat/models.py`. The architecture doc previously suggested moving `ChatFolder` to `features/workspace/models.py` — this has **not** happened and is tracked as future work.

---

## 4. Entity Relationship Diagram

```
chatfolder (1) ──────── (0..N) conversation (1) ──────── (0..N) message
    id                              id                            id
    name                            title                         conversation_id (FK)
    created_at                      folder_id (FK, nullable)      role
                                    created_at                    content
                                    updated_at                    created_at
                                                                  model_used
                                                                  avatar_url
```

**Cardinality**:
- One folder → many conversations (0..N).
- One conversation → zero or one folder (0..1).
- One conversation → many messages (0..N — a brand-new chat starts empty).
- One message → exactly one conversation (1).

---

## 5. Sample Data

```sql
-- Sample folders
INSERT INTO chatfolder (id, name, created_at) VALUES
('folder-1', 'Job offers',     '2026-04-01 10:00:00'),
('folder-2', 'ESP32 projects', '2026-04-01 10:00:00');

-- Sample conversations
INSERT INTO conversation (id, title, folder_id, created_at, updated_at) VALUES
('conv-1', 'CV update',      'folder-1', '2026-04-10 09:00:00', '2026-04-10 09:15:00'),
('conv-2', 'ESP32 overview', 'folder-2', '2026-04-12 14:00:00', '2026-04-12 14:30:00');

-- Sample messages
INSERT INTO message (id, conversation_id, role, content, created_at, model_used) VALUES
('msg-1', 'conv-2', 'user',      'What is ESP32?',                       '2026-04-12 14:00:00', NULL),
('msg-2', 'conv-2', 'assistant', 'ESP32 is a low-cost microcontroller…', '2026-04-12 14:00:05', 'claude-sonnet-4-5');
```

---

## 6. Migration Workflow

This project uses **Alembic directly** (`alembic.ini` at repo root, revisions in `alembic/versions/`).

```bash
# Create a new revision after changing rx.Model classes
alembic revision --autogenerate -m "describe the change"

# Apply migrations to the local SQLite DB
alembic upgrade head

# Inspect current revision
alembic current

# Roll back one step
alembic downgrade -1
```

Reflex also exposes thin wrappers (`reflex db makemigrations`, `reflex db migrate`) which call the same Alembic machinery; either is fine.

**Current baseline**: revision `da92f255a8fe` ("empty message", 2026-04-13). It is the only revision and it creates `chatfolder`, `conversation`, and `message`. There are no follow-up migrations yet.

---

## 7. Common Query Patterns

### Get conversation with messages
```python
from sqlmodel import select
from mychat_reflex.features.chat.models import Conversation, Message

with rx.session() as session:
    conversation = session.get(Conversation, conv_id)
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == conv_id)
        .order_by(Message.created_at)
    ).all()
```

### Get conversations in folder
```python
with rx.session() as session:
    conversations = session.exec(
        select(Conversation)
        .where(Conversation.folder_id == folder_id)
        .order_by(Conversation.updated_at.desc())
    ).all()
```

### Get all folders
```python
with rx.session() as session:
    folders = session.exec(select(ChatFolder)).all()
```

> **The codebase uses modern SQLModel `select()` syntax** (see `LoadHistoryUseCase.execute`). Avoid the legacy `session.query(...)` style in new code.

---

## 8. Advanced Query Patterns (recipes — not yet wired into features)

The patterns below are **reference snippets**. Most of them are not currently used by the app; treat them as templates for upcoming features (sidebar previews, search, stats, batch ops).

### 8.1 Recent Conversations with Last-Message Preview

```python
from sqlalchemy import func
from sqlmodel import select
from mychat_reflex.features.chat.models import Conversation, Message

def get_recent_conversations_with_preview(limit: int = 20):
    with rx.session() as session:
        conversations = session.exec(
            select(Conversation)
            .order_by(Conversation.updated_at.desc())
            .limit(limit)
        ).all()

        results = []
        for conv in conversations:
            last_msg = session.exec(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .limit(1)
            ).first()

            count = session.exec(
                select(func.count(Message.id))
                .where(Message.conversation_id == conv.id)
            ).one()

            results.append({
                "conversation": conv,
                "last_message": (last_msg.content[:50] + "…") if last_msg else "",
                "message_count": count,
            })

        session.expunge_all()
        return results
```

### 8.2 Search Messages by Content

```python
def search_messages(query: str, limit: int = 50):
    with rx.session() as session:
        return session.exec(
            select(Message)
            .where(Message.content.like(f"%{query}%"))
            .order_by(Message.created_at.desc())
            .limit(limit)
        ).all()
```

> For production, consider SQLite FTS5 (virtual table + triggers) or moving to PostgreSQL with `tsvector`.

### 8.3 Conversation Statistics

```python
from datetime import datetime, timedelta, timezone

def get_conversation_stats(conversation_id: str):
    with rx.session() as session:
        total = session.exec(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id)
        ).one()

        user_count = session.exec(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id,
                   Message.role == "user")
        ).one()

        ai_count = session.exec(
            select(func.count(Message.id))
            .where(Message.conversation_id == conversation_id,
                   Message.role == "assistant")
        ).one()

        first_msg = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .limit(1)
        ).first()

        last_msg = session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        ).first()

        duration = (last_msg.created_at - first_msg.created_at) if (first_msg and last_msg) else timedelta(0)

        return {
            "total_messages": total,
            "user_messages": user_count,
            "ai_messages": ai_count,
            "first_message_at": first_msg.created_at if first_msg else None,
            "last_message_at": last_msg.created_at if last_msg else None,
            "duration": duration,
        }
```

### 8.4 Batch Operations

```python
def delete_old_conversations(days_old: int = 90):
    """Delete conversations older than X days. Messages are NOT cascade-deleted today —
    you must delete them explicitly (or add an ON DELETE CASCADE migration first)."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days_old)
    with rx.session() as session:
        old_ids = [c.id for c in session.exec(
            select(Conversation).where(Conversation.updated_at < cutoff)
        ).all()]

        session.exec(
            Message.__table__.delete().where(Message.conversation_id.in_(old_ids))
        )
        session.exec(
            Conversation.__table__.delete().where(Conversation.id.in_(old_ids))
        )
        session.commit()
        return len(old_ids)


def move_conversations_to_folder(conversation_ids: list[str], folder_id: str):
    with rx.session() as session:
        for conv in session.exec(
            select(Conversation).where(Conversation.id.in_(conversation_ids))
        ).all():
            conv.folder_id = folder_id
        session.commit()
```

---

## 9. Optimisation Strategies (forward-looking)

### 9.1 Index Strategy

**Current state**: the `da92f255a8fe` migration creates **only primary keys and foreign keys** — no secondary indexes. SQLite implicitly indexes PKs and (in modern versions) FKs, but range/order queries on `created_at` are full scans.

**Recommended next migration** when usage grows:

```sql
CREATE INDEX idx_conversation_folder_id        ON conversation(folder_id);
CREATE INDEX idx_conversation_updated_at       ON conversation(updated_at DESC);
CREATE INDEX idx_message_conversation_created  ON message(conversation_id, created_at);
CREATE INDEX idx_message_role                  ON message(role);
```

Generate it via:
```bash
alembic revision -m "add hot-path indexes"
# then hand-write op.create_index(...) calls
alembic upgrade head
```

### 9.2 Query Optimisation Patterns

**❌ N+1 antipattern**:
```python
conversations = session.exec(select(Conversation)).all()
for conv in conversations:
    msgs = session.exec(select(Message).where(Message.conversation_id == conv.id)).all()
```

**✅ Pagination** (current recommended pattern for `LoadHistoryUseCase` extensions):
```python
def get_messages_paginated(conversation_id: str, page: int = 1, page_size: int = 50):
    offset = (page - 1) * page_size
    with rx.session() as session:
        return session.exec(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(offset).limit(page_size)
        ).all()
```

### 9.3 Connection Pooling

Reflex configures the engine via `rxconfig.py`. For SQLite in dev, pooling is largely a no-op. When migrating to Postgres, set `pool_size` / `max_overflow` / `pool_timeout` on the engine URL.

### 9.4 Caching

The current `ChatState` does not cache messages — `on_load` and `select_chat` re-query on every navigation. If this becomes a bottleneck, a per-conversation in-state cache is the simplest first step:

```python
class ChatState(rx.State):
    _message_cache: dict[str, list[Message]] = {}
    # … populate / invalidate on send / delete
```

---

## 10. Data Migration Strategies

### 10.1 Schema Versioning

Alembic's `alembic_version` table is the single source of truth for "what schema am I on?". Don't roll your own `schema_version` table.

### 10.2 Writing a Migration

```bash
alembic revision --autogenerate -m "add avatar_url to message"
```

Generated stub:
```python
def upgrade() -> None:
    op.add_column("message", sa.Column("avatar_url", sa.String(), nullable=True))

def downgrade() -> None:
    op.drop_column("message", "avatar_url")
```

### 10.3 Data Backfill Pattern

```python
def backfill_model_used():
    with rx.session() as session:
        orphans = session.exec(
            select(Message)
            .where(Message.role == "assistant", Message.model_used.is_(None))
        ).all()

        for msg in orphans:
            msg.model_used = "claude-sonnet-3-5"  # historical default
        session.commit()
```

---

## 11. Monitoring & Debugging

### 11.1 Enable Query Logging
```python
import logging
logging.basicConfig()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
```

### 11.2 Quick Performance Check
```python
import time
start = time.time()
with rx.session() as session:
    rows = session.exec(
        select(Message).where(Message.conversation_id == "conv-1")
    ).all()
print(f"{(time.time()-start)*1000:.2f} ms, {len(rows)} rows")
```

### 11.3 DB Size

```bash
# File size
ls -lh reflex.db

# Reclaim space after large deletes
sqlite3 reflex.db "VACUUM;"
```

---

## 12. Backup & Recovery

### 12.1 Backup
```bash
# Cold copy (app should be stopped)
cp reflex.db reflex_backup_$(date +%Y%m%d_%H%M%S).db

# Hot, consistent backup
sqlite3 reflex.db ".backup reflex_backup.db"
```

### 12.2 Restore
```bash
pkill -f "reflex run"
cp backups/reflex_20260412_120000.db reflex.db
reflex run
```

### 12.3 Export to JSON
```python
import json
from sqlmodel import select

def export_conversations_to_json(output_file: str = "export.json"):
    with rx.session() as session:
        conversations = session.exec(select(Conversation)).all()
        export = []
        for conv in conversations:
            messages = session.exec(
                select(Message)
                .where(Message.conversation_id == conv.id)
                .order_by(Message.created_at)
            ).all()
            export.append({
                "conversation": {
                    "id": conv.id,
                    "title": conv.title,
                    "folder_id": conv.folder_id,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                },
                "messages": [
                    {
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat(),
                        "model_used": m.model_used,
                    } for m in messages
                ],
            })
        with open(output_file, "w") as f:
            json.dump(export, f, indent=2)
```

---

## 13. Security Considerations

### 13.1 SQL Injection
SQLModel/SQLAlchemy parameterises all comparisons — `Message.conversation_id == user_input` is safe. **Never** build raw SQL strings with f-strings around user input.

### 13.2 Data at Rest
SQLite file is unencrypted on disk. For sensitive deployments, use SQLCipher or move to a managed Postgres with disk encryption.

### 13.3 What Must NEVER Be Stored
- API keys (Anthropic / OpenAI) — these live in `.env` and are loaded by `mychat_reflex.py:initialize_dependencies()`.
- Passwords / tokens / PII — auth is not implemented yet; design carefully when it is.

---

## 14. Testing Database Operations

### 14.1 In-Memory DB Fixture

```python
# tests/conftest.py
import pytest
from sqlmodel import SQLModel, Session, create_engine

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        yield s
```

This is exactly what `tests/features/chat/test_use_cases.py` does today.

### 14.2 Sample Fixture

```python
@pytest.fixture
def sample_conversation(session):
    conv = Conversation(id="test-conv-1", title="Test Conversation")
    session.add(conv)
    session.add(Message(id="msg-1", conversation_id=conv.id, role="user",      content="Hello"))
    session.add(Message(id="msg-2", conversation_id=conv.id, role="assistant", content="Hi there!"))
    session.commit()
    return conv.id
```

### 14.3 Integration Test Example

```python
from sqlmodel import select

def test_load_conversation_messages(session, sample_conversation):
    messages = session.exec(
        select(Message)
        .where(Message.conversation_id == sample_conversation)
        .order_by(Message.created_at)
    ).all()

    assert len(messages) == 2
    assert messages[0].content == "Hello"
    assert messages[1].content == "Hi there!"
```

---

## 15. Known Drift / Future Work

The following items are documented gaps between this reference and ideal state. Each should be a follow-up PR with an Alembic migration:

- [ ] Add `ON DELETE CASCADE` from `message.conversation_id` → `conversation.id`.
- [ ] Add `ON DELETE SET NULL` from `conversation.folder_id` → `chatfolder.id`.
- [ ] Add hot-path indexes (see §9.1).
- [ ] Consider a CHECK constraint on `message.role` (or migrate to a SQLModel `Enum` column).
- [ ] Decide whether `ChatFolder` belongs in `features/workspace/models.py` (currently lives in `features/chat/models.py`).
