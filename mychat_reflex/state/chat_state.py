"""Chat application state management."""

from __future__ import annotations

import json
import httpx
import reflex as rx
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class Message(BaseModel):
    """A single chat message."""

    id: str
    content: str
    is_user: bool
    timestamp: str
    avatar_url: Optional[str] = None


class ChatFolder(BaseModel):
    """A folder containing chat conversations."""

    id: str
    name: str
    chats: list[str] = Field(default_factory=list)


class Chat(BaseModel):
    """A chat conversation."""

    id: str
    title: str
    folder_id: Optional[str] = None


class ChatState(rx.State):
    """Main chat application state (ViewModel)."""

    # --- ADR 014: Backend-Only Variables ---
    # Prefixed with '_' so Reflex does not serialize this to the browser
    _api_base_url: str = "http://localhost:8000"

    # UI State
    is_generating: bool = False

    # Current chat
    current_chat_id: str = "esp32-overview"
    current_chat_title: str = "ESP32 Overview"

    # Messages in current chat
    messages: list[Message] = [
        Message(
            id="1",
            content="Bądź specjalistą od projektowania CAD zwłaszcza kuchni na wymiar. Znasz się procesie obróbki CNC, materiałach i technologiach.",
            is_user=True,
            timestamp="6:15 PM 30 Mar 2026",
            avatar_url="https://i.pravatar.cc/150?img=11",
        ),
        Message(
            id="2",
            content="Cześć! Z przyjemnością wcielę się w tę rolę. Projektowanie i produkcja kuchni na wymiar to fascynujące połączenie inżynierii, ergonomii, designu i zaawansowanej technologii.\n\nOto kompleksowe zestawienie najważniejszych pojęć oraz krok po kroku opisany proces – od pierwszej kreski w programie CAD, aż po gotową kuchnię u klienta.",
            is_user=False,
            timestamp="6:15 PM 30 Mar 2026",
        ),
    ]

    # Folders and chats
    folders: list[ChatFolder] = [
        ChatFolder(
            id="job-offers", name="Job offers", chats=["cv-update", "email-prep"]
        ),
        ChatFolder(
            id="esp32", name="ESP32 projects", chats=["esp32-overview", "first-project"]
        ),
    ]

    chats: list[Chat] = [
        Chat(id="cv-update", title="CV update", folder_id="job-offers"),
        Chat(id="email-prep", title="Email preparation", folder_id="job-offers"),
        Chat(id="esp32-overview", title="ESP32 overview", folder_id="esp32"),
        Chat(id="first-project", title="First ESP project", folder_id="esp32"),
    ]

    # Input state
    input_text: str = ""

    # Search state
    sidebar_search: str = ""
    global_search: str = ""

    # UI state
    selected_model: str = "3.1 Pro Preview"

    # Notes
    notes_content: str = ""

    @rx.var
    def current_chat(self) -> Optional[Chat]:
        """Get the current chat object."""
        for chat in self.chats:
            if chat.id == self.current_chat_id:
                return chat
        return None

    @rx.var
    def filtered_folders(self) -> list[ChatFolder]:
        """Filter folders based on search."""
        if not self.sidebar_search:
            return self.folders
        search_lower = self.sidebar_search.lower()
        return [f for f in self.folders if search_lower in f.name.lower()]

    def set_input_text(self, value: str):
        """Update the input text."""
        self.input_text = value

    def set_sidebar_search(self, value: str):
        """Update sidebar search."""
        self.sidebar_search = value

    def set_global_search(self, value: str):
        """Update global search."""
        self.global_search = value

    def select_chat(self, chat_id: str):
        """Select a chat conversation."""
        self.current_chat_id = chat_id
        for chat in self.chats:
            if chat.id == chat_id:
                self.current_chat_title = chat.title
                break

    def send_message(self):
        """Handles user input and triggers the generation task."""
        if not self.input_text.strip() or self.is_generating:
            return

        # 1. Add User Message immediately (Optimistic UI update)
        user_msg = Message(
            id=f"msg-{len(self.messages) + 1}",
            content=self.input_text,
            is_user=True,
            timestamp=datetime.now().strftime("%I:%M %p %d %b %Y"),
            avatar_url="https://i.pravatar.cc/150?img=11",
        )
        self.messages.append(user_msg)

        # 2. Add empty AI Placeholder Message
        ai_msg_id = f"msg-{len(self.messages) + 1}"
        ai_msg = Message(
            id=ai_msg_id,
            content="",
            is_user=False,
            timestamp=datetime.now().strftime("%I:%M %p %d %b %Y"),
        )
        self.messages.append(ai_msg)

        # 3. Lock UI and clear input
        prompt = self.input_text
        self.input_text = ""
        self.is_generating = True

        # Yield immediately to push the user message and empty AI bubble to the UI
        yield

        # 4. Chain the streaming event handler
        yield ChatState.stream_response(prompt, ai_msg_id)

    async def stream_response(self, prompt: str, message_id: str):
        """
        Streams the response from the FastAPI backend.
        Every 'yield' automatically syncs the state to the frontend without blocking.
        """
        chat_id = self.current_chat_id
        api_url = f"{self._api_base_url}/chat/{chat_id}/stream"

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream(
                    "POST", api_url, json={"content": prompt}
                ) as response:
                    current_event = "message"

                    # Parse the Server-Sent Events (SSE) stream
                    async for line in response.aiter_lines():
                        line = line.strip()
                        if not line:
                            continue

                        if line.startswith("event:"):
                            current_event = line.split(":", 1)[1].strip()

                        elif line.startswith("data:"):
                            data_str = line.split(":", 1)[1].strip()
                            try:
                                data = json.loads(data_str)

                                # Find the AI message we are currently streaming into
                                msg_idx = next(
                                    (
                                        i
                                        for i, m in enumerate(self.messages)
                                        if m.id == message_id
                                    ),
                                    None,
                                )

                                if msg_idx is not None:
                                    if current_event == "status":
                                        self.messages[
                                            msg_idx
                                        ].content = f"_{data.get('message')}_\n\n"
                                        yield  # Push status to UI

                                    elif current_event == "sources_found":
                                        sources = data
                                        notes = "### Retrieved Sources\n\n"
                                        for idx, src in enumerate(sources):
                                            notes += f"**Source {idx + 1}:** {src.get('text')[:100]}...\n\n"
                                        self.notes_content = notes
                                        self.messages[msg_idx].content = ""
                                        yield  # Push notes panel update to UI

                                    elif current_event == "content_chunk":
                                        self.messages[msg_idx].content += data.get(
                                            "text", ""
                                        )
                                        yield  # Push text chunk to UI

                                    elif current_event == "error":
                                        self.messages[
                                            msg_idx
                                        ].content += (
                                            f"\n\n**Error:** {data.get('message')}"
                                        )
                                        yield  # Push error to UI

                            except json.JSONDecodeError:
                                pass  # Ignore malformed JSON chunks

        except Exception as e:
            msg_idx = next(
                (i for i, m in enumerate(self.messages) if m.id == message_id), None
            )
            if msg_idx is not None:
                self.messages[
                    msg_idx
                ].content += (
                    f"\n\n**Connection Error:** Could not reach backend ({str(e)})"
                )
                yield

        finally:
            # Unlock the UI when the stream finishes or fails
            self.is_generating = False
            yield

    # --- Restored Methods ---

    def create_new_chat(self):
        """Create a new chat conversation."""
        new_id = f"chat-{len(self.chats) + 1}"
        new_chat = Chat(id=new_id, title="New Chat")
        self.chats.append(new_chat)
        self.current_chat_id = new_id
        self.current_chat_title = "New Chat"
        self.messages = []

    def create_new_folder(self):
        """Create a new folder."""
        new_id = f"folder-{len(self.folders) + 1}"
        new_folder = ChatFolder(id=new_id, name="New Folder")
        self.folders.append(new_folder)

    def copy_message(self, message_id: str):
        """Copy message to clipboard (placeholder)."""
        pass

    def delete_message(self, message_id: str):
        """Delete a message."""
        self.messages = [m for m in self.messages if m.id != message_id]

    def regenerate_message(self, message_id: str):
        """Regenerate an AI response (placeholder)."""
        pass
