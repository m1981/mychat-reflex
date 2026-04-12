"""
Workspace feature - Bounded context for chat organization.

This vertical slice contains:
- models.py: ChatFolder model (rx.Model)
- use_cases.py: CreateFolderUseCase, MoveChatUseCase, etc.
- state.py: WorkspaceState (rx.State)
- ui.py: sidebar(), folder_section(), chat_item()

Responsibilities:
- Organize chats into folders
- Display sidebar navigation
- Search and filter chats
- Create/rename/delete folders
"""

__all__ = []
