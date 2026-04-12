"""
Knowledge Base State - UI Controller for Knowledge Base Feature.

This module contains KnowledgeBaseState (rx.State) which:
1. Manages notes/knowledge base UI state
2. Handles notes content and editing
3. Follows Rule #4: Feature Isolation (no cross-feature state dependencies)

Extracted from ChatState (Phase 4, Task 4.2)
"""

import logging
import reflex as rx

logger = logging.getLogger(__name__)


# ============================================================================
# KNOWLEDGE BASE STATE (UI CONTROLLER)
# ============================================================================


class KnowledgeBaseState(rx.State):
    """
    Knowledge Base State - The UI Controller for Notes/Knowledge Base.

    Responsibilities:
    - Manage notes content state
    - Handle notes editing and persistence
    - Maintain feature isolation (Rule #4)

    IMPORTANT: This follows Reflex's state management rules!
    - State variables are automatically reactive
    - Event handlers update state and trigger UI updates
    """

    # ========================================================================
    # UI STATE (Sent to Browser)
    # ========================================================================

    # Notes content
    notes_content: str = ""

    # ========================================================================
    # EVENT HANDLERS
    # ========================================================================

    def set_notes_content(self, value: str):
        """
        Update notes content.

        Args:
            value: New notes content
        """
        logger.info(f"[KnowledgeBaseState] Updating notes content: {len(value)} chars")
        self.notes_content = value
        # TODO: Add persistence to database when Notes model is implemented

    def clear_notes(self):
        """Clear all notes content."""
        logger.info("[KnowledgeBaseState] Clearing notes")
        self.notes_content = ""
