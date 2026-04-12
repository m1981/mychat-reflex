# Database Schema Reference

**Database**: SQLite (via Reflex rx.Model)
**ORM**: SQLAlchemy (managed by Reflex)
**Migration Tool**: Alembic (via `reflex db migrate`)
**Last Updated**: 2026-04-12

---

## Schema Overview

```sql
-- Tables managed by Reflex rx.Model
conversations
messages
chat_folders
reflex_user (Reflex internal)
```

---

## 1. conversations

**Purpose**: Stores chat conversation metadata

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL DEFAULT 'New Chat',
    folder_id TEXT,  -- FK to chat_folders.id (nullable)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (folder_id) REFERENCES chat_folders(id) ON DELETE SET NULL
);

CREATE INDEX idx_conversations_folder_id ON conversations(folder_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);
```

**Columns**:
- `id` (TEXT, PK): UUID or unique identifier
- `title` (TEXT): Display name for conversation (e.g., "ESP32 Overview")
- `folder_id` (TEXT, FK, nullable): Reference to parent folder
- `created_at` (TIMESTAMP): Creation timestamp
- `updated_at` (TIMESTAMP): Last message timestamp

**Relationships**:
- Has many `messages` (one-to-many via `conversation_id`)
- Belongs to one `chat_folders` (optional, many-to-one via `folder_id`)

**Business Rules**:
- Deleting a conversation deletes all its messages (cascade)
- Deleting a folder sets `folder_id` to NULL (not cascade)
- Default title is "New Chat" (can be auto-generated from first message)

**rx.Model Definition**:
```python
class Conversation(rx.Model, table=True):
    id: str
    title: str = "New Chat"
    folder_id: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    updated_at: datetime = datetime.utcnow()
```

---

## 2. messages

**Purpose**: Stores individual chat messages (user and assistant turns)

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    model_used TEXT,  -- e.g., "claude-sonnet-4-5", "gpt-4o"
    avatar_url TEXT,  -- Optional user avatar
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_role ON messages(role);
```

**Columns**:
- `id` (TEXT, PK): UUID
- `conversation_id` (TEXT, FK): Parent conversation
- `role` (TEXT, CHECK): "user" | "assistant" | "system"
- `content` (TEXT): Message text (simplified string-only for MVP)
- `created_at` (TIMESTAMP): Message timestamp
- `model_used` (TEXT, nullable): Which LLM generated this (assistant only)
- `avatar_url` (TEXT, nullable): User profile picture URL

**Relationships**:
- Belongs to one `conversations` (many-to-one via `conversation_id`)

**Business Rules**:
- `role` must be "user", "assistant", or "system"
- User messages have `model_used = NULL`
- Assistant messages should have `model_used` populated
- Messages are ordered by `created_at` within a conversation
- Deleting a conversation deletes all messages (cascade)

**rx.Model Definition**:
```python
class Message(rx.Model, table=True):
    id: str
    conversation_id: str
    role: str  # "user" | "assistant" | "system"
    content: str
    created_at: datetime = datetime.utcnow()
    model_used: Optional[str] = None
    avatar_url: Optional[str] = None
```

---

## 3. chat_folders

**Purpose**: Organizational folders for grouping conversations

```sql
CREATE TABLE chat_folders (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_folders_name ON chat_folders(name);
```

**Columns**:
- `id` (TEXT, PK): UUID
- `name` (TEXT): Folder display name (e.g., "Job offers", "ESP32 projects")
- `created_at` (TIMESTAMP): Folder creation time

**Relationships**:
- Has many `conversations` (one-to-many via `conversations.folder_id`)

**Business Rules**:
- Folder names should be unique (enforced in application layer, not DB constraint)
- Deleting a folder sets `conversations.folder_id` to NULL (does NOT delete conversations)
- Empty folders are allowed

**rx.Model Definition**:
```python
class ChatFolder(rx.Model, table=True):
    id: str
    name: str
    created_at: datetime = datetime.utcnow()
```

---

## 4. Entity Relationship Diagram

```
chat_folders (1) ────────────── (0..N) conversations (1) ────────────── (0..N) messages
    id                                      id                                    id
    name                                    title                                 conversation_id (FK)
    created_at                              folder_id (FK)                        role
                                           created_at                            content
                                           updated_at                            created_at
                                                                                 model_used
                                                                                 avatar_url
```

