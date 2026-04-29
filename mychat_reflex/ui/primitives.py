"""
ui/primitives.py

Primitive component building blocks.

Rules:
- rx.el.* only — no rx.button, no rx.box — zero Radix style bleed
- dark: variants work because tailwind.config.js uses darkMode: "class"
  and Reflex writes the .dark class on <html> when color mode toggles
- Radix components (rx.popover, rx.switch, rx.select, rx.slider) are
  imported here for behaviour only; their *triggers* always use rx.el.button
"""

import reflex as rx
from typing import Optional, Callable

# ============================================================================
# DESIGN TOKENS
# All theme-aware classes live here. Import T in feature files, never
# write dark: strings inline in feature code.
# ============================================================================

T: dict[str, str] = {
    # ── Surfaces ─────────────────────────────────────────────────────────────
    "surface_app": "bg-white dark:bg-zinc-950",
    "surface_raised": "bg-zinc-50 dark:bg-zinc-900",
    "surface_hover": "hover:bg-zinc-100 dark:hover:bg-zinc-800",
    "surface_hover_soft": "hover:bg-zinc-50 dark:hover:bg-zinc-900/50",
    # ── Borders ───────────────────────────────────────────────────────────────
    "border": "border-zinc-200 dark:border-zinc-800",
    "border_divider": "border-zinc-200 dark:border-zinc-800",
    # ── Text ──────────────────────────────────────────────────────────────────
    "text_primary": "text-zinc-900 dark:text-zinc-100",
    "text_secondary": "text-zinc-600 dark:text-zinc-400",
    "text_muted": "text-zinc-500 dark:text-zinc-500",
    "text_faint": "text-zinc-400 dark:text-zinc-500",
    "placeholder": "placeholder-zinc-400 dark:placeholder-zinc-500",
    # ── Accent (indigo) ───────────────────────────────────────────────────────
    "accent_text": "text-indigo-600 dark:text-indigo-400",
    "accent_pill": (
        "text-indigo-600 bg-indigo-50 hover:bg-indigo-100 "
        "dark:text-indigo-300 dark:bg-indigo-500/10 dark:hover:bg-indigo-500/20"
    ),
    "item_active_blue": (
        "bg-indigo-50 text-indigo-700 font-medium "
        "dark:bg-indigo-500/10 dark:text-indigo-300"
    ),
    "item_active_amber": (
        "bg-amber-50 text-amber-700 font-medium "
        "dark:bg-amber-500/10 dark:text-amber-300"
    ),
    "item_inactive": "text-zinc-700 dark:text-zinc-300",
    # ── Inputs ────────────────────────────────────────────────────────────────
    "input": (
        "w-full rounded-lg py-1.5 px-3 text-sm border outline-none transition focus:ring-2 "
        "bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400 "
        "focus:border-indigo-400 focus:ring-indigo-100 "
        "dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 "
        "dark:focus:border-indigo-500 dark:focus:ring-indigo-500/10"
    ),
    # ── Toolbar primitives ────────────────────────────────────────────────────
    "pill_btn": (
        "h-8 px-3 rounded-full border flex items-center gap-1.5 flex-shrink-0 "
        "cursor-pointer transition-colors select-none "
        "border-zinc-200 text-zinc-700 hover:bg-zinc-50 hover:border-zinc-300 "
        "dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:border-zinc-600"
    ),
    "icon_btn": (
        "h-8 w-8 rounded-full border flex items-center justify-center "
        "flex-shrink-0 cursor-pointer transition-colors select-none "
        "border-zinc-200 text-zinc-600 hover:bg-zinc-50 "
        "dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
    ),
    "icon_btn_square": (
        "h-8 w-8 rounded-md flex items-center justify-center "
        "flex-shrink-0 cursor-pointer transition-colors select-none"
    ),
    # ── Nav items ─────────────────────────────────────────────────────────────
    "nav_item": (
        "w-full text-left bg-transparent rounded-lg text-sm font-normal "
        "py-1.5 px-3 transition-colors cursor-pointer "
        "text-zinc-700 hover:bg-zinc-200/60 hover:text-zinc-900 "
        "dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-white"
    ),
    "footer_btn": (
        "flex items-center gap-3 w-full px-3 py-2 rounded-lg text-sm font-medium "
        "cursor-pointer transition-colors "
        "text-zinc-700 hover:bg-zinc-200/60 hover:text-zinc-900 "
        "dark:text-zinc-300 dark:hover:bg-zinc-800 dark:hover:text-white"
    ),
    # ── Popovers ──────────────────────────────────────────────────────────────
    "popover_panel": (
        "p-2 rounded-xl border shadow-lg "
        "bg-white border-zinc-200 dark:bg-zinc-900 dark:border-zinc-800"
    ),
    "popover_item": (
        "w-full text-left px-3 py-1.5 rounded-md text-sm transition-colors "
        "hover:bg-zinc-100 dark:hover:bg-zinc-800"
    ),
    "popover_label": (
        "text-xs font-semibold uppercase tracking-wide mb-1.5 px-1 "
        "text-zinc-500 dark:text-zinc-400"
    ),
    "popover_title": (
        "text-sm font-semibold mb-2 px-1 text-zinc-800 dark:text-zinc-200"
    ),
    "popover_hint": ("text-xs mt-2 px-1 text-zinc-500 dark:text-zinc-500"),
    # ── Layout & Surfaces ─────────────────────────────────────────────────────
    "sidebar_root": "bg-zinc-50 dark:bg-zinc-950",
    "input_wrapper": (
        "bg-white border-zinc-200 focus-within:border-zinc-300 focus-within:ring-zinc-200 "
        "dark:bg-zinc-900 dark:border-zinc-800 dark:focus-within:border-zinc-700 dark:focus-within:ring-zinc-700"
    ),
    # ── Buttons ───────────────────────────────────────────────────────────────
    "btn_primary": (
        "bg-indigo-600 hover:bg-indigo-700 text-white "
        "dark:bg-indigo-500 dark:hover:bg-indigo-400"
    ),
    "btn_ghost_square": (
        "bg-white border-zinc-200 text-zinc-600 hover:bg-zinc-100 "
        "dark:bg-transparent dark:border-zinc-700 dark:text-zinc-400 dark:hover:bg-zinc-800"
    ),
    "btn_action": (
        "text-zinc-400 hover:text-zinc-700 hover:bg-zinc-100 "
        "dark:text-zinc-500 dark:hover:text-zinc-200 dark:hover:bg-zinc-800"
    ),
    "btn_blue_tint": (
        "text-blue-600 bg-blue-50 hover:bg-blue-100 "
        "dark:text-blue-400 dark:bg-blue-900/20 dark:hover:bg-blue-900/30"
    ),
    # ── Badges & Avatars ──────────────────────────────────────────────────────
    "avatar_circle": "border-zinc-200 bg-zinc-100 dark:border-zinc-700 dark:bg-zinc-800",
    "badge_muted": "bg-zinc-100 text-zinc-500 dark:bg-zinc-800 dark:text-zinc-400",
    "badge_outline": "bg-zinc-100 border-zinc-200 text-zinc-600 dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-400",
    # ── Typography & Markdown ─────────────────────────────────────────────────
    "text_amber": "text-amber-600 dark:text-amber-400",
    "prose_body": "prose-zinc dark:prose-invert",
    "code_block": "bg-zinc-100 text-zinc-800 dark:bg-zinc-900 dark:text-zinc-200",
    # ── Specific Inputs ───────────────────────────────────────────────────────
    "input_search": (
        "bg-white border-zinc-200 text-zinc-900 placeholder-zinc-400 focus:border-indigo-400 focus:ring-indigo-100 "
        "dark:bg-zinc-900 dark:border-zinc-800 dark:text-zinc-100 dark:placeholder-zinc-500 dark:focus:border-indigo-500 dark:focus:ring-indigo-500/10"
    ),
}


