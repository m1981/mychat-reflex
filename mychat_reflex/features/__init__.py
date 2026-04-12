"""
Features module - Vertical Slice Architecture.

Each feature is a self-contained bounded context with:
- models.py: rx.Model classes (Database + Domain + UI unified)
- use_cases.py: Pure business logic
- state.py: rx.State controllers (handles UI + DB interactions)
- ui.py: Reflex components

Features:
- chat/: Core chat conversation functionality
- workspace/: Sidebar, folders, chat organization
"""

__all__ = []