**Cardinality**:
- One folder can have many conversations (0..N)
- One conversation belongs to zero or one folder (0..1)
- One conversation has many messages (1..N)
- One message belongs to exactly one conversation (1)

---

## 5. Sample Data

```sql
-- Sample folders
INSERT INTO chat_folders (id, name, created_at) VALUES
('folder-1', 'Job offers', '2026-04-01 10:00:00'),
('folder-2', 'ESP32 projects', '2026-04-01 10:00:00');

-- Sample conversations
INSERT INTO conversations (id, title, folder_id, created_at, updated_at) VALUES
('conv-1', 'CV update', 'folder-1', '2026-04-10 09:00:00', '2026-04-10 09:15:00'),
('conv-2', 'ESP32 overview', 'folder-2', '2026-04-12 14:00:00', '2026-04-12 14:30:00');

-- Sample messages
INSERT INTO messages (id, conversation_id, role, content, created_at, model_used) VALUES
('msg-1', 'conv-2', 'user', 'What is ESP32?', '2026-04-12 14:00:00', NULL),
('msg-2', 'conv-2', 'assistant', 'ESP32 is a low-cost microcontroller...', '2026-04-12 14:00:05', 'claude-sonnet-4-5');
```

---

## 6. Migration Commands

```bash
# Initialize Reflex database
reflex db init

# Create migration after model changes
reflex db migrate --message "Add Message and Conversation models"

# Apply migrations
reflex db migrate

# Check migration status
reflex db status

# Rollback last migration
reflex db downgrade -1
```

---

## 7. Query Patterns

### Get conversation with messages
```python
with rx.session() as session:
    conversation = session.query(Conversation).filter(Conversation.id == conv_id).first()
    messages = session.query(Message).filter(
        Message.conversation_id == conv_id
    ).order_by(Message.created_at).all()
```

### Get conversations in folder
```python
with rx.session() as session:
    conversations = session.query(Conversation).filter(
        Conversation.folder_id == folder_id
    ).order_by(Conversation.updated_at.desc()).all()
```

### Get all folders with conversation count
```python
with rx.session() as session:
    folders = session.query(ChatFolder).all()
    # Count conversations per folder in application code
```

---

## 8. Advanced Query Patterns

### 8.1 Get Recent Conversations with Last Message

**Scenario**: Display sidebar with conversation titles and previews

```python
from sqlalchemy import func
from mychat_reflex.features.chat.models import Conversation, Message

def get_recent_conversations_with_preview(limit: int = 20):
    """
    Get recent conversations with their last message text.

    Returns list of dicts: {conversation: Conversation, last_message: str, message_count: int}
    """
    with rx.session() as session:
        # Get conversations ordered by updated_at
        conversations = session.query(Conversation).order_by(
            Conversation.updated_at.desc()
        ).limit(limit).all()

        results = []
        for conv in conversations:
            # Get last message for preview
            last_msg = session.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at.desc()).first()

            # Get message count
            count = session.query(func.count(Message.id)).filter(
                Message.conversation_id == conv.id
            ).scalar()

            results.append({
                "conversation": conv,
                "last_message": last_msg.content[:50] + "..." if last_msg else "",
                "message_count": count
            })

        session.expunge_all()  # Detach from session
        return results
```

### 8.2 Search Messages by Content

**Scenario**: Global search across all conversations

```python
def search_messages(query: str, limit: int = 50):
    """
    Full-text search across all messages.

    Note: SQLite FTS (Full-Text Search) would be better for production.
    This is a simple LIKE query for MVP.
    """
    with rx.session() as session:
        messages = session.query(Message).filter(
            Message.content.like(f"%{query}%")
        ).order_by(Message.created_at.desc()).limit(limit).all()

        session.expunge_all()
        return messages
```

**Future: SQLite FTS5 Integration**
```sql
-- Create virtual table for full-text search
CREATE VIRTUAL TABLE messages_fts USING fts5(
    id UNINDEXED,
    content,
    content=messages,
    content_rowid=rowid
);

-- Triggers to keep FTS in sync
CREATE TRIGGER messages_ai AFTER INSERT ON messages BEGIN
  INSERT INTO messages_fts(rowid, content) VALUES (new.rowid, new.content);
END;

-- Search query
SELECT * FROM messages_fts WHERE content MATCH 'ESP32' ORDER BY rank;
```