# ============================================================================
# PRIMITIVE COMPONENTS
# ============================================================================


def pill_btn(
    *children,
    on_click: Optional[Callable] = None,
    extra: str = "",
) -> rx.Component:
    """Outlined pill button. Uses rx.el.button — no Radix style bleed."""
    return rx.el.button(
        *children,
        on_click=on_click,
        class_name=f"{T['pill_btn']} {extra}".strip(),
    )


def icon_btn(
    icon: str,
    on_click: Optional[Callable] = None,
    extra: str = "",
) -> rx.Component:
    """Circular outlined icon button."""
    return rx.el.button(
        rx.icon(icon, size=14),
        on_click=on_click,
        class_name=f"{T['icon_btn']} {extra}".strip(),
    )


def icon_btn_square(
    icon: str,
    on_click: Optional[Callable] = None,
    extra: str = "",
) -> rx.Component:
    """Square icon button (e.g. key button with blue tint)."""
    return rx.el.button(
        rx.icon(icon, size=14),
        on_click=on_click,
        class_name=f"{T['icon_btn_square']} {extra}".strip(),
    )


def nav_item(
    *children,
    on_click: Optional[Callable] = None,
) -> rx.Component:
    """Sidebar navigation item."""
    return rx.el.button(
        *children,
        on_click=on_click,
        class_name=T["nav_item"],
    )


def footer_btn(
    *children,
    on_click: Optional[Callable] = None,
) -> rx.Component:
    """Sidebar footer action button."""
    return rx.el.button(
        *children,
        on_click=on_click,
        class_name=T["footer_btn"],
    )


def card(*children, extra: str = "") -> rx.Component:
    """Standard raised card container."""
    return rx.el.div(
        *children,
        class_name=(
            f"rounded-xl border bg-white dark:bg-zinc-900 "
            f"border-zinc-200 dark:border-zinc-800 {extra}"
        ).strip(),
    )


def divider(axis: str = "h") -> rx.Component:
    """Horizontal or vertical divider."""
    if axis == "h":
        return rx.el.hr(class_name="border-zinc-200 dark:border-zinc-800 w-full")
    return rx.el.div(class_name="w-px self-stretch bg-zinc-200 dark:bg-zinc-800")


def text_input(
    placeholder: str = "",
    value: str = "",
    on_change: Optional[Callable] = None,
    extra: str = "",
) -> rx.Component:
    """Styled text input, compatible with Radix theme."""
    return rx.el.input(
        placeholder=placeholder,
        value=value,
        on_change=on_change,
        class_name=f"{T['input']} {extra}".strip(),
    )


# ── Radix wrappers (behaviour only, styled trigger) ──────────────────────────


def popover(
    trigger: rx.Component,
    content: rx.Component,
    min_width: str = "220px",
) -> rx.Component:
    """
    Radix popover with a plain-button trigger.
    Pass your trigger content (icon + text), not a full rx.button.
    """
    return rx.popover.root(
        rx.popover.trigger(trigger),
        rx.popover.content(
            content,
            class_name=f"{T['popover_panel']} min-w-[{min_width}]",
        ),
    )
