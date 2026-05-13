"""
ScrollableCanvas - drop-in ttk.Canvas subclass with per-column tag-based vertical scrolling.

Items tagged with `scroll_tag` (default "scrollable") scroll on mouse wheel events via
canvas.move(); items without the tag stay fixed. The canvas is divided into vertical
column bands; each column scrolls independently with its own scrollbar.
"""

import ttkbootstrap as ttk
from modules.scaling import scale


class ScrollableCanvas(ttk.Canvas):

    _SB_TRACK_TAG = "_sb_track"
    _SB_THUMB_TAG = "_sb_thumb"

    def __init__(
        self,
        master,
        viewport=(20, 60, 760, 510),
        columns: list = None,
        scroll_tag: str = "scrollable",
        wheel_step: int = 40,
        track_color: str = "#1a1a1a",
        thumb_color: str = "#d4a017",
        sb_width: int = 4,
        sb_inset: int = 6,
        **kw,
    ):
        super().__init__(master, **kw)

        self._viewport = (
            scale(viewport[0]),
            scale(viewport[1]),
            scale(viewport[2]),
            scale(viewport[3]),
        )
        self._scroll_tag = scroll_tag
        self._wheel_step = scale(wheel_step)
        self._track_color = track_color
        self._thumb_color = thumb_color
        self._sb_width = scale(sb_width)
        self._sb_inset = scale(sb_inset)

        # Build scaled column bands. If none provided, the whole viewport is one column.
        if columns:
            self._columns = [(scale(x0), scale(x1)) for x0, x1 in columns]
        else:
            self._columns = [(self._viewport[0], self._viewport[2])]

        n = len(self._columns)
        self._col_offsets: list[int] = [0] * n
        self._col_max_offsets: list[int] = [0] * n
        self._col_items: list[set] = [set() for _ in range(n)]

        # Scrollbar item IDs per column (None until first ensure)
        self._col_track_ids: list = [None] * n
        self._col_thumb_ids: list = [None] * n
        self._drag_col: int = -1
        self._drag_anchor: float = 0.0

        self._hidden_windows: dict = {}
        self._hidden_native: set = set()
        self._page_hidden_windows: dict = {}
        self._page_hidden_native: set = set()
        self._item_y_bounds: dict = {}

        self.bind("<MouseWheel>", self._on_wheel, add="+")
        self.bind("<Button-4>", self._on_wheel, add="+")
        self.bind("<Button-5>", self._on_wheel, add="+")

    @property
    def viewport_height(self) -> int:
        return self._viewport[3] - self._viewport[1]

    def set_content_height(self, h: int):
        """Bucket scrollable items into columns and stash their Y bounds.

        Must be called when items are visible (not state="hidden") so that
        bbox() returns valid bounds. Typically called once after a fresh
        load (LoadPatches / loadCheats), after reset_scroll().
        """
        n = len(self._columns)
        self._col_items = [set() for _ in range(n)]
        self._item_y_bounds = {}

        # Clear stale hidden-item entries from a previous load.
        self._hidden_windows.clear()
        self._hidden_native.clear()
        self._page_hidden_windows.clear()
        self._page_hidden_native.clear()

        for item in self.find_withtag(self._scroll_tag):
            bbox = self.bbox(item)
            if not bbox:
                continue
            center_x = (bbox[0] + bbox[2]) / 2

            col_idx = None
            for i, (x0, x1) in enumerate(self._columns):
                if x0 <= center_x < x1:
                    col_idx = i
                    break
            if col_idx is None:
                continue

            self._col_items[col_idx].add(item)
            offset = self._col_offsets[col_idx]
            self._item_y_bounds[item] = (bbox[1] + offset, bbox[3] + offset)

        # Compute per-column max scroll offsets from original Y bounds
        for i in range(n):
            if self._col_items[i]:
                max_y = max(self._item_y_bounds[it][1] for it in self._col_items[i])
            else:
                max_y = 0
            self._col_max_offsets[i] = max(0, max_y - self.viewport_height)

        self._ensure_scrollbars()
        self._refresh_all_clipping()
        for i in range(n):
            self._draw_thumb_for_col(i)

    def reset_scroll(self):
        """Reset all column scroll positions to top.

        Restores any hidden windows (moved to x=-10000) back to their real X so
        that canvas.delete() can cleanly remove them, and un-hides native items
        so they are in a clean state before the caller recreates content.
        """
        for item, real_x in self._hidden_windows.items():
            coords = self.coords(item)
            if coords:
                self.coords(item, real_x, coords[1])
        self._hidden_windows.clear()

        for item in self._hidden_native:
            try:
                self.itemconfigure(item, state="normal")
            except Exception:
                pass
        self._hidden_native.clear()

        # clear page-hidden state (items will be deleted and recreated by caller).
        self._page_hidden_windows.clear()
        self._page_hidden_native.clear()

        for i in range(len(self._columns)):
            self._col_offsets[i] = 0
        self._col_items = [set() for _ in range(len(self._columns))]
        self._item_y_bounds.clear()

    def hide_tag(self, tag: str):
        """Hide all items with the given tag, using coord-translation for window items.

        Tracked separately from scroll-clipping so _refresh_clipping_for_col
        never accidentally un-hides page-hidden items during a scroll.
        """
        for item in self.find_withtag(tag):
            if self.type(item) == "window":
                if item not in self._page_hidden_windows and item not in self._hidden_windows:
                    coords = self.coords(item)
                    if coords:
                        self._page_hidden_windows[item] = coords[0]
                        self.coords(item, -10000, coords[1])
            else:
                if item not in self._page_hidden_native:
                    if self.itemcget(item, "state") != "hidden":
                        self.itemconfigure(item, state="hidden")
                    self._page_hidden_native.add(item)

    def show_tag(self, tag: str):
        """Show all items with the given tag, reversing hide_tag."""
        for item in self.find_withtag(tag):
            if self.type(item) == "window":
                if item in self._page_hidden_windows:
                    coords = self.coords(item)
                    if coords:
                        real_x = self._page_hidden_windows.pop(item)
                        self.coords(item, real_x, coords[1])
            else:
                if item in self._page_hidden_native:
                    self._page_hidden_native.discard(item)
                    # Only restore if scroll-clipping isn't also hiding it
                    if item not in self._hidden_native:
                        self.itemconfigure(item, state="normal")

    def clear_scrollable(self):
        """Delete all scrollable items and reset offsets."""
        self.delete(self._scroll_tag)
        self._hidden_windows.clear()
        self._hidden_native.clear()
        self._page_hidden_windows.clear()
        self._page_hidden_native.clear()
        self._item_y_bounds.clear()
        n = len(self._columns)
        self._col_offsets = [0] * n
        self._col_max_offsets = [0] * n
        self._col_items = [set() for _ in range(n)]
        for i in range(n):
            self._draw_thumb_for_col(i)

    def _on_wheel(self, event):
        if isinstance(event.widget, ttk.Scale):
            return

        try:
            from modules.FrontEnd.CanvasMgr import Canvas_Create
            Canvas_Create.hide_tooltip()
        except Exception:
            pass

        # Determine column under cursor
        col_idx = next(
            (i for i, (x0, x1) in enumerate(self._columns) if x0 <= event.x < x1),
            None,
        )
        if col_idx is None or self._col_max_offsets[col_idx] <= 0:
            return

        if event.num == 4:
            dy = -self._wheel_step
        elif event.num == 5:
            dy = self._wheel_step
        else:
            dy = int(-event.delta / 120 * self._wheel_step)

        new_offset = max(
            0, min(self._col_max_offsets[col_idx], self._col_offsets[col_idx] + dy)
        )
        if new_offset != self._col_offsets[col_idx]:
            self._apply_col_offset(col_idx, new_offset)

    def _apply_col_offset(self, col_idx: int, new_offset: int):
        delta = self._col_offsets[col_idx] - new_offset
        if delta != 0:
            for item in self._col_items[col_idx]:
                self.move(item, 0, delta)
        self._col_offsets[col_idx] = new_offset
        self._refresh_clipping_for_col(col_idx)
        self._draw_thumb_for_col(col_idx)

    def _refresh_all_clipping(self):
        for i in range(len(self._columns)):
            self._refresh_clipping_for_col(i)

    def _refresh_clipping_for_col(self, col_idx: int):
        """Hide items whose Y-bounds fall fully outside the viewport.

        Uses stashed original Y bounds (from set_content_height) minus the column's
        current scroll offset to compute the item's *current* Y span. This avoids
        canvas.bbox(), which returns None for items with state="hidden" — that
        previously made it impossible to un-hide a native text item once it had
        scrolled out of view.
        """
        y1, y2 = self._viewport[1], self._viewport[3]
        offset = self._col_offsets[col_idx]

        for item in self._col_items[col_idx]:
            bounds = self._item_y_bounds.get(item)
            if bounds is None:
                continue

            # Don't touch items hidden by the page system — they have their own state.
            if item in self._page_hidden_windows or item in self._page_hidden_native:
                continue

            current_y_top = bounds[0] - offset
            current_y_bot = bounds[1] - offset

            # Strict clipping: an item is visible only when its entire bbox
            should_hide = current_y_top < y1 or current_y_bot > y2
            item_type = self.type(item)

            if item_type == "window":
                is_hidden = item in self._hidden_windows
                if should_hide:
                    if not is_hidden:
                        coords = self.coords(item)
                        if coords:
                            self._hidden_windows[item] = coords[0]
                            self.coords(item, -10000, coords[1])
                else:
                    if is_hidden:
                        coords = self.coords(item)
                        if coords:
                            real_x = self._hidden_windows.pop(item)
                            self.coords(item, real_x, coords[1])
            else:
                is_hidden = item in self._hidden_native
                if should_hide:
                    if not is_hidden:
                        if self.itemcget(item, "state") != "hidden":
                            self.itemconfigure(item, state="hidden")
                            self._hidden_native.add(item)
                else:
                    if is_hidden:
                        self.itemconfigure(item, state="normal")
                        self._hidden_native.discard(item)

    def _ensure_scrollbars(self):
        y1 = self._viewport[1]
        y2 = self._viewport[3]

        for i, (x0, x1) in enumerate(self._columns):
            x = x1 - self._sb_inset

            if self._col_track_ids[i] is None:
                track_tag = f"{self._SB_TRACK_TAG}_col{i}"
                thumb_tag = f"{self._SB_THUMB_TAG}_col{i}"

                self._col_track_ids[i] = self.create_rectangle(
                    x, y1, x + self._sb_width, y2,
                    fill=self._track_color,
                    outline="",
                    tags=(self._SB_TRACK_TAG, track_tag),
                )
                self._col_thumb_ids[i] = self.create_rectangle(
                    x, y1, x + self._sb_width, y1 + 10,
                    fill=self._thumb_color,
                    outline="",
                    tags=(self._SB_THUMB_TAG, thumb_tag),
                )
                self.tag_bind(thumb_tag, "<Button-1>",
                              lambda e, ci=i: self._on_thumb_press(e, ci))
                self.tag_bind(thumb_tag, "<B1-Motion>",
                              lambda e, ci=i: self._on_thumb_drag(e, ci))
                self.tag_bind(thumb_tag, "<ButtonRelease-1>",
                              lambda e, ci=i: self._on_thumb_release(e, ci))
            else:
                self.coords(self._col_track_ids[i], x, y1, x + self._sb_width, y2)
                self.tag_raise(f"{self._SB_TRACK_TAG}_col{i}")
                self.tag_raise(f"{self._SB_THUMB_TAG}_col{i}")

    def _draw_thumb_for_col(self, col_idx: int):
        thumb_id = self._col_thumb_ids[col_idx]
        track_id = self._col_track_ids[col_idx]
        if thumb_id is None:
            return

        max_off = self._col_max_offsets[col_idx]
        if max_off <= 0:
            self.itemconfigure(track_id, state="hidden")
            self.itemconfigure(thumb_id, state="hidden")
            return

        self.itemconfigure(track_id, state="normal")
        self.itemconfigure(thumb_id, state="normal")

        y1 = self._viewport[1]
        y2 = self._viewport[3]
        vp_h = y2 - y1
        content_h = max_off + vp_h

        thumb_h = max(scale(20), int(vp_h * vp_h / content_h))
        track_span = vp_h - thumb_h
        ratio = self._col_offsets[col_idx] / max_off if max_off > 0 else 0
        thumb_top = y1 + int(track_span * ratio)
        thumb_bot = thumb_top + thumb_h

        x0, x1 = self._columns[col_idx]
        x = x1 - self._sb_inset
        self.coords(thumb_id, x, thumb_top, x + self._sb_width, thumb_bot)

    def _on_thumb_press(self, event, col_idx: int):
        thumb_id = self._col_thumb_ids[col_idx]
        coords = self.coords(thumb_id)
        if not coords:
            return
        self._drag_col = col_idx
        self._drag_anchor = event.y - coords[1]

    def _on_thumb_drag(self, event, col_idx: int):
        if self._drag_col != col_idx:
            return
        max_off = self._col_max_offsets[col_idx]
        if max_off <= 0:
            return

        thumb_id = self._col_thumb_ids[col_idx]
        y1 = self._viewport[1]
        y2 = self._viewport[3]
        thumb_coords = self.coords(thumb_id)
        thumb_h = thumb_coords[3] - thumb_coords[1]
        track_span = (y2 - y1) - thumb_h
        if track_span <= 0:
            return

        new_thumb_top = max(y1, min(y2 - thumb_h, event.y - self._drag_anchor))
        ratio = (new_thumb_top - y1) / track_span
        new_offset = int(ratio * max_off)
        if new_offset != self._col_offsets[col_idx]:
            self._apply_col_offset(col_idx, new_offset)

    def _on_thumb_release(self, event, col_idx: int):
        self._drag_col = -1