### 8.3 Get Conversation Statistics

```python
from datetime import datetime, timedelta

def get_conversation_stats(conversation_id: str):
    """Get detailed statistics for a conversation."""
    with rx.session() as session:
        # Total messages
        total = session.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id
        ).scalar()

        # User vs AI message counts
        user_count = session.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id,
            Message.role == "user"
        ).scalar()

        ai_count = session.query(func.count(Message.id)).filter(
            Message.conversation_id == conversation_id,
            Message.role == "assistant"
        ).scalar()

        # First and last message timestamps
        first_msg = session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).first()

        last_msg = session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at.desc()).first()

        # Calculate duration
        if first_msg and last_msg:
            duration = last_msg.created_at - first_msg.created_at
        else:
            duration = timedelta(0)

        return {
            "total_messages": total,
            "user_messages": user_count,
            "ai_messages": ai_count,
            "first_message_at": first_msg.created_at if first_msg else None,
            "last_message_at": last_msg.created_at if last_msg else None,
            "duration": duration,
            "messages_per_hour": total / (duration.total_seconds() / 3600) if duration.total_seconds() > 0 else 0
        }
```

### 8.4 Batch Operations

**Scenario**: Delete old conversations

```python
def delete_old_conversations(days_old: int = 90):
    """
    Delete conversations older than X days.

    Messages will be cascade-deleted due to FK constraint.
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_old)

    with rx.session() as session:
        deleted = session.query(Conversation).filter(
            Conversation.updated_at < cutoff_date
        ).delete()

        session.commit()
        return deleted
```

**Scenario**: Move conversations to folder

```python
def move_conversations_to_folder(conversation_ids: list[str], folder_id: str):
    """Bulk move conversations to a folder."""
    with rx.session() as session:
        session.query(Conversation).filter(
            Conversation.id.in_(conversation_ids)
        ).update({"folder_id": folder_id}, synchronize_session=False)

        session.commit()
```

---

## 9. Database Optimization Strategies

### 9.1 Index Strategy

**Current Indexes** (from schema above):
```sql
-- Conversations
CREATE INDEX idx_conversations_folder_id ON conversations(folder_id);
CREATE INDEX idx_conversations_created_at ON conversations(created_at DESC);

-- Messages
CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_role ON messages(role);
```

**Additional Indexes for Production**:
```sql
-- Composite index for common query pattern
CREATE INDEX idx_messages_conv_created ON messages(conversation_id, created_at);

-- For search functionality
CREATE INDEX idx_messages_content_partial ON messages(content COLLATE NOCASE);

-- For filtering by model
CREATE INDEX idx_messages_model ON messages(model_used) WHERE model_used IS NOT NULL;
```

**Index Maintenance**:
```sql
-- Analyze query performance
EXPLAIN QUERY PLAN
SELECT * FROM messages WHERE conversation_id = 'conv-1' ORDER BY created_at;

-- Rebuild indexes (SQLite auto-maintains, rarely needed)
REINDEX;

-- Analyze table statistics
ANALYZE;
```

### 9.2 Query Optimization Patterns

**❌ Bad: N+1 Query Problem**
```python
# Don't do this! Causes N+1 queries
conversations = session.query(Conversation).all()
for conv in conversations:
    # Each iteration = 1 additional query!
    messages = session.query(Message).filter(
        Message.conversation_id == conv.id
    ).all()
```

**✅ Good: Eager Loading**
```python
from sqlalchemy.orm import joinedload

# Load conversations with messages in ONE query
conversations = session.query(Conversation).options(
    joinedload(Conversation.messages)
).all()
```

**✅ Better: Pagination**
```python
def get_messages_paginated(conversation_id: str, page: int = 1, page_size: int = 50):
    """Load messages in pages to reduce memory usage."""
    offset = (page - 1) * page_size

    with rx.session() as session:
        messages = session.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).offset(offset).limit(page_size).all()

        session.expunge_all()
        return messages
```

### 9.3 Connection Pooling

**Reflex Default** (handled automatically):
```python
# rxconfig.py
config = rx.Config(
    app_name="mychat_reflex",
    db_url="sqlite:///reflex.db",
    # Connection pool settings (if using PostgreSQL in production)
    # pool_size=10,
    # max_overflow=20,
    # pool_timeout=30,
)
```

