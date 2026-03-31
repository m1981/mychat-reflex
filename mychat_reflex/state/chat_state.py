"""Chat application state management."""

from __future__ import annotations

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
    """Main chat application state."""

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
            avatar_url="https://i.pravatar.cc/150?img=11"
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
        ChatFolder(id="job-offers", name="Job offers", chats=["cv-update", "email-prep"]),
        ChatFolder(id="esp32", name="ESP32 projects", chats=["esp32-overview", "first-project"]),
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
        """Send a new message."""
        if not self.input_text.strip():
            return

        # Add user message
        new_message = Message(
            id=str(len(self.messages) + 1),
            content=self.input_text,
            is_user=True,
            timestamp=datetime.now().strftime("%I:%M %p %d %b %Y"),
            avatar_url="https://i.pravatar.cc/150?img=11"
        )
        self.messages.append(new_message)
        self.input_text = ""

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
