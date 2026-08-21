"""Tkinter confirm window for single captures.

V1 requirement (section 5): for kind=single captures, show the cropped image
on the left and the parsed item on the right, let the operator pick an
account, and either confirm (send) or dismiss (drop).

The bridge runs in its own process; this module exposes:

* ``run_confirm(payload, image_paths)`` — single-shot callback used by the
  dispatcher when running with ``--ui``. Opens a modal window, blocks until
  the user picks an account or dismisses.
* ``mainloop(stop_event)`` — invoked by ``main.py`` to keep the Tk mainloop
  alive (and to set a `mainloop` attribute so main detects it).
"""

import json
import threading
from pathlib import Path
from tkinter import (
    BOTH,
    END,
    LEFT,
    RIGHT,
    TOP,
    Button,
    Canvas,
    Frame,
    Label,
    OptionMenu,
    StringVar,
    Tk,
    Toplevel,
    X,
    messagebox,
)
from typing import Any

from PIL import Image, ImageTk

from bridge.accounts import load_accounts
from bridge.i18n import tr
from bridge.log import get_logger

LOGGER = get_logger()

_pending_queue: list[tuple[dict[str, Any], list[Path], Any]] = []
_pending_lock = threading.Lock()
_result_events: dict[int, threading.Event] = {}
_results: dict[int, str | None] = {}
_root: Tk | None = None


def run_confirm(payload: dict[str, Any], image_paths: list[Path]) -> str | None:
    """Open a modal confirm window and block until the user responds."""
    if _root is None:
        # No UI mainloop started — fall back to dispatcher default.
        LOGGER.warning("Tk root not initialised; run_confirm cannot show UI")
        accounts = load_accounts()
        return accounts[0] if accounts else None

    seq = id(payload)
    event = threading.Event()
    _result_events[seq] = event
    _results[seq] = None

    with _pending_lock:
        _pending_queue.append((payload, image_paths, seq))
    _root.event_generate("<<GiaoitPending>>", when="tail")

    event.wait(timeout=3600)
    return _results.pop(seq, None)


def _handle_pending(root: Tk) -> None:
    with _pending_lock:
        if not _pending_queue:
            return
        payload, image_paths, seq = _pending_queue.pop(0)

    accounts = load_accounts()
    dialog = _ConfirmDialog(root, payload, image_paths, accounts)
    root.wait_window(dialog.top)
    _results[seq] = dialog.account_id
    event = _result_events.pop(seq, None)
    if event is not None:
        event.set()


class _ConfirmDialog:
    def __init__(self, root: Tk, payload: dict[str, Any], image_paths: list[Path], accounts: list[str]) -> None:
        self.top = Toplevel(root)
        self.top.title(tr("Capture") + f" {payload.get('capture_id', '')[:8]}")
        self.top.transient(root)
        self.top.grab_set()
        self.account_id: str | None = None

        container = Frame(self.top)
        container.pack(fill=BOTH, expand=True)

        # Left: image preview
        image_frame = Frame(container)
        image_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=8, pady=8)
        if image_paths:
            try:
                pil_img = Image.open(image_paths[0])
                pil_img.thumbnail((400, 600))
                tk_img = ImageTk.PhotoImage(pil_img)
                canvas = Canvas(image_frame, width=pil_img.width, height=pil_img.height)
                canvas.pack()
                canvas.create_image(0, 0, anchor="nw", image=tk_img)
                canvas.image = tk_img  # keep reference
            except Exception:  # ruff: ignore[blind-except]
                Label(image_frame, text=tr("(no preview)")).pack()
        else:
            Label(image_frame, text=tr("(no image)")).pack()

        # Right: JSON view + account dropdown + buttons
        right = Frame(container)
        right.pack(side=RIGHT, fill=BOTH, expand=True, padx=8, pady=8)

        Label(right, text=tr("Parsed item (editable before send):")).pack(anchor="w")
        from tkinter import Text

        text_widget = Text(right, width=60, height=20)
        text_widget.pack(fill=BOTH, expand=True)
        text_widget.insert(END, json.dumps(payload, indent=2, ensure_ascii=False))

        account_row = Frame(right)
        account_row.pack(fill=X, pady=8)
        Label(account_row, text=tr("Account:")).pack(side=LEFT)
        self.account_var = StringVar(value=accounts[0] if accounts else "")
        OptionMenu(account_row, self.account_var, *accounts).pack(side=LEFT, padx=8)

        button_row = Frame(right)
        button_row.pack(side=TOP, pady=4)
        Button(button_row, text=tr("Send"), command=self._on_send).pack(side=LEFT, padx=4)
        Button(button_row, text=tr("Dismiss"), command=self._on_dismiss).pack(side=LEFT, padx=4)

    def _on_send(self) -> None:
        chosen = self.account_var.get().strip()
        if not chosen:
            messagebox.showwarning(tr("No account"), tr("Pick or type an account first."))
            return
        self.account_id = chosen
        self.top.destroy()

    def _on_dismiss(self) -> None:
        self.account_id = None
        self.top.destroy()


def mainloop(stop_event: threading.Event) -> None:
    """Run the Tk mainloop until ``stop_event`` is set."""
    global _root
    try:
        _root = Tk()
    except Exception:
        LOGGER.exception("Tk unavailable; UI disabled")
        return
    _root.withdraw()
    _root.title(tr("GiaoIT Bridge"))
    _root.bind("<<GiaoitPending>>", lambda _e: _handle_pending(_root))

    def _poll_stop() -> None:
        if stop_event.is_set():
            try:
                _root.quit()
                _root.destroy()
            except Exception:
                pass
            return
        _root.after(200, _poll_stop)

    _root.after(200, _poll_stop)
    _root.mainloop()
    _root = None


# Marker so main.py can detect the UI is available.
mainloop.mainloop = True  # type: ignore[attr-defined]
