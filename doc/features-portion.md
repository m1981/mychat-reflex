I need to first agree on requirements. Please analyze them then check against current architecture and API above
If you need clarifications please ask questions!!!!



### F22. Chat Search & Filtering

**Motivation**: Help users quickly find specific conversations in large chat histories.

**Description**: Real-time search functionality that filters chats by title and content.

**Functional Requirements**:

**Search Capabilities**:
- Search by chat title (primary)
- Search within message content (secondary)
- Real-time filtering (updates as user types)
- Debounced search (500ms delay to reduce lag)
- Case-insensitive matching






Index: src/core/di.py
IDEA additional info:
Subsystem: com.intellij.openapi.diff.impl.patch.CharsetEP
<+>UTF-8
===================================================================
diff --git a/src/core/di.py b/src/core/di.py
new file mode 100644
--- /dev/null	(date 1775336495726)
+++ b/src/core/di.py	(date 1775336495726)
@@ -0,0 +1,46 @@
+# File: src/core/di.py
+import os
+from fastapi import Depends
+from sqlalchemy.ext.asyncio import AsyncSession
+
+from src.core.database.session import get_db
+from src.infrastructure.database.conversation_repo import SQLAlchemyConversationRepo
+from src.infrastructure.vector_store.mock_adapter import MockVectorStore
+from src.infrastructure.llm.openai_adapter import OpenAIAdapter
+from src.features.chat.domain.services.prompt_builder import RAGPromptBuilder
+from src.features.chat.use_cases.send_message import SendMessageUseCase
+
+# --- Providers ---
+
+def get_conversation_repo(session: AsyncSession = Depends(get_db)) -> SQLAlchemyConversationRepo:
+    return SQLAlchemyConversationRepo(session)
+
+def get_vector_store() -> MockVectorStore:
+    return MockVectorStore()
+
+def get_llm_service() -> OpenAIAdapter:
+    # In a real app, load this from .env using python-dotenv or pydantic-settings
+    api_key = os.getenv("OPENAI_API_KEY", "your-api-key-here")
+    return OpenAIAdapter(api_key=api_key, model="gpt-4o-mini")
+
+def get_prompt_builder() -> RAGPromptBuilder:
+    return RAGPromptBuilder()
+
+# --- Main Use Case Injection ---
+
+def get_send_message_use_case(
+    repo: SQLAlchemyConversationRepo = Depends(get_conversation_repo),
+    vector_store: MockVectorStore = Depends(get_vector_store),
+    llm: OpenAIAdapter = Depends(get_llm_service),
+    prompt_builder: RAGPromptBuilder = Depends(get_prompt_builder)
+) -> SendMessageUseCase:
+    """
+    Wires together the Clean Architecture Use Case.
+    FastAPI will automatically resolve all dependencies in the tree.
+    """
+    return SendMessageUseCase(
+        conversation_repo=repo,
+        vector_store=vector_store,
+        llm_service=llm,
+        prompt_builder=prompt_builder
+    )
\ No newline at end of file
Index: src/infrastructure/vector_store/mock_adapter.py
IDEA additional info:
Subsystem: com.intellij.openapi.diff.impl.patch.CharsetEP
<+>UTF-8
===================================================================
diff --git a/src/infrastructure/vector_store/mock_adapter.py b/src/infrastructure/vector_store/mock_adapter.py
new file mode 100644
--- /dev/null	(date 1775336478829)
+++ b/src/infrastructure/vector_store/mock_adapter.py	(date 1775336478829)
@@ -0,0 +1,13 @@
+# File: src/infrastructure/vector_store/mock_adapter.py
+import asyncio
+from typing import List
+from src.core.domain.interfaces import IVectorStore
+from src.core.domain.entities import SearchResult
+
+class MockVectorStore(IVectorStore):
+    async def search(self, query: str, limit: int = 5) -> List[SearchResult]:
+        await asyncio.sleep(1) # Simulate network delay
+        return [
+            SearchResult(id="1", text="ESP32 is a low-cost microcontroller with Wi-Fi.", score=0.9),
+            SearchResult(id="2", text="It is widely used in IoT projects.", score=0.85)
+        ]
\ No newline at end of file
Index: mychat_reflex/state/chat_state.py
IDEA additional info:
Subsystem: com.intellij.openapi.diff.impl.patch.CharsetEP
<+>UTF-8
===================================================================
diff --git a/mychat_reflex/state/chat_state.py b/mychat_reflex/state/chat_state.py
--- a/mychat_reflex/state/chat_state.py	(revision 5e5ce2debc0836d50090fc677c7bcbbff3246864)
+++ b/mychat_reflex/state/chat_state.py	(date 1775335914017)
@@ -41,7 +41,7 @@

     # --- ADR 014: Backend-Only Variables ---
     # Prefixed with '_' so Reflex does not serialize this to the browser