**For Production (PostgreSQL)**:
```python
# Switch from SQLite to PostgreSQL for better concurrency
db_url = "postgresql://user:pass@localhost/mychat_db"
```

### 9.4 Caching Strategy

**Problem**: Repeated queries for same data waste resources

**Solution 1: Application-level caching**
```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache conversation metadata for 5 minutes
@lru_cache(maxsize=100)
def get_conversation_cached(conversation_id: str, cache_timestamp: int):
    """
    Cache conversation by ID.

    cache_timestamp is rounded to 5-minute intervals to invalidate cache.
    """
    with rx.session() as session:
        conv = session.query(Conversation).filter(
            Conversation.id == conversation_id
        ).first()
        session.expunge(conv)
        return conv

# Usage
cache_ts = int(datetime.utcnow().timestamp() / 300)  # Round to 5-min intervals
conversation = get_conversation_cached("conv-1", cache_ts)
```

**Solution 2: Reflex State caching**
```python
class ChatState(rx.State):
    _message_cache: dict[str, list[Message]] = {}

    def load_messages(self, conversation_id: str, force_refresh: bool = False):
        # Check cache first
        if not force_refresh and conversation_id in self._message_cache:
            self.messages = self._message_cache[conversation_id]
            return

        # Load from database
        with rx.session() as session:
            messages = session.query(Message).filter(...).all()
            session.expunge_all()

            # Update cache
            self._message_cache[conversation_id] = messages
            self.messages = messages
```

---

## 10. Data Migration Strategies

### 10.1 Schema Versioning

**Track schema version**:
```sql
CREATE TABLE schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description TEXT
);

INSERT INTO schema_version (version, description) VALUES
(1, 'Initial schema with conversations and messages'),
(2, 'Added chat_folders table'),
(3, 'Added model_used and avatar_url to messages');
```

### 10.2 Migration Scripts

**Alembic (Reflex uses this)**:
```bash
# Create migration
reflex db migrate --message "Add avatar_url to messages"

# Generated file: alembic/versions/xxx_add_avatar_url.py
def upgrade():
    op.add_column('messages', sa.Column('avatar_url', sa.String(), nullable=True))

def downgrade():
    op.drop_column('messages', 'avatar_url')
```

### 10.3 Data Backfill Pattern

**Example: Backfill model_used for old messages**

```python
def backfill_model_used():
    """
    Backfill model_used for old assistant messages.

    Assume all old messages used default model.
    """
    with rx.session() as session:
        # Find assistant messages without model_used
        messages = session.query(Message).filter(
            Message.role == "assistant",
            Message.model_used.is_(None)
        ).all()

        # Update in batches
        batch_size = 100
        for i in range(0, len(messages), batch_size):
            batch = messages[i:i+batch_size]
            for msg in batch:
                msg.model_used = "claude-sonnet-3-5"  # Default

            session.commit()
            print(f"Backfilled {min(i+batch_size, len(messages))} messages")
```

---

## 11. Database Monitoring & Debugging

### 11.1 Enable Query Logging

**SQLAlchemy logging**:
```python
import logging

# Enable SQL query logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

**Output**:
```
INFO:sqlalchemy.engine:BEGIN (implicit)
INFO:sqlalchemy.engine:SELECT messages.id, messages.content, ...
FROM messages WHERE messages.conversation_id = ?
INFO:sqlalchemy.engine:[generated in 0.00012s] ('conv-1',)
```

### 11.2 Query Performance Analysis

```python
import time

def analyze_query_performance():
    """Measure query execution time."""
    with rx.session() as session:
        start = time.time()

        # Your query here
        messages = session.query(Message).filter(
            Message.conversation_id == "conv-1"
        ).all()

        duration = time.time() - start
        print(f"Query took {duration*1000:.2f}ms, returned {len(messages)} rows")
```

### 11.3 Database Size Monitoring

```sql
-- Check table sizes (SQLite)
SELECT
    name,
    (SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name=m.name) as count
FROM sqlite_master m
WHERE type='table';

-- Vacuum to reclaim space
VACUUM;
```

---

## 12. Backup & Recovery

### 12.1 Backup Strategy

**SQLite Backup (Simple)**:
```bash
# Copy database file
cp reflex.db reflex_backup_$(date +%Y%m%d).db

# Or use SQLite backup command
sqlite3 reflex.db ".backup reflex_backup.db"
```

**Automated Backup Script**:
```python
import shutil
from datetime import datetime
import os

