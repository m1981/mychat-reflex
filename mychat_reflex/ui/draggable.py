"""HTML5 Drag-and-Drop primitives for Reflex 0.8+.

Reflex's built-in ``rx.el.*`` element classes do **not** include
``on_drag_start`` / ``on_drag_over`` / ``on_drop`` etc. in their
allow-listed event triggers. The framework rejects them at component
construction time:

    ValueError: The Div does not take in an `on_drag_over` event trigger.

We work around this by subclassing the underlying ``Div`` / ``Li`` element
classes and extending ``get_event_triggers`` with the standard HTML5 drag
events. The corresponding React props (``onDragStart`` / ``onDragOver`` /
``onDrop`` / etc.) are emitted automatically by Reflex's name-mangling
(``on_drag_start`` -> ``onDragStart``), so no JS shim is needed.

Use:

    from mychat_reflex.ui.draggable import drag_div, drag_li

    drag_li(
        ...,
        draggable=True,
        on_drag_start=State.start_drag(item.id),
        on_drag_end=State.end_drag,
    )

    drag_div(
        ...,
        on_drag_over=[State.set_hover(target.id), rx.prevent_default],
        on_drag_leave=State.clear_hover,
        on_drop=[State.drop(target.id), rx.prevent_default],
    )

NOTE: ``rx.prevent_default`` is REQUIRED on both ``on_drag_over`` and
``on_drop`` — otherwise the browser refuses the drop (HTML5 spec).
"""

from __future__ import annotations

from reflex.components.el.elements.typography import Div, Li
from reflex.event import no_args_event_spec

# All HTML5 drag/drop events we want to expose. Reflex auto-converts
# snake_case -> camelCase for the React prop names.
_DRAG_TRIGGERS = {
    "on_drag": no_args_event_spec,
    "on_drag_start": no_args_event_spec,
    "on_drag_end": no_args_event_spec,
    "on_drag_enter": no_args_event_spec,
    "on_drag_over": no_args_event_spec,
    "on_drag_leave": no_args_event_spec,
    "on_drop": no_args_event_spec,
}


class DragDiv(Div):
    """``<div>`` with HTML5 drag/drop event triggers enabled."""

    @classmethod
    def get_event_triggers(cls):
        return {**super().get_event_triggers(), **_DRAG_TRIGGERS}


class DragLi(Li):
    """``<li>`` with HTML5 drag/drop event triggers enabled."""

    @classmethod
    def get_event_triggers(cls):
        return {**super().get_event_triggers(), **_DRAG_TRIGGERS}


# Convenience factories matching the rx.el.* call-style.
drag_div = DragDiv.create
drag_li = DragLi.create

__all__ = ["DragDiv", "DragLi", "drag_div", "drag_li"]
