import reflex as rx

# FIXME (Phase 4): extract WorkspaceState, remove this import
from mychat_reflex.features.chat.state import ChatState
from ...ui.primitives import T, nav_item, footer_btn, text_input


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
    return rx.el.li(
        nav_item(
            rx.icon(
                "message-square",
                size=14,
                class_name=f"mr-2 flex-shrink-0 {T['text_faint']}",
            ),
            rx.el.span(chat.title),
            on_click=ChatState.select_chat(chat.id),
        ),
        class_name="list-none",
    )


def folder_header(folder: rx.Var) -> rx.Component:
    return rx.el.p(
        folder.name,
        class_name=(
            f"text-[11px] font-semibold uppercase tracking-wider "
            f"px-3 mb-1.5 mt-3 {T['text_muted']}"
        ),
    )


def navigation_list() -> rx.Component:
    return rx.el.nav(
        rx.el.p(
            "Chats",
            class_name=(
                f"text-[11px] font-semibold uppercase tracking-wider "
                f"px-3 mb-1.5 mt-3 {T['text_muted']}"
            ),
        ),
        rx.el.ul(
            rx.foreach(ChatState.chats, chat_item),
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
                rx.foreach(ChatState.filtered_folders, folder_header),
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
