<!--
LLM INSTRUCTION BLOCK
MOTIVATION: This file defines the "How" for a specific internal module or service. It enforces Clean Architecture and Dependency Inversion. It is DESCRIPTIVE.
CONTENTS: Layer, Responsibility, Inputs, Outputs, Injected Interfaces, and Concrete Dependencies.
DO'S:
- DO keep it concise. This should take a human 2 minutes to read.
- DO strictly separate Injected Interfaces (Ports) from Concrete Dependencies (Adapters).
DON'TS:
- DO NOT allow Application/Domain layers to depend on Concrete Infrastructure (e.g., a Use Case cannot depend on `chromadb`).
-->

# ⚙️ [Component/Service Name]

**Target Path:** `src/features/[feature_name]/[layer]/[filename].py`
**Description:** [One sentence technical description of what this module does.]

## Contract Definitions

*   **Layer:** [Domain | Application (Use Case) | Infrastructure (Adapter) | Presentation (API)]
*   **Responsibility:** [What is the single responsibility of this module?]
*   **Input:** `[Data Type]` - [Description]
*   **Output:** `[Data Type]` - [Description]
*   **Throws/Errors:** `[Exception Types]`

## Dependencies (Dependency Inversion)
*   **Injected Interfaces (Ports):** 
    *   🔌 `[Interface Name, e.g., IVectorStore]` - [Why it's needed]
*   **Concrete Dependencies (Only allowed if Infrastructure/Presentation):**
    *   📦 `[Library/DB, e.g., chromadb, fastapi, sqlalchemy]`