import reflex as rx

# FIXME (Phase 4): extract WorkspaceState, remove this import
from mychat_reflex.features.chat.state import ChatState
from ...ui.primitives import T, nav_item, footer_btn, text_input
from ...ui.draggable import drag_div, drag_li

# Reflex 0.8: chain rx.prevent_default with state handlers on dragover/drop
# so the browser actually accepts the drop (HTML5 spec requirement).
_PREVENT = rx.prevent_default


def sidebar_header() -> rx.Component:
    return rx.el.div(
        rx.el.h2(
            "Super Chat",
            class_name=f"text-lg font-semibold tracking-tight {T['text_primary']}",
        ),
        class_name=f"px-5 py-4 border-b {T['border_divider']}",
    )


def action_buttons() -> rx.Component:
    return rx.el.div(
        # New chat — filled indigo pill
        rx.el.button(
            rx.icon("plus", size=15),
            rx.el.span("New chat"),
            on_click=ChatState.create_new_chat,
            class_name=(
                f"flex-1 flex justify-center items-center gap-2 "
                f"py-2 px-4 rounded-full text-sm font-medium "
                f"cursor-pointer transition-colors {T['btn_primary']}"
            ),
        ),
        # New folder — ghost square
        rx.el.button(
            rx.icon("folder-plus", size=15),
            on_click=ChatState.create_new_folder,
            class_name=(
                f"p-2 rounded-full border cursor-pointer transition-colors {T['btn_ghost_square']}"
            ),
        ),
        class_name="px-4 py-3 flex gap-2 items-center",
    )


def sidebar_search() -> rx.Component:
    return rx.el.div(
        text_input(
            placeholder="Search",
            value=ChatState.sidebar_search,
            on_change=ChatState.set_sidebar_search,
        ),
        class_name="px-4 mb-3",
    )


def chat_item(chat: rx.Var) -> rx.Component:
    """Draggable chat row."""
    is_dragging = ChatState.dragged_chat_id == chat.id
    return drag_li(
        nav_item(
            rx.icon(
                "grip-vertical",
                size=12,
                class_name=f"mr-1 flex-shrink-0 opacity-40 group-hover:opacity-100 {T['text_faint']}",
            ),
            rx.icon(
                "message-square",
                size=14,
                class_name=f"mr-2 flex-shrink-0 {T['text_faint']}",
            ),
            rx.el.span(chat.title, class_name="truncate"),
            on_click=ChatState.select_chat(chat.id),
        ),
        # HTML5 drag source
        draggable=True,
        on_drag_start=ChatState.start_drag_chat(chat.id),
        on_drag_end=ChatState.end_drag_chat,
        class_name=rx.cond(
            is_dragging,
            "list-none opacity-40",
            "list-none",
        ),
    )


def folder_drop_zone(folder: rx.Var) -> rx.Component:
    """A folder rendered as a drop target, with its child chats listed below.

    `folder` is a dict {id, name, chats}.
    """
    is_active = ChatState.drag_over_folder_id == folder["id"]
    is_dragging_anything = ChatState.dragged_chat_id != ""

    return rx.el.div(
        # Folder header (drop target)
        drag_div(
            rx.icon(
                "folder",
                size=13,
                class_name=f"mr-2 flex-shrink-0 {T['text_muted']}",
            ),
            rx.el.span(
                folder["name"],
                class_name=(
                    f"text-[11px] font-semibold uppercase tracking-wider "
                    f"{T['text_muted']}"
                ),
            ),
            rx.el.span(
                folder["chats"].length(),
                class_name=(
                    f"ml-auto text-[10px] font-medium px-1.5 py-0.5 rounded-full "
                    f"{T['text_faint']}"
                ),
            ),
            # Drop target wiring
            on_drag_over=[
                ChatState.set_drag_over_folder(folder["id"]),
                _PREVENT,
            ],
            on_drag_leave=ChatState.clear_drag_over_folder,
            on_drop=[
                ChatState.drop_chat_on_folder(folder["id"]),
                _PREVENT,
            ],
            class_name=rx.cond(
                is_active,
                # Active drop highlight
                "flex items-center px-3 py-1.5 mt-3 mb-1.5 rounded-md "
                "ring-2 ring-indigo-400/70 bg-indigo-500/10 transition-all",
                rx.cond(
                    is_dragging_anything,
                    # Hint mode: subtle dashed outline so user sees drop targets
                    "flex items-center px-3 py-1.5 mt-3 mb-1.5 rounded-md "
                    "border border-dashed border-indigo-400/30 transition-all",
                    "flex items-center px-3 py-1.5 mt-3 mb-1.5 rounded-md",
                ),
            ),
        ),
        # Chats inside this folder
        rx.el.ul(
            rx.foreach(folder["chats"], chat_item),
            class_name="space-y-0.5 ml-2 border-l border-dashed border-white/5 pl-2",
        ),
        class_name="",
    )