def backup_database():
    """Create timestamped database backup."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_dir = "backups"
    os.makedirs(backup_dir, exist_ok=True)

    source = "reflex.db"
    destination = f"{backup_dir}/reflex_{timestamp}.db"

    shutil.copy2(source, destination)
    print(f"Backup created: {destination}")

    # Keep only last 7 days of backups
    cleanup_old_backups(backup_dir, days=7)
```

### 12.2 Restore Procedure

```bash
# 1. Stop the application
pkill -f "reflex run"

# 2. Restore from backup
cp backups/reflex_20260412_120000.db reflex.db

# 3. Restart application
reflex run
```

### 12.3 Export to JSON (Portable Format)

```python
import json
from datetime import datetime

def export_conversations_to_json(output_file: str = "export.json"):
    """Export all conversations to JSON for portability."""
    with rx.session() as session:
        conversations = session.query(Conversation).all()

        export_data = []
        for conv in conversations:
            messages = session.query(Message).filter(
                Message.conversation_id == conv.id
            ).order_by(Message.created_at).all()

            export_data.append({
                "conversation": {
                    "id": conv.id,
                    "title": conv.title,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                },
                "messages": [
                    {
                        "id": msg.id,
                        "role": msg.role,
                        "content": msg.content,
                        "created_at": msg.created_at.isoformat(),
                        "model_used": msg.model_used,
                    }
                    for msg in messages
                ]
            })

        with open(output_file, 'w') as f:
            json.dump(export_data, f, indent=2)

        print(f"Exported {len(conversations)} conversations to {output_file}")
```

---

## 13. Security Considerations

### 13.1 SQL Injection Prevention

**✅ Reflex/SQLAlchemy handles this automatically**:
```python
# Safe - parameterized query
conversation_id = user_input  # Could be malicious
messages = session.query(Message).filter(
    Message.conversation_id == conversation_id  # ✅ Safe!
).all()
```

**❌ NEVER do raw SQL with user input**:
```python
# DANGEROUS! Do NOT do this!
query = f"SELECT * FROM messages WHERE conversation_id = '{user_input}'"
session.execute(query)  # ❌ SQL injection vulnerability!
```

### 13.2 Data Encryption at Rest

**SQLite with SQLCipher** (future enhancement):
```python
# Install: pip install sqlcipher3
from sqlcipher3 import dbapi2 as sqlite

# Encrypted database
db_url = "sqlite+pysqlcipher:///:memory:?cipher=aes-256-cfb&kdf_iter=64000"
```

### 13.3 Sensitive Data Handling

```python
# Do NOT store API keys in database!
class Message(rx.Model):
    content: str  # ✅ User content only
    # ❌ api_key: str  # NEVER store this!

# API keys should be in environment variables or secrets manager
```

---

## 14. Testing Database Operations

### 14.1 In-Memory Database for Tests

```python
# tests/conftest.py
import pytest
import reflex as rx

@pytest.fixture
def test_db():
    """Create in-memory database for each test."""
    # Override config to use in-memory DB
    test_config = rx.Config(db_url="sqlite:///:memory:")

    # Create tables
    with rx.session() as session:
        Message.metadata.create_all(session.bind)
        Conversation.metadata.create_all(session.bind)

    yield

    # Cleanup (automatic with :memory:)
```

### 14.2 Database Fixtures

```python
@pytest.fixture
def sample_conversation(test_db):
    """Create a sample conversation with messages."""
    with rx.session() as session:
        conv = Conversation(
            id="test-conv-1",
            title="Test Conversation"
        )
        session.add(conv)

        msg1 = Message(
            id="msg-1",
            conversation_id="test-conv-1",
            role="user",
            content="Hello"
        )
        msg2 = Message(
            id="msg-2",
            conversation_id="test-conv-1",
            role="assistant",
            content="Hi there!"
        )

        session.add_all([msg1, msg2])
        session.commit()

    return "test-conv-1"
```

### 14.3 Integration Test Example

```python
def test_load_conversation_messages(sample_conversation):
    """Test loading messages for a conversation."""
    with rx.session() as session:
        messages = session.query(Message).filter(
            Message.conversation_id == sample_conversation
        ).order_by(Message.created_at).all()

        assert len(messages) == 2
        assert messages[0].content == "Hello"
        assert messages[1].content == "Hi there!"
```
