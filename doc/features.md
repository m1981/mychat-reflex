F1 - Chats should have URL that could be used to easily save in browser bookmarks or send someone to share.
F2 - Each chat can have different setting like: model, temperature, thinking budget, media resolution, URL context, Grounding with Google Maps.
F3 - Each conversation should have scroll positioning system (when user jumps between chats system always preserve position of last seen position in conversation (like in IDE editors when jumping between files)

F4 - Each chat should be

F5 - I need to see current cost for a conversation based on the input and output token count. (IF model does not provide tokens count in API we will use fast tokenizer regardless of provider. We don't have to be token perfect)


# Feature Specification

## Chat Interface



### 2. Chat Content Area

**Motivation**: Create a scrollable message container that automatically manages scroll position and provides visual feedback for errors and empty states.

**Description**: The main scrollable container that renders the message history, handles scroll behavior, and displays system notifications.

**Functional Requirements**:
- Render messages in chronological order
- Auto-scroll to bottom when new messages arrive
- Manual scroll support without breaking auto-scroll
- Smooth scrolling behavior

**Expected Results**:
- New messages automatically scroll into view unless user is reading history
- Users can manually scroll up to read history without interruption
- Empty state provides clear call-to-action
- Content width adapts to user preference

---

### 4. Generation Control

**Motivation**: Allow users to stop long-running AI responses to save time and API costs.

**Description**: A prominently displayed button that appears only during AI response generation, allowing immediate interruption.

**Functional Requirements**:
- Only visible when AI is generating a response
- Prominent placement (recommended: bottom center or near message input)
- Immediate response to user action
- Graceful handling of mid-stream cancellation
- State cleanup after cancellation

**Expected Results**:
- Users can stop unwanted responses immediately
- API streaming connections are properly closed
- Partial responses are preserved for reference
- UI returns to ready state after cancellation


### 6. Chat Export & Duplication


**Clone Functionality**:
- Duplicates entire chat including all messages
- Auto-generates unique title ("Copy of [Original Title]", "Copy of [Original Title] (2)", etc.)
- Inserts cloned chat at top of chat list
- Copies all configuration settings
- Assigns unique chat ID

**Expected Results**:
- Users can share chat screenshots easily
- Markdown exports are readable and properly formatted
- Cloned chats are immediately accessible
- No naming conflicts occur

---

### 7. Text Selection Enhancement

**Motivation**: Streamline the copy-paste workflow for users who frequently copy AI responses.

**Description**: Automatic clipboard integration when users select text within messages.

**Functional Requirements**:
- Auto-copy selected text to clipboard
- Visual feedback (toast notification) on successful copy
- Support both mouse drag selection and keyboard selection
- Scoped to message content area only (doesn't interfere with UI element selection)
- Works across all message types (user, assistant, system)

**Expected Results**:
- Users can copy text with a single gesture (select only)
- Clear confirmation that text was copied
- No interference with normal text selection behavior
- Consistent experience across browsers

## Message System

### 8. Message Display Component

**Motivation**: Create a flexible message rendering system that supports different message types and visual states while maintaining clarity and usability.

**Description**: A unified component that renders user, assistant, and system messages with role-based styling and interactive capabilities.

**Functional Requirements**:
- Three message types: User, Assistant (AI), System
- Role-specific visual indicators:
  - User: Person/user icon
  - Assistant: Provider-specific icon (OpenAI logo, Anthropic logo, etc.)
  - System: Settings/system icon
- Alternating background colors for visual separation
- Two view states: View mode (default) and Edit mode
- Responsive width matching chat layout settings
- For tall messages (>800px height recommended): duplicate action buttons at top and bottom
- Dynamic height calculation and adjustment
- Smooth transitions between view and edit modes

**Expected Results**:
- Users can immediately distinguish message sources
- Visual rhythm helps scan long conversations
- Action buttons remain accessible without scrolling
- Provider branding creates trust and clarity

---

### 9. Message Editing System

**Motivation**: Allow users to refine their prompts and correct mistakes without starting a new conversation.

**Description**: A comprehensive editing system that enables users to modify any message with automatic conversation truncation handling.

**Functional Requirements**:

**Edit Mode Activation**:
- Click "Edit" button on any message
- Enter edit mode with focused textarea
- Preserve original content as starting point
- ESC key to cancel and return to view mode

**Edit Capabilities**:
- Auto-resizing textarea (expands with content)
- File drop support (drag & drop files into textarea)
  - Image files: Converts to base64 data URLs
  - Text files: Inserts content inline
- Paste handler for images and files
- Keyboard shortcuts:
  - Ctrl/Cmd+Enter: Save and submit
  - ESC: Cancel editing
- Real-time character/line tracking (optional)

**Save Operations**:
1. **Save**: Updates message content only
2. **Save & Submit**: Updates and triggers AI response
3. **Save & Truncate**: Updates message and removes all subsequent messages (with confirmation)

**Conversation Truncation**:
- When editing a message that has responses after it
- Show confirmation modal: "This will remove all messages after this one. Continue?"
- On confirm: Remove all messages after edited message and optionally regenerate AI response
- On cancel: Return to edit mode

**Expected Results**:
- Users can iterate on prompts easily
- File attachments work seamlessly
- Truncation prevents conversation inconsistencies
- Clear warnings prevent accidental data loss

---

### 10. Message Content Rendering

**Motivation**: Display AI responses with rich formatting, code syntax highlighting, mathematical equations, and interactive diagrams.

**Description**: A sophisticated rendering engine that transforms markdown-formatted AI responses into beautifully formatted, interactive content.

**Functional Requirements**:

**Markdown Support**:
- GitHub Flavored Markdown (GFM) specification
- Headers (H1-H6)
- Bold, italic, strikethrough
- Ordered and unordered lists
- Block quotes
- Horizontal rules
- Tables with proper alignment
- Task lists (checkboxes)

**Code Rendering**:
- Inline code: `code` with monospace font and subtle background
- Fenced code blocks with language detection
- Syntax highlighting for 100+ languages
- Line numbers (optional)
- Language label display
- Copy button per code block
- Horizontal scroll for long lines

**Mathematical Equations**:
- Inline math: $equation$ using LaTeX syntax
- Display math blocks: $$equation$$ centered on own line
- Support for complex mathematical notation
- Use KaTeX or MathJax rendering engine

**Special Features**:
- Mermaid diagram rendering (see Feature #11)
- Whitespace preservation in paragraphs
- External links open in new tab
- Image embedding
- Lazy loading for performance (images, heavy content)

**Expected Results**:
- Technical content is readable and professional
- Code examples are easy to copy and understand
- Mathematical formulas render correctly
- Fast initial render even for long messages

---

### 11. Interactive Diagram Support (Mermaid)

**Motivation**: Enable visualization of flowcharts, diagrams, and graphs directly within chat responses for better comprehension.

**Description**: Automatic detection and rendering of Mermaid diagram syntax with export and editing capabilities.

**Functional Requirements**:

**Diagram Rendering**:
- Auto-detect Mermaid code blocks (```mermaid syntax)
- Supported diagram types:
  - Flowcharts
  - Sequence diagrams
  - Class diagrams
  - State diagrams
  - Entity Relationship diagrams
  - Gantt charts
  - Pie charts
  - Git graphs
- Custom theme configuration (recommended: "forest" or "default")
- HTML label support for rich text in nodes
- Interactive pan/zoom (optional)
- Security level configuration (prevent XSS)

**Export Options**:
1. **SVG Export**: Vector format, perfect quality at any size
2. **PNG Export**: Standard resolution raster image
3. **High-Resolution Export**:
   - 2x resolution JPEG
   - 4x resolution JPEG
   - Configurable quality (recommended: 95%)

**Editing Integration**:
- "Edit in Mermaid Live Editor" button
- Compress diagram state using lz-string
- Open in new tab at https://mermaid.live/edit
- Preserves diagram code and theme settings

**Source Code Toggle**:
- Collapsible section showing raw Mermaid code
- "Show diagram source" expandable details
- Syntax-highlighted code display
- Copy source code button

**Error Handling**:
- Graceful fallback when rendering fails
- Display error message with details
- Show raw code for user to debug
- Preserve content even if diagram fails

**Expected Results**:
- Complex processes visualized instantly
- High-quality exports for presentations
- Easy iteration using external editor
- No chat disruption on render errors

---

### 12. Message Action Controls

**Motivation**: Provide quick access to common message operations without cluttering the interface.

**Description**: Context-aware action buttons that appear on hover and adapt based on message type and position.

**Functional Requirements**:

**Available Actions**:
1. **Copy Message**: Copy message text to clipboard
   - Success feedback (checkmark icon or toast)
   - Preserves formatting (optional: plain text or markdown)

2. **Edit Message**: Enter edit mode for this message
   - Only for user messages (not AI responses)
   - Focus textarea automatically

3. **Delete Message**: Remove message from conversation
   - Confirmation dialog: "Delete this message?"
   - For user messages: May trigger truncation warning
   - For assistant messages: Simple deletion

4. **Regenerate Response**: Re-run AI generation
   - Only for last assistant message
   - Uses same prompt and settings
   - Replaces existing response

**UI Behavior**:
- Hidden by default
- Appear on message hover (desktop)
- Always visible on mobile or when message is focused
- Positioned top-right of message
- Tooltips on hover (optional)
- Keyboard accessible (Tab navigation)

**Conditional Display**:
- Copy: All messages
- Edit: User and System messages only
- Delete: All messages (with appropriate warnings)
- Regenerate: Last assistant message only

**Expected Results**:
- Clean interface when not needed
- Discoverable actions on interaction
- No accidental deletions
- Fast, responsive interactions

---

### 13. Message Insertion

**Motivation**: Allow users to inject new messages at any point in the conversation for role-playing, testing, or context injection.

**Description**: Floating action buttons between messages that enable insertion of new content at specific positions.

**Functional Requirements**:
- Insert button appears between every two messages
- Also appears before first message (if empty) and after last message
- Floating plus icon (+) or similar
- Click to create new message at that position
- If no chat exists, creates new chat first
- Opens in edit mode immediately
- Supports all message roles (user, assistant, system)

**Visual Design**:
- Subtle when not hovered (low opacity)
- Highlight on hover
- Position-aware (knows insertion index)
- Doesn't disrupt message flow

**Expected Results**:
- Users can add context anywhere in conversation
- Useful for role-playing scenarios (alternating speakers)
- System messages can be injected for meta-instructions
- Creates new chat seamlessly when needed

---

### 14. Code Block Features

**Motivation**: Make code snippets highly readable and easy to copy, with proper syntax highlighting.

**Description**: Specialized rendering for code blocks with language-specific highlighting and copy functionality.

**Functional Requirements**:

**Syntax Highlighting**:
- Auto-detect language from code fence (```python, ```javascript, etc.)
- Support 100+ programming languages
- Use Prism.js, highlight.js, or similar library
- Theme: Match application theme (dark/light mode)
- Line numbers (optional, recommended for long blocks)

**Language Indicator**:
- Display language name in top-right corner
- Small, unobtrusive label
- Helps users understand context

**Copy Functionality**:
- Copy button in top-right corner
- One-click copy of entire code block
- Success feedback (icon change: copy → checkmark)
- Preserves formatting and indentation
- Resets after 2 seconds

**Styling**:
- Dark theme: Dark background (#282c34 or similar)
- Light theme: Light background (#f6f8fa or similar)
- Monospace font (Consolas, Monaco, 'Courier New')
- Horizontal scroll for long lines (no wrapping)
- Proper padding and margins
- Border or shadow for definition

**Expected Results**:
- Code is immediately readable
- Language context is clear
- Copy operation is effortless
- Long code blocks remain accessible

## Configuration System

### 15. API Key Management

**Motivation**: Allow users to securely configure their own API keys for different AI providers without hardcoding credentials.

**Description**: A secure interface for managing API keys for multiple AI service providers with proper validation and storage.

**Functional Requirements**:

**Multi-Provider Support**:
- Support multiple providers (OpenAI, Anthropic, DeepInfra, etc.)
- Provider-specific input fields
- Provider logos/icons for easy identification
- Independent key management per provider

**Security Features**:
- Password-masked input fields (type="password")
- Keys stored in browser local storage (encrypted if possible)
- Never send keys to your backend (client-side only or proxy pattern)
- Clear visual indication when key is set vs. not set

**User Interface**:
- Modal or dedicated settings page
- Save/Cancel actions
- Validation on save (check key format)
- Test connection button (optional, recommended)
- Clear indication of required vs. optional providers

**Error Handling**:
- Invalid key format warnings
- API connection test results
- Clear error messages on auth failures
- Prompt to enter key if missing when attempting to use provider

**Expected Results**:
- Users control their own API access
- Keys are secure and never exposed
- Easy to update or change keys
- Clear feedback on key validity

---

### 16. Chat Configuration System

**Motivation**: Provide default settings for new chats while allowing per-chat customization of AI behavior.

**Description**: A two-tier configuration system with application-wide defaults and per-chat overrides.

**Functional Requirements**:

**Default Configuration**:
- Default system message (instructions for AI)
- Default provider selection (e.g., "Anthropic")
- Default model (e.g., "claude-sonnet-4-5")
- Default parameters:
  - Temperature (default: 0.7)
  - Max tokens (default: 4096)
  - Top P (default: 1.0)
  - Presence penalty (default: 0)
  - Frequency penalty (default: 0)

**System Message Editor**:
- Multi-line textarea
- Auto-expanding based on content
- Focus/blur height management (collapse when not focused)
- Character count (optional)
- Common presets dropdown (optional)

**Reset Functionality**:
- "Reset to Defaults" button
- Confirmation dialog
- Restores factory default configuration
- Preserves API keys

**Per-Chat Override**:
- Each chat can have custom settings
- Changes to defaults don't affect existing chats
- Visual indicator when chat uses custom settings

**Expected Results**:
- Consistent baseline behavior for new chats
- Flexibility to experiment per conversation
- Easy recovery from misconfiguration
- Clear distinction between defaults and overrides

---

### 17. Advanced Model Parameters

**Motivation**: Give advanced users fine-grained control over AI model behavior to optimize for different use cases.

**Description**: Comprehensive interface for adjusting AI model parameters with real-time validation and helpful guidance.

**Functional Requirements**:

**Provider & Model Selection**:
- Dropdown for AI provider (OpenAI, Anthropic, etc.)
- Dropdown for model (filtered by selected provider)
- Dynamic model list based on provider
- Display model capabilities (context length, features)

**Parameter Controls**:

1. **Max Tokens** (Response Length):
   - Slider or number input
   - Range: 100 to model-specific maximum
   - Shows remaining context window
   - Validation: Cannot exceed model limit
   - Description: "Maximum length of AI response"

2. **Temperature** (Creativity):
   - Slider: 0.0 to 2.0, step 0.1
   - Visual indicator: Cold (0) → Neutral (1) → Hot (2)
   - Description: "Higher = more creative/random, Lower = more focused/deterministic"
   - Default: 0.7

3. **Top P** (Nucleus Sampling):
   - Slider: 0.0 to 1.0, step 0.05
   - Description: "Cumulative probability threshold for token selection"
   - Default: 1.0
   - Advanced parameter (can be hidden by default)

4. **Presence Penalty**:
   - Slider: -2.0 to 2.0, step 0.1
   - Description: "Positive values penalize repetition of any tokens"
   - Default: 0.0
   - Advanced parameter

5. **Frequency Penalty**:
   - Slider: -2.0 to 2.0, step 0.1
   - Description: "Positive values penalize frequent tokens proportionally"
   - Default: 0.0
   - Advanced parameter

6. **Thinking Mode** (Provider-Specific):
   - Toggle switch
   - Only available for supported models (e.g., Claude with extended thinking)
   - Thinking budget tokens: Number input (e.g., 1000-32000)
   - Description: "Allow model to 'think' before responding"

**Validation & Constraints**:
- Real-time validation of all inputs
- Model-specific maximum enforcement
- Warning when approaching token limits
- Disable incompatible controls (e.g., thinking mode for OpenAI)

**Presets** (Optional):
- "Creative Writing" (high temperature)
- "Code Generation" (low temperature, high tokens)
- "Concise Answers" (low tokens, moderate temperature)
- Custom preset saving

**UI Organization**:
- Basic settings visible by default
- Advanced settings in collapsible section
- Tooltips on hover for all parameters
- "What's this?" links to documentation

**Expected Results**:
- Advanced users can fine-tune model behavior
- Beginners can use sensible defaults
- No invalid configurations possible
- Clear understanding of each parameter's effect

---

### 18. Provider Architecture

**Motivation**: Create a flexible, extensible system for supporting multiple AI providers with different APIs and capabilities.

**Description**: A provider registry pattern that abstracts provider-specific API differences behind a common interface.

**Functional Requirements**:

**Provider Registry**:
- Centralized registration of available providers
- Provider capabilities metadata:
  - Supported models list
  - Max tokens per model
  - Special features (thinking mode, vision, tools)
  - Pricing information (input/output costs)
  - API endpoint(s)

**Provider Interface** (Common Contract):
- `formatRequest(messages, config)`: Transform standard request to provider format
- `parseResponse(response)`: Transform provider response to standard format
- `parseStreamingResponse(chunk)`: Handle streaming responses
- `validateConfig(config)`: Validate configuration for this provider
- `getDefaultModel()`: Return default model for this provider

**Supported Providers** (Example):
1. **Anthropic**:
   - Models: Claude Sonnet 4.5, Claude Haiku 4.5, etc.
   - Features: Extended thinking, 200K context
   - API format: Messages API

2. **OpenAI**:
   - Models: GPT-4, GPT-4 Turbo, GPT-3.5 Turbo
   - Features: Function calling, JSON mode
   - API format: Chat Completions API

3. **DeepInfra** (or other alternatives):
   - Models: Various open-source models
   - Cost-effective alternative

**Provider Switching**:
- Switch providers mid-conversation
- Automatic model validation on switch
- Parameter compatibility checking
- Clear indication of active provider

**Extensibility**:
- Easy to add new providers (implement interface)
- No changes to core chat logic required
- Provider-specific features opt-in

**Expected Results**:
- Users can choose preferred provider
- Easy migration between providers
- Consistent behavior across providers
- Simple to add new providers in future

## Content Organization

### 19. Prompt Library

**Motivation**: Allow users to save and reuse common instructions, templates, and system messages across chats.

**Description**: A library system for storing, managing, and importing reusable prompt templates.

**Functional Requirements**:

**Prompt Structure**:
- Each prompt has:
  - Unique ID (UUID)
  - Name/title (searchable)
  - Prompt content (multi-line text)

**CRUD Operations**:
1. **Create**: Add new prompt with name and content
2. **Read**: View all prompts in library
3. **Update**: Edit name or content of existing prompt
4. **Delete**: Remove prompt from library

**User Interface**:
- Modal or dedicated page
- Table or card layout
- Two columns: Name | Prompt Content
- Auto-expanding textareas for editing
- Focus/blur height management (compact when not editing)
- Search/filter functionality (optional)

**Import/Export**:
- **Export**: Download prompts as CSV file
  - Format: `name,prompt` (two columns)
  - Filename: `prompts-YYYY-MM-DD.csv`
- **Import**: Upload CSV file to bulk-add prompts
  - Validates CSV format
  - Merges with existing prompts
  - Shows success/error feedback

**Usage Integration**:
- Quick insert into system message field
- Apply to current chat
- Preview before applying

**Expected Results**:
- Users build library of reusable prompts over time
- Easy sharing of prompts via CSV
- Quick experimentation with different instruction sets
- Consistent prompt structure across chats

---

### 20. Token Usage & Cost Tracking

**Motivation**: Help users understand API costs and optimize token usage to stay within budgets.

**Description**: Real-time token counting and cost estimation based on provider pricing models.

**Functional Requirements**:

**Token Counting**:
- Count tokens for entire conversation (all messages)
- Use model-specific tokenizers:
  - OpenAI models: Use `cl100k_base` encoding (tiktoken)
  - Anthropic models: Use `cl100k_base` + 10% buffer
  - Other providers: Appropriate tokenizer
- Real-time updates as messages are added
- Display total token count prominently

**Cost Calculation**:
- Provider-specific pricing:
  - Input tokens: $/1K tokens
  - Output tokens: $/1K tokens (usually higher)
- Estimation strategy:
  - Assume 80% input tokens, 20% output tokens (before generation)
  - After generation: Use actual token counts if available from API
- Currency conversion (optional): USD → Local currency
- Cost per message (optional)
- Total conversation cost

**Display Format**:
- **Token count**: "1,234 tokens"
- **Estimated cost**: "$0.05" or "€0.05"
- **Visual indicator**:
  - Green: Low usage (<50% of typical limit)
  - Yellow: Medium usage (50-80%)
  - Red: High usage (>80% of limit)

**Update Behavior**:
- Update on message add/edit/delete
- Pause updates during AI generation (for performance)
- Resume and refresh after generation completes
- Memoize calculations to avoid redundant computation

**Token Limit Warnings**:
- Warning when approaching model's context limit
- Suggestion to summarize or start new chat
- Disable send button if over limit

**Expected Results**:
- Users aware of API costs in real-time
- Early warning before hitting context limits
- Informed decisions about conversation length
- Budget tracking for API usage

## Navigation & Organization

### 21. Sidebar Menu System

**Motivation**: Provide a persistent navigation panel for managing multiple conversations while conserving screen space.

**Description**: A collapsible sidebar containing chat history, folders, search, and settings access.

**Functional Requirements**:

**Layout & Behavior**:
- Fixed width: 260-290px when expanded
- Collapsible with smooth transitions (200-300ms)
- Desktop: Hover to reveal toggle button
- Mobile: Overlay mode (3/4 screen width, 75vw)
- Mobile: Backdrop overlay (semi-transparent black) to focus attention
- Fixed positioning with proper z-index layering
- Supports dark and light themes

**Desktop Interaction**:
- Toggle button appears on hover
- Click to collapse/expand
- Keyboard shortcut (optional, e.g., Ctrl+B)
- State persists across sessions

**Mobile Interaction**:
- Menu icon in mobile bar opens sidebar
- Backdrop dismisses sidebar on click
- Swipe gesture to dismiss (optional)
- Close button in sidebar

**Expected Results**:
- Desktop users can reclaim space when focusing
- Mobile users get full-screen chat experience
- Smooth, professional animations
- State persists as expected

---

### 22. Chat Search & Filtering

**Motivation**: Help users quickly find specific conversations in large chat histories.

**Description**: Real-time search functionality that filters chats by title and content.

**Functional Requirements**:

**Search Capabilities**:
- Search by chat title (primary)
- Search within message content (secondary)
- Real-time filtering (updates as user types)
- Debounced search (500ms delay to reduce lag)
- Case-insensitive matching

**User Interface**:
- Search input field at top of sidebar
- Clear/reset button (X icon) when search active
- Result count display (optional): "3 of 45 chats"
- Highlight matching text (optional)

**Filter Behavior**:
- Hide non-matching chats
- Hide empty folders (folders with no matching chats)
- Preserve folder structure for matches
- Auto-expand folders containing matches

**State Management**:
- Disabled during AI generation (prevent conflicts)
- Clears when sidebar closed (optional)
- Persists during session (optional)

**Expected Results**:
- Users can find old conversations instantly
- Search responds quickly even with 100+ chats
- Folder organization aids discovery
- No performance issues with large histories

---

### 23. Chat Organization System

**Motivation**: Organize conversations into folders for easier management and navigation.

**Description**: A hierarchical folder system with drag-and-drop capabilities and visual customization.

**Functional Requirements**:

**Creating Chats**:
- "New Chat" button prominently displayed
- Creates chat in root (no folder) or within current folder
- Disabled during AI generation
- Keyboard shortcut (optional, e.g., Ctrl+N)
- Accessibility labels for screen readers

**Creating Folders**:
- "New Folder" button (desktop only, optional on mobile)
- Auto-incrementing names: "New Folder", "New Folder 2", etc.
- UUID-based unique identifiers
- Collision-free naming algorithm
- Disabled during generation

**Chat History List**:
- Scrollable container
- Displays folders (collapsible) and root-level chats
- Preserves folder expanded/collapsed state
- Loading state (skeleton or spinner)
- Empty state: "No chats yet"
- Error handling with user-friendly messages

**Chat History Items**:
- Active chat highlighted (background color, border)
- Chat title display with overflow handling (gradient fade)
- Active indicator (dot or icon)
- Click to switch to chat
- Inline title editing:
  - Double-click or Edit button
  - Auto-focus input
  - Enter to save, Escape to cancel
  - Validation (no empty titles)
- Delete with confirmation dialog
- Drag handle for reordering
- Disabled during generation

**Folder Features**:
1. **Expand/Collapse**: Click folder header to toggle
2. **Rename**: Inline editing like chat titles
3. **Delete**: Removes folder but moves chats to root (not deleted)
4. **Color Customization**:
   - Circular color wheel picker (HSL-based)
   - 60px radius SVG circle
   - Mouse angle detection for color selection
   - Preview on hover
   - "Remove color" option to reset
   - Theme-aware (adapts to dark/light mode)
   - Dimming effect on hover
5. **Drag & Drop**:
   - Drag chats into folders
   - Drag folders to reorder them
   - Auto-expand folder when chat hovers over it (for drop)
   - Visual feedback (hover state, drop zone highlighting)

**Drag & Drop Interactions**:
- Drag chat → Drop in folder: Move chat to folder
- Drag chat → Drop in root area: Remove from folder
- Drag folder → Drop between folders: Reorder folders
- Prevent dragging during generation
- Smooth animations for all operations

**Expected Results**:
- Users can organize hundreds of chats efficiently
- Visual customization (colors) aids quick recognition
- Drag & drop feels natural and responsive
- No accidental deletions
- Folder state persists across sessions

## Settings & Preferences

### 24. Application Settings

**Motivation**: Centralize all user preferences in one location for easy discovery and management.

**Description**: A comprehensive settings interface for theme, layout, behavior, and integrations.

**Functional Requirements**:

**Settings Panel**:
- Modal or dedicated page
- Organized sections (Appearance, Behavior, Advanced)
- Save/Cancel actions
- "Reset to Defaults" option
- Keyboard navigation (Tab, Enter)

**Settings Categories**:

1. **Appearance**:
   - **Theme Selector**: Light/Dark mode toggle
     - Icon-based UI (Sun icon for light, Moon for dark)
     - Applies system-wide immediately
     - Persists across sessions
   - **Layout Width**: Normal (40%) vs. Wide (55%)
     - Button-based selection or toggle
     - Visual preview (optional)
     - Active state highlighting
     - Affects message and content width

2. **Behavior**:
   - **Enter to Submit**: Toggle Enter key behavior
     - ON: Enter sends message, Shift+Enter for new line
     - OFF: Enter for new line, Ctrl+Enter to send
     - Helps mobile users (often want OFF)
   - **Auto Title Generation**: Toggle automatic chat naming
     - ON: AI generates title from first message
     - OFF: User must manually name chats
     - Saves API costs when OFF

3. **Integrations**:
   - **Language Selector**: Dropdown for interface language
     - Supported languages list (English, Spanish, Polish, etc.)
     - Language code to name mapping
     - Changes all UI text immediately
     - Persists selection
   - **API Configuration**: Link to API key management
   - **Prompt Library**: Link to prompt management

**Expected Results**:
- Users can customize app to preferences
- Settings changes apply immediately
- All preferences persist across sessions
- Easy to reset if confused

---

### 25. Mobile-First Navigation

**Motivation**: Provide a dedicated navigation bar for mobile users since sidebar is hidden by default.

**Description**: A mobile-only top bar with essential navigation controls.

**Functional Requirements**:

**Visibility**:
- Visible only on mobile devices (hidden on desktop via media query)
- Breakpoint: <768px (mobile/tablet)
- Sticky positioning at top of viewport (stays visible while scrolling)

**Controls**:
1. **Menu Toggle**: Opens sidebar
   - Hamburger icon (three lines)
   - Left-aligned
   - Opens sidebar in overlay mode
   - Screen reader label: "Open menu"

2. **Chat Title Display**: Shows current chat name
   - Center-aligned
   - Truncate long titles with ellipsis
   - Scrollable if title exceeds width
   - Max height: 2-3 lines

3. **New Chat Button**: Quick chat creation
   - Right-aligned
   - Plus (+) icon
   - Disabled during AI generation
   - Creates chat and focuses input

**State Management**:
- All buttons disabled during generation (visual feedback)
- Chat title updates when switching chats
- Integrates with sidebar state

**Expected Results**:
- Mobile users have easy access to navigation
- Current context (chat title) always visible
- Quick actions available without opening sidebar
- No wasted screen space on desktop

---

### 26. Internationalization (i18n)

**Motivation**: Make the application accessible to users worldwide in their native languages.

**Description**: Multi-language support system with runtime language switching.

**Functional Requirements**:

**Language Support**:
- English (default)
- Additional languages: Spanish, French, German, Polish, Japanese, Chinese, etc.
- JSON-based translation files (one per language)
- Namespace organization (common, chat, settings, etc.)

**Language Selector UI**:
- Dropdown component
- Shows language name in native script:
  - English (English)
  - Español (Spanish)
  - 日本語 (Japanese)
- Current selection highlighted
- Persists in local storage

**Translation System**:
- Use i18n library (i18next, vue-i18n, etc.)
- Runtime language switching (no page reload)
- Fallback to English for missing translations
- Pluralization support (1 message vs. 2 messages)
- Date/time formatting per locale

**Coverage**:
- All UI labels and buttons
- Error messages and notifications
- Tooltips and help text
- Placeholder text
- Settings descriptions

**Expected Results**:
- Users can use app in preferred language
- Language switches instantly
- No broken layouts due to text length differences
- Professional translations (not machine-translated)

---

## UI Components & Patterns

### 27. Reusable UI Components

**Motivation**: Maintain consistency and reduce development time with a component library.

**Description**: Standard UI components used throughout the application.

**Components**:

1. **Toggle Switch**:
   - Checkbox-based implementation
   - Animated slide transition (150-200ms)
   - Optional label (left or right of switch)
   - Active state: Green indicator
   - Supports dark and light themes
   - Accessible (keyboard navigable, ARIA labels)

2. **Modal System**:
   - Portal-based rendering (renders outside DOM hierarchy)
   - Backdrop click to dismiss (configurable)
   - Custom close handlers
   - Action buttons:
     - Confirm (primary)
     - Cancel (optional, secondary)
   - Scrollable content area for long content
   - Centered positioning (vertical and horizontal)
   - Custom title and message support
   - Children content support (any content)
   - Dark mode support
   - Escape key to dismiss
   - Focus trap (keyboard navigation stays in modal)

3. **Toast Notifications**:
   - Non-blocking notifications
   - Appears top-right (or configurable position)
   - Auto-dismiss after 3-5 seconds
   - Types: Success, Error, Info, Warning
   - Icon per type
   - Dismiss button
   - Multiple toasts stack vertically
   - Smooth enter/exit animations

**Design Principles**:
- Consistent spacing and sizing
- Theme-aware (dark/light mode)
- Accessible (ARIA labels, keyboard navigation)
- Smooth animations (60fps)
- Hover states and visual feedback

**Expected Results**:
- Consistent look and feel across app
- Familiar interaction patterns
- Accessible to all users
- Professional polish

---

### 28. Responsive Design System

**Motivation**: Deliver excellent experience on any device from mobile phones to desktop monitors.

**Description**: Comprehensive responsive design patterns and breakpoints.

**Breakpoints**:
- Mobile: 0-639px
- Tablet: 640-1023px
- Desktop: 1024px+
- Wide desktop: 1280px+ (optional enhancements)

**Responsive Patterns**:

1. **Layout Adaptation**:
   - Mobile: Single column, full-width
   - Tablet: Adaptive (sidebar overlay)
   - Desktop: Two-column (sidebar + chat)

2. **Auto-Expanding Textareas**:
   - Start at single line (or 3 lines)
   - Expand with content (up to max height)
   - Collapse on blur (optional)
   - Focus/blur height management

3. **Text Overflow Handling**:
   - Long text: Ellipsis (...) with tooltip on hover
   - Gradient fade: For chat titles, folder names
   - Scrollable: For code blocks, wide content

4. **Touch-Friendly Targets**:
   - Minimum tap target: 44x44px (iOS guidelines)
   - Spacing between tappable elements: 8px minimum
   - No hover-only interactions on mobile

**Accessibility**:
- ARIA labels on all interactive elements
- Screen reader support
- Keyboard navigation (Tab, Enter, Escape)
- Focus visible indicators
- Color contrast ratios (WCAG AA minimum)

**Performance**:
- Lazy loading for images and heavy components
- Virtual scrolling for long lists (optional)
- Debounced search and auto-save
- Memoization to prevent unnecessary re-renders

**Expected Results**:
- App works well on any device
- No horizontal scrolling on mobile
- Fast, responsive interactions
- Accessible to users with disabilities

---

### 29. Development Tools

**Motivation**: Provide developers with debugging tools during development without impacting production.

**Description**: A debug panel with real-time state monitoring and logging controls.

**Functional Requirements**:

**Visibility**:
- Only in development mode (hidden in production)
- Toggle visibility (keyboard shortcut, e.g., Ctrl+Shift+D)
- Fixed position overlay (doesn't obstruct main UI)

**Information Displayed**:
- Render count tracking (performance monitoring)
- Generation state (idle, generating, error)
- Active chat index and total chat count
- Message count in current chat
- Cursor position (line/column in textarea)
- Scroll position and reading estimate
- Element IDs and focus tracking

**Logging System**:
- Module-based logging (ui, tokens, focus, etc.)
- Selectable modules (checkboxes)
- Log level filtering (debug, info, warn, error)
- Console integration
- Timestamp on all logs

**Interaction Tracking**:
- Mouse movement coordinates
- Selection change events
- Keyboard events
- Focus/blur events

**Expected Results**:
- Developers can debug issues quickly
- Performance bottlenecks visible
- No impact on production bundle size
- Helps understand app behavior


---

## Data Management & Persistence

### 30. State Persistence

**Motivation**: Preserve user data across browser sessions and prevent data loss.

**Description**: Client-side storage system for chats, settings, and user data.

**Functional Requirements**:

**Storage Strategy**:
- Use browser's Local Storage API
- JSON serialization for complex objects
- Namespace keys to avoid conflicts (e.g., "app-state-v2")

**Persisted Data**:
1. **Chat History**: All chats with messages
2. **Folders**: Folder structure and metadata
3. **Settings**: Theme, language, layout preferences
4. **API Keys**: Securely stored (consider encryption)
5. **Prompts**: Saved prompt library
6. **UI State**: Sidebar open/closed, folder expanded states

**Storage Considerations**:
- Local Storage limit: ~5-10MB (browser-dependent)
- Monitor storage usage
- Warning when approaching limit (e.g., at 80%)
- Compression for large datasets (optional)

**Data Migration**:
- Version number in stored data
- Migration functions for schema changes
- Backward compatibility for old data formats

**Error Handling**:
- Quota exceeded: Show user-friendly error
- Corrupt data: Reset to defaults with confirmation
- Failed writes: Retry mechanism or error notification

**Expected Results**:
- User data survives page refresh
- Settings persist across sessions
- Graceful handling of storage limits
- No data loss on normal usage

---

### 31. Import/Export System

**Motivation**: Allow users to backup data, share conversations, and migrate between devices.

**Description**: Comprehensive data export and import functionality.

**Functional Requirements**:

**Chat Export**:
- **Individual Chat**:
  - Markdown format (.md file)
  - PNG image (see Feature #6)
  - JSON format (full data with metadata)
- **All Chats**:
  - JSON file with all conversations
  - Organized by folders
  - Includes metadata (timestamps, config)

**Chat Import**:
- Upload JSON file
- Validate format and version
- Merge with existing chats or replace all
- Preserve folder structure
- Conflict resolution (duplicate chat IDs)

**Prompt Library Export/Import**:
- CSV format (name, prompt columns)
- Compatible with spreadsheet software
- Bulk operations

**Settings Export/Import**:
- JSON file with all settings
- Useful for setting up new device
- Excludes API keys (security)

**Expected Results**:
- Users can backup important conversations
- Easy migration to new device or browser
- Share conversations with colleagues
- Recover from data loss

---

## Implementation Notes for Developers

### Architecture Recommendations

**State Management**:
- Use centralized state management (Redux, Zustand, Pinia, etc.)
- Organize state into slices:
  - Chat Slice: Chats, messages, current chat
  - Config Slice: Settings, theme, layout
  - Auth Slice: API keys
  - Prompt Slice: Prompt library
  - UI Slice: Sidebar state, modals

**Provider Pattern**:
- Abstract AI provider logic behind common interface
- Factory pattern for creating provider instances
- Registry pattern for provider lookup
- Strategy pattern for request formatting

**Service Layer**:
- **ChatSubmissionService**: Handles API calls to AI providers
- **TitleService**: Auto-generates chat titles
- **StorageService**: Manages local storage operations
- **TokenizerFactory**: Provider-specific token counting

**Component Organization**:
```
components/
├── Chat/
│   ├── ChatContent/
│   │   ├── Message/
│   │   │   ├── ViewMode/
│   │   │   ├── EditMode/
│   │   │   └── CodeBlock/
│   │   └── ...
│   └── ...
├── Menu/
│   ├── ChatHistory/
│   ├── ChatFolder/
│   └── ...
├── Settings/
└── Common/ (reusable components)
```

---

### API Integration

**Streaming Response Handling**:
```
1. Client sends request to your backend endpoint
2. Backend forwards to AI provider API
3. Stream chunks back to client
4. Client updates UI incrementally
5. Handle stream interruption gracefully
```

**Token Counting**:
- Use provider-specific tokenizers
- Count before sending (for validation)
- Update from API response (actual usage)
- Apply provider-specific buffers (Anthropic: +10%)

**Error Handling**:
- Network errors: Retry with exponential backoff
- Rate limits: Show clear message, suggest waiting
- Invalid API key: Redirect to settings
- Quota exceeded: Show cost estimation, suggest optimization

---

### Performance Optimization

**Critical Optimizations**:
1. **Lazy Loading**:
   - Code highlighting library
   - Mermaid diagram renderer
   - Heavy components (Settings, Prompt Library)

2. **Memoization**:
   - Token count calculations
   - Expensive renders (Markdown, code blocks)
   - Search/filter results

3. **Debouncing**:
   - Search input (500ms)
   - Auto-save (1000ms)
   - Scroll event handlers (100ms)

4. **Virtual Scrolling** (for 1000+ chats):
   - Render only visible chat items
   - Improves sidebar performance

5. **Code Splitting**:
   - Split by route (if multi-page)
   - Split large libraries
   - Lazy load modals

**Bundle Size Targets**:
- Initial load: <300KB (gzipped)
- Total JS: <1MB (gzipped)
- Individual chunks: <100KB

---

### Security Considerations

**API Key Security**:
- Never send API keys to your backend (unless using proxy pattern)
- If using proxy: Implement rate limiting and authentication
- Client-side: Store encrypted if possible
- Warn users about browser extensions that can read storage

**XSS Prevention**:
- Sanitize user input before storage
- Mermaid diagrams: Use "loose" security level with caution
- Markdown rendering: Use trusted libraries only
- CSP headers in production

**Data Privacy**:
- Clear disclaimer that data is stored locally
- Option to clear all data
- No telemetry without consent
- API calls go directly to provider (or through your secure proxy)

---

### Testing Strategy

**Unit Tests**:
- Utility functions (token counting, formatting)
- State management (reducers, actions)
- Component logic (hooks, helpers)
- Coverage target: 80%+

**Integration Tests**:
- Chat creation flow
- Message editing and submission
- Folder organization (drag & drop)
- Search functionality
- Import/export operations

**E2E Tests** (Critical Paths):
- New user onboarding
- Send first message
- Multi-turn conversation
- Switch between chats
- Export chat

**Visual Regression Tests**:
- Use Backstop.js, Percy, or similar
- Test light/dark themes
- Mobile and desktop layouts
- Component states (hover, focus, disabled)

---

### Deployment Considerations

**Environment Variables**:
```
VITE_DEFAULT_PROVIDER=anthropic
VITE_API_PROXY_URL=https://your-proxy.com (if using proxy)
VITE_ENABLE_DEBUG=false (production)
VITE_SENTRY_DSN=... (error tracking)
```

**Build Configuration**:
- Production build with minification
- Source maps for debugging (upload to error tracking service)
- Tree shaking to remove unused code
- Asset optimization (images, fonts)

**Hosting**:
- Static site hosting (Vercel, Netlify, Cloudflare Pages)
- CDN for fast global delivery
- HTTPS required (for security and features like clipboard API)
- Custom domain (optional)

**Monitoring**:
- Error tracking (Sentry, Rollbar)
- Analytics (optional, privacy-focused)
- Performance monitoring (Web Vitals)
- User feedback mechanism

---

## Summary

This specification describes a comprehensive AI chat application with 31 major features covering:

- **Chat Interface** (Features 1-7): Core chat experience
- **Message System** (Features 8-14): Rich message rendering and editing
- **Configuration** (Features 15-18): AI provider and model management
- **Organization** (Features 19-20): Prompts and token tracking
- **Navigation** (Features 21-23): Sidebar and chat organization
- **Settings** (Features 24-26): User preferences and i18n
- **UI Components** (Features 27-29): Reusable components and responsive design
- **Data Management** (Features 30-31): Persistence and import/export

### Technology-Agnostic Implementation

This specification can be implemented in:
- **Reflex** (Python): Use Reflex state management, components, and event handlers
- **React** (JavaScript/TypeScript): Use hooks, context, and component libraries
- **Vue** (JavaScript/TypeScript): Use composition API, Pinia, and component libraries
- **Svelte** (JavaScript/TypeScript): Use stores, components, and reactive statements
- **Angular** (TypeScript): Use services, components, and RxJS

The core concepts—state management, component hierarchy, event handling, and data flow—translate across frameworks.

### Key Success Metrics

- **Performance**: First Contentful Paint < 1.5s, Time to Interactive < 3s
- **Usability**: Users can send first message within 30 seconds of landing
- **Reliability**: 99.9% uptime, zero data loss
- **Accessibility**: WCAG AA compliance, keyboard navigation, screen reader support
- **Mobile**: Full functionality on devices as small as 320px width

### Next Steps for Implementation

1. Set up project structure and development environment
2. Implement state management and data layer
3. Build core UI components (Modal, Toggle, etc.)
4. Implement message rendering and chat interface
5. Add provider integration and API handling
6. Implement organization features (folders, search)
7. Add settings and preferences
8. Optimize for performance and bundle size
9. Add comprehensive testing
10. Deploy and monitor

---

*End of Feature Specification*