def unfiled_drop_zone() -> rx.Component:
    """The 'Chats' header doubles as a drop target that removes a chat from
    its current folder (folder_id -> None)."""
    is_active = ChatState.drag_over_folder_id == "__root__"
    is_dragging_anything = ChatState.dragged_chat_id != ""
    return drag_div(
        rx.el.span("Chats"),
        rx.cond(
            is_dragging_anything,
            rx.el.span(
                "← drop here to unfile",
                class_name="ml-2 normal-case font-normal opacity-60",
            ),
            rx.fragment(),
        ),
        on_drag_over=[
            ChatState.set_drag_over_folder("__root__"),
            _PREVENT,
        ],
        on_drag_leave=ChatState.clear_drag_over_folder,
        on_drop=[
            ChatState.drop_chat_on_folder(""),  # "" = unfiled
            _PREVENT,
        ],
        class_name=rx.cond(
            is_active,
            f"text-[11px] font-semibold uppercase tracking-wider "
            f"px-3 py-1 mb-1.5 mt-3 rounded-md "
            f"ring-2 ring-indigo-400/70 bg-indigo-500/10 transition-all "
            f"{T['text_muted']}",
            rx.cond(
                is_dragging_anything,
                f"text-[11px] font-semibold uppercase tracking-wider "
                f"px-3 py-1 mb-1.5 mt-3 rounded-md "
                f"border border-dashed border-indigo-400/30 transition-all "
                f"{T['text_muted']}",
                f"text-[11px] font-semibold uppercase tracking-wider "
                f"px-3 mb-1.5 mt-3 {T['text_muted']}",
            ),
        ),
    )


def navigation_list() -> rx.Component:
    return rx.el.nav(
        unfiled_drop_zone(),
        rx.el.ul(
            rx.foreach(ChatState.unfiled_chats, chat_item),
            class_name="space-y-0.5",
        ),
        rx.cond(
            ChatState.folders.length() > 0,
            rx.el.div(
                rx.el.p(
                    "Folders",
                    class_name=(
                        f"text-[11px] font-semibold uppercase tracking-wider "
                        f"px-3 mb-1.5 mt-3 {T['text_muted']}"
                    ),
                ),
                rx.foreach(ChatState.folders_with_chats, folder_drop_zone),
            ),
        ),
        class_name="flex-1 overflow-y-auto px-2 pb-4",
    )


def sidebar_footer() -> rx.Component:
    return rx.el.div(
        rx.color_mode.button(size="2", cursor="pointer"),
        footer_btn(
            rx.icon("settings", size=16),
            rx.el.span("Settings"),
        ),
        footer_btn(
            rx.el.div(
                class_name=(
                    f"w-6 h-6 rounded-full border flex items-center justify-center {T['avatar_circle']}"
                ),
            ),
            rx.el.span("Michal"),
        ),
        class_name=f"px-3 py-3 border-t space-y-1 {T['border_divider']}",
    )


def sidebar() -> rx.Component:
    return rx.el.aside(
        sidebar_header(),
        action_buttons(),
        sidebar_search(),
        navigation_list(),
        sidebar_footer(),
        class_name=(
            f"w-[260px] flex-shrink-0 flex flex-col h-full border-r "
            f"{T['sidebar_root']} {T['border']}"
        ),
    )