-    _api_base_url: str = "http://localhost:8000"
+    _api_base_url: str = "http://localhost:8080"

     # UI State
     is_generating: bool = False
@@ -163,25 +163,32 @@
         self.input_text = ""
         self.is_generating = True

-        # Yield immediately to push the user message and empty AI bubble to the UI
+        print("[DEBUG] Yielding optimistic UI update...")
         yield

-        # 4. Chain the streaming event handler
+        print(f"[DEBUG] Chaining stream_response for msg_id: {ai_msg_id}...")
         yield ChatState.stream_response(prompt, ai_msg_id)

     async def stream_response(self, prompt: str, message_id: str):
-        """
-        Streams the response from the FastAPI backend.
-        Every 'yield' automatically syncs the state to the frontend without blocking.
-        """
+        """Streams the response from the FastAPI backend."""
+        print(f"[DEBUG] stream_response started. Prompt: '{prompt}'")
+
         chat_id = self.current_chat_id
         api_url = f"{self._api_base_url}/chat/{chat_id}/stream"
+        print(f"[DEBUG] Target API URL: {api_url}")

         try:
             async with httpx.AsyncClient(timeout=60.0) as client:
-                async with client.stream(
-                    "POST", api_url, json={"content": prompt}
-                ) as response:
+                print("[DEBUG] Sending POST request to backend...")
+
+                async with client.stream("POST", api_url, json={"content": prompt}) as response:
+                    print(f"[DEBUG] HTTP Response Status: {response.status_code}")
+
+                    # CRITICAL FIX: Catch 404s, 500s, and port conflicts!
+                    if response.status_code != 200:
+                        error_text = await response.aread()
+                        raise Exception(f"HTTP {response.status_code}: {error_text.decode('utf-8')[:100]}")
+
                     current_event = "message"

                     # Parse the Server-Sent Events (SSE) stream
@@ -190,6 +197,8 @@
                         if not line:
                             continue

+                        print(f"[DEBUG] Received SSE Line: {line}") # Log raw stream data
+
                         if line.startswith("event:"):
                             current_event = line.split(":", 1)[1].strip()

@@ -216,11 +225,7 @@
                                         yield  # Push status to UI

                                     elif current_event == "sources_found":
-                                        sources = data
-                                        notes = "### Retrieved Sources\n\n"
-                                        for idx, src in enumerate(sources):
-                                            notes += f"**Source {idx + 1}:** {src.get('text')[:100]}...\n\n"
-                                        self.notes_content = notes
+                                        self.notes_content = "### Retrieved Sources\n\n" + str(data)
                                         self.messages[msg_idx].content = ""
                                         yield  # Push notes panel update to UI

@@ -239,22 +244,17 @@
                                         yield  # Push error to UI

                             except json.JSONDecodeError:
-                                pass  # Ignore malformed JSON chunks
+                                print(f"[DEBUG] Failed to parse JSON: {data_str}")

         except Exception as e:
-            msg_idx = next(
-                (i for i, m in enumerate(self.messages) if m.id == message_id), None
-            )
+            print(f"[ERROR] stream_response failed: {str(e)}")
+            msg_idx = next((i for i, m in enumerate(self.messages) if m.id == message_id), None)
             if msg_idx is not None:
-                self.messages[
-                    msg_idx
-                ].content += (
-                    f"\n\n**Connection Error:** Could not reach backend ({str(e)})"
-                )
+                self.messages[msg_idx].content += f"\n\n**Connection Error:** {str(e)}"
                 yield

         finally:
-            # Unlock the UI when the stream finishes or fails
+            print("[DEBUG] stream_response finished. Unlocking UI.")
             self.is_generating = False
             yield

