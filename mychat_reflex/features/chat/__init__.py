"""
Chat feature - Bounded context for conversation functionality.

This vertical slice contains:
- models.py: Message, Conversation models (rx.Model)
- use_cases.py: SendMessageUseCase, LoadHistoryUseCase
- state.py: ChatState (rx.State)
- ui.py: chat_area(), message_bubble(), chat_input()

Responsibilities:
- Send and receive messages
- Stream AI responses
- Display conversation history
- Message actions (copy, delete, regenerate)
"""

__all__ = []
