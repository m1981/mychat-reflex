"""
Reflex database configuration.

This module provides database configuration for the Reflex application.

Reflex Database Architecture:
----------------------------
Reflex uses SQLAlchemy under the hood, but provides rx.Model for simplified ORM.

Key differences from traditional SQLAlchemy:
1. rx.Model classes ARE the database tables (no separate ORM layer)
2. rx.Model instances ARE the domain entities (no mapping needed)
3. rx.Model instances ARE the UI state variables (no serialization needed)

This "unified model" approach eliminates the "Triple Model Tax":
- ❌ OLD: ORM Model → Domain Entity → UI State (3 classes!)
- ✅ NEW: rx.Model (1 class serves all 3 purposes!)

Database Sessions in Reflex:
----------------------------
Use rx.session() for database operations. CRITICAL RULES:

1. **Short-lived sessions**: Open, execute, close immediately
   ```python
   with rx.session() as session:
       session.add(message)
       session.commit()
   # Session is closed here
   ```

2. **NEVER hold session during async operations**:
   ```python
   # ❌ WRONG - Session held during 30-second LLM call!
   with rx.session() as session:
       save_user_message(session)
       response = await llm.stream()  # 30 seconds!
       save_ai_message(session)

   # ✅ CORRECT - Short-lived sessions
   with rx.session() as session:
       save_user_message(session)
   response = await llm.stream()
   with rx.session() as session:
       save_ai_message(session)
   ```

3. **Use in rx.State methods**:
   - Synchronous queries: Direct rx.session() usage
   - Async background tasks: rx.session() in @rx.background methods

Configuration:
--------------
Reflex automatically configures the database from rxconfig.py.
The database URL is set in the config file.

Models are defined in features/*/models.py using rx.Model.
"""

import reflex as rx


class DatabaseConfig:
    """
    Shared database configuration and utilities.

    This class provides centralized database configuration that can be
    used across all features.

    Note: Reflex handles database initialization automatically via rxconfig.py.
    This class is for shared utilities and documentation.
    """

    @staticmethod
    def get_db_url() -> str:
        """
        Get the database URL from Reflex config.

        Returns:
            str: Database connection URL
        """
        # Reflex config is loaded automatically
        # This is mainly for documentation/debugging
        return rx.config.get_config().db_url if hasattr(rx.config, "get_config") else ""


# Re-export rx.Model for convenience
Model = rx.Model

__all__ = ["DatabaseConfig", "Model"]