Index: src/infrastructure/database/conversation_repo.py
IDEA additional info:
Subsystem: com.intellij.openapi.diff.impl.patch.CharsetEP
<+>UTF-8
===================================================================
diff --git a/src/infrastructure/database/conversation_repo.py b/src/infrastructure/database/conversation_repo.py
new file mode 100644
--- /dev/null	(date 1775336458187)
+++ b/src/infrastructure/database/conversation_repo.py	(date 1775336458187)
@@ -0,0 +1,76 @@
+# File: src/infrastructure/database/conversation_repo.py
+import json
+import uuid
+from typing import List, Union
+from sqlalchemy.ext.asyncio import AsyncSession
+from sqlalchemy import select
+
+from src.core.domain.interfaces import IConversationRepo
+from src.core.domain.entities import ChatMessage, Role, TextPart, ImagePart, DocumentPart
+from src.core.database.models import Conversation, Message as DBMessage
+
+
+class SQLAlchemyConversationRepo(IConversationRepo):
+    def __init__(self, session: AsyncSession):
+        self.session = session
+
+    async def save_message(self, conversation_id: str, role: Role, content: Union[str, list]) -> str:
+        # 1. Ensure conversation exists
+        conv = await self.session.get(Conversation, conversation_id)
+        if not conv:
+            conv = Conversation(id=conversation_id, title="New Chat")
+            self.session.add(conv)
+
+        # 2. Handle ADR 009: Polymorphic Content Serialization
+        if isinstance(content, list):
+            # Convert Pydantic parts to JSON string for the DB Text column
+            db_content = json.dumps([part.model_dump() for part in content])
+        else:
+            db_content = content
+
+        # 3. Create ORM Model
+        msg_id = str(uuid.uuid4())
+        db_msg = DBMessage(
+            id=msg_id,
+            conversation_id=conversation_id,
+            role=role,
+            content=db_content
+        )
+        self.session.add(db_msg)
+        await self.session.commit()
+
+        return msg_id
+
+    async def get_history(self, conversation_id: str) -> List[ChatMessage]:
+        # 1. Query ORM Models
+        stmt = select(DBMessage).where(DBMessage.conversation_id == conversation_id).order_by(DBMessage.created_at)
+        result = await self.session.execute(stmt)
+        db_messages = result.scalars().all()
+
+        domain_messages = []
+
+        # 2. ADR 005: Map ORM Models to Pure Domain Models
+        for db_msg in db_messages:
+            parsed_content = db_msg.content
+
+            # Attempt to deserialize JSON back into Polymorphic parts
+            if parsed_content.strip().startswith("["):
+                try:
+                    raw_list = json.loads(parsed_content)
+                    parts = []
+                    for item in raw_list:
+                        if item.get("type") == "text":
+                            parts.append(TextPart(**item))
+                        elif item.get("type") == "image":
+                            parts.append(ImagePart(**item))
+                        elif item.get("type") == "document":
+                            parts.append(DocumentPart(**item))
+                    parsed_content = parts
+                except json.JSONDecodeError:
+                    pass  # It was just a normal string that happened to start with '['
+
+            domain_messages.append(
+                ChatMessage(role=db_msg.role, content=parsed_content)
+            )
+
+        return domain_messages
\ No newline at end of file
Index: src/main.py
IDEA additional info:
Subsystem: com.intellij.openapi.diff.impl.patch.CharsetEP
<+>UTF-8
===================================================================
diff --git a/src/main.py b/src/main.py
new file mode 100644
--- /dev/null	(date 1775336618141)
+++ b/src/main.py	(date 1775336618141)
@@ -0,0 +1,29 @@
+# File: src/main.py
+import uvicorn
+from contextlib import asynccontextmanager
+from fastapi import FastAPI
+from fastapi.middleware.cors import CORSMiddleware
+
+from src.features.chat.presentation.routes import router as chat_router
+from src.core.database.session import init_db
+
+# Lifespan event to create DB tables on startup
+@asynccontextmanager
+async def lifespan(app: FastAPI):
+    await init_db()
+    yield
+
+app = FastAPI(title="Super Chat API", lifespan=lifespan)
+
+app.add_middleware(
+    CORSMiddleware,
+    allow_origins=["http://localhost:3000", "http://localhost:8000"],
+    allow_credentials=True,
+    allow_methods=["*"],
+    allow_headers=["*"],
+)
+
+app.include_router(chat_router)
+
+if __name__ == "__main__":
+    uvicorn.run("src.main:app", host="0.0.0.0", port=8080, reload=True)
\ No newline at end of file
Index: src/core/database/session.py
IDEA additional info:
Subsystem: com.intellij.openapi.diff.impl.patch.CharsetEP
<+>UTF-8
===================================================================
diff --git a/src/core/database/session.py b/src/core/database/session.py
new file mode 100644
--- /dev/null	(date 1775336384522)
+++ b/src/core/database/session.py	(date 1775336384522)
@@ -0,0 +1,19 @@
+# File: src/core/database/session.py
+from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
+from .models import Base
+
+# ADR 004: Using SQLite for the Modular Monolith
+DATABASE_URL = "sqlite+aiosqlite:///./superchat.db"
+
+engine = create_async_engine(DATABASE_URL, echo=False)
+AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
+
+async def init_db():
+    """Creates all tables in the SQLite database."""
+    async with engine.begin() as conn:
+        await conn.run_sync(Base.metadata.create_all)
+
+async def get_db() -> AsyncSession:
+    """FastAPI dependency to get a database session."""
+    async with AsyncSessionLocal() as session:
+        yield session
\ No newline at end of file
