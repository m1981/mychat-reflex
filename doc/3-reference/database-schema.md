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
