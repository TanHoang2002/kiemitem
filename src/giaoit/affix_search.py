"""Affix search panel: nhập affix + GA + min/max + AND/OR → quét stash → list matches.

Có 2 entry point:
- ``AffixSearchPanel(QWidget)`` — nhúng vào dashboard (layout chính)
- ``AffixSearchDialog(QDialog)`` — dialog độc lập (Ctrl+F) wrap panel

KHÔNG lưu profile. KHÔNG mark junk/favorite. Read-only search.
"""

import logging
import threading
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QDoubleValidator
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QCompleter,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from src.game_data import GameCatalog
from src.i18n import tr
from src.profiles.editor.dialogs import IgnoreScrollWheelComboBox, IgnoreScrollWheelSpinBox

if TYPE_CHECKING:
    from src.item.models import Item

LOGGER = logging.getLogger(__name__)


class AffixSearchRow(QWidget):
    """One row: affix combobox + Greater checkbox + min/max value inputs + remove button."""

    remove_requested = pyqtSignal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        self.name_combo = IgnoreScrollWheelComboBox()
        self.name_combo.setEditable(True)
        self.name_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        completer = self.name_combo.completer()
        if completer is not None:
            completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.name_combo.setMaximumWidth(400)
        affix_dict = GameCatalog().affix_dict
        self.name_combo.addItems(sorted(affix_dict.values()))
        self._affix_reverse = {v: k for k, v in affix_dict.items()}
        layout.addWidget(self.name_combo)

        self.greater_checkbox = QCheckBox(tr("Greater"))
        self.greater_checkbox.setFixedWidth(80)
        layout.addWidget(self.greater_checkbox)

        self.min_edit = QLineEdit()
        self.min_edit.setPlaceholderText(tr("Min"))
        self.min_edit.setFixedWidth(70)
        self.min_edit.setValidator(QDoubleValidator(self.min_edit))
        layout.addWidget(self.min_edit)

        self.max_edit = QLineEdit()
        self.max_edit.setPlaceholderText(tr("Max"))
        self.max_edit.setFixedWidth(70)
        self.max_edit.setValidator(QDoubleValidator(self.max_edit))
        layout.addWidget(self.max_edit)

        self.remove_btn = QPushButton("×")
        self.remove_btn.setFixedWidth(30)
        self.remove_btn.setToolTip(tr("Remove this row"))
        self.remove_btn.clicked.connect(lambda: self.remove_requested.emit(self))
        layout.addWidget(self.remove_btn)

        layout.addStretch()

    def to_filter(self) -> tuple[AffixFilterModel | None, str]:
        text = self.name_combo.currentText().strip()
        if not text:
            return None, "empty"
        name = self._affix_reverse.get(text)
        if not name:
            name = self._affix_reverse.get(text.lower())
        if not name:
            return None, f"affix '{text}' not in catalog"

        try:
            min_v = float(self.min_edit.text()) if self.min_edit.text().strip() else None
        except ValueError:
            return None, f"invalid min value: {self.min_edit.text()!r}"
        try:
            max_v = float(self.max_edit.text()) if self.max_edit.text().strip() else None
        except ValueError:
            return None, f"invalid max value: {self.max_edit.text()!r}"
        if min_v is not None and max_v is not None and min_v > max_v:
            return None, f"min ({min_v}) > max ({max_v})"

        from src.profiles.affixes import AffixFilterModel

        model = AffixFilterModel(
            name=name, want_greater=self.greater_checkbox.isChecked(), min_value=min_v, max_value=max_v
        )
        return model, ""


class _OperatorButton(QPushButton):
    """Toggle button between AND/OR. Clicking it flips the mode and syncs all siblings."""

    def __init__(self, panel: AffixSearchPanel, parent=None):
        super().__init__("AND", parent)
        self._panel = panel
        self.setFixedWidth(60)
        self.setStyleSheet(
            "QPushButton { font-weight: bold; color: #aaa; background: transparent; border: none; }"
            "QPushButton:hover { color: #fff; }"
        )
        self.clicked.connect(self._toggle)

    def _toggle(self) -> None:
        new_mode = "any" if self.text() == "AND" else "all"
        self._panel.set_match_mode(new_mode)

    def refresh(self, mode: str) -> None:
        self.setText("OR" if mode == "any" else "AND")


class AffixSearchPanel(QWidget):
    """Embedded panel: search affix/aspect/name + AND/OR + result list."""

    scan_complete = pyqtSignal(object)

    SEARCH_TYPES = ("Affix", "Aspect", "Name")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._scan_thread: threading.Thread | None = None
        self._match_mode: str = "all"
        self._search_type: str = "Affix"
        self.rows: list[AffixSearchRow] = []
        self._operators: list[_OperatorButton] = []
        self._setup_ui()
        self.scan_complete.connect(self._on_scan_complete)

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # ── Header + search type switcher ────────────────────────────────
        top_bar = QHBoxLayout()
        header = QLabel(tr("🔍 ITEM SEARCH"))
        header.setStyleSheet("font-weight: bold; color: #888; letter-spacing: 1px;")
        top_bar.addWidget(header)
        top_bar.addStretch()

        top_bar.addWidget(QLabel(tr("Search by:")))
        self.type_combo = IgnoreScrollWheelComboBox()
        self.type_combo.addItems(list(self.SEARCH_TYPES))
        self.type_combo.setFixedWidth(100)
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        top_bar.addWidget(self.type_combo)
        layout.addLayout(top_bar)

        self.help_label = QLabel(tr("Enter affixes. Click AND/OR between rows. Items matching appear below."))
        self.help_label.setWordWrap(True)
        self.help_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.help_label)

        # ── Affix search section (rows + AND/OR) ─────────────────────────
        self.affix_section = QWidget()
        affix_layout = QVBoxLayout(self.affix_section)
        affix_layout.setContentsMargins(0, 0, 0, 0)

        # Row for Add/Remove/AND-OR buttons
        affix_controls = QHBoxLayout()
        self.add_btn = QPushButton(tr("+ Add affix"))
        self.add_btn.clicked.connect(lambda: self._add_row())
        affix_controls.addWidget(self.add_btn)
        affix_controls.addStretch()
        affix_controls.addWidget(QLabel(tr("Match:")))
        self.and_btn = QPushButton("AND")
        self.and_btn.setCheckable(True)
        self.and_btn.setChecked(True)
        self.or_btn = QPushButton("OR")
        self.or_btn.setCheckable(True)
        self.and_btn.toggled.connect(self._sync_match_toggle)
        self.or_btn.toggled.connect(self._sync_match_toggle)
        affix_controls.addWidget(self.and_btn)
        affix_controls.addWidget(self.or_btn)
        affix_layout.addLayout(affix_controls)

        # Rows scroll area
        self.rows_scroll = QScrollArea()
        self.rows_scroll.setWidgetResizable(True)
        self.rows_scroll.setFixedHeight(120)
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.rows_scroll.setWidget(self.rows_container)
        affix_layout.addWidget(self.rows_scroll)
        self._add_row()

        # Min matches requirement — clean, visible row
        min_row = QWidget()
        min_row.setStyleSheet("background-color: #333; border-radius: 4px;")
        min_h = QHBoxLayout(min_row)
        min_h.setContentsMargins(10, 6, 10, 6)
        min_h.setSpacing(8)

        min_label = QLabel(tr("Cần ít nhất"))
        min_label.setStyleSheet("color: #ccc; font-size: 10pt;")
        min_h.addWidget(min_label)

        self.min_count_spin = IgnoreScrollWheelSpinBox()
        self.min_count_spin.setMinimum(0)
        self.min_count_spin.setMaximum(99)
        self.min_count_spin.setValue(0)
        self.min_count_spin.setFixedHeight(30)
        self.min_count_spin.setMinimumWidth(50)
        self.min_count_spin.setStyleSheet(
            "QSpinBox { font-size: 12pt; padding: 2px 8px; }"
            "QSpinBox::up-button { width: 20px; }"
            "QSpinBox::down-button { width: 20px; }"
        )
        min_h.addWidget(self.min_count_spin)

        suffix_label = QLabel(tr("affix khớp (0 = tất cả)"))
        suffix_label.setStyleSheet("color: #999; font-size: 10pt;")
        min_h.addWidget(suffix_label)
        min_h.addStretch()

        affix_layout.addWidget(min_row)

        layout.addWidget(self.affix_section)

        # ── Aspect / Name search section ─────────────────────────────────
        self.simple_section = QWidget()
        simple_layout = QVBoxLayout(self.simple_section)
        simple_layout.setContentsMargins(0, 0, 0, 0)

        # Row 1: name combobox
        name_row = QHBoxLayout()
        self.simple_combo = IgnoreScrollWheelComboBox()
        self.simple_combo.setEditable(True)
        self.simple_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        simple_completer = self.simple_combo.completer()
        if simple_completer is not None:
            simple_completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            simple_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.simple_combo.setMinimumWidth(600)
        name_row.addWidget(self.simple_combo, stretch=1)

        # Min/Max value inputs (visible only for Aspect search)
        self.aspect_min_label = QLabel(tr("Min %:"))
        self.aspect_min_edit = QLineEdit()
        self.aspect_min_edit.setPlaceholderText(tr("Min"))
        self.aspect_min_edit.setFixedWidth(60)
        self.aspect_min_edit.setValidator(QDoubleValidator(self.aspect_min_edit))
        self.aspect_max_label = QLabel(tr("Max %:"))
        self.aspect_max_edit = QLineEdit()
        self.aspect_max_edit.setPlaceholderText(tr("Max"))
        self.aspect_max_edit.setFixedWidth(60)
        self.aspect_max_edit.setValidator(QDoubleValidator(self.aspect_max_edit))
        for w in (self.aspect_min_label, self.aspect_min_edit, self.aspect_max_label, self.aspect_max_edit):
            w.setVisible(False)
        name_row.addWidget(self.aspect_min_label)
        name_row.addWidget(self.aspect_min_edit)
        name_row.addWidget(self.aspect_max_label)
        name_row.addWidget(self.aspect_max_edit)
        name_row.addStretch()
        simple_layout.addLayout(name_row)

        self.simple_section.setVisible(False)
        layout.addWidget(self.simple_section)

        # ── Search button ────────────────────────────────────────────────
        action_bar = QHBoxLayout()
        action_bar.addStretch()
        self.search_btn = QPushButton(tr("🔍 Search (F5)"))
        self.search_btn.clicked.connect(self._start_search)
        action_bar.addWidget(self.search_btn)
        layout.addLayout(action_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888; font-style: italic;")
        layout.addWidget(self.status_label)

        self.result_list = QListWidget()
        self.result_list.setMinimumHeight(100)
        layout.addWidget(self.result_list, stretch=1)

    def _on_type_changed(self, search_type: str) -> None:
        """Switch UI between Affix (multi-row) and Aspect/Name (single combobox)."""
        self._search_type = search_type
        if search_type == "Affix":
            self.affix_section.setVisible(True)
            self.simple_section.setVisible(False)
            self.help_label.setText(tr("Enter affixes. Click AND/OR between rows. Items matching appear below."))
        else:
            self.affix_section.setVisible(False)
            self.simple_section.setVisible(True)
            # Show Min/Max only for Aspect search (aspect has value range)
            show_range = search_type == "Aspect"
            for w in (self.aspect_min_label, self.aspect_min_edit, self.aspect_max_label, self.aspect_max_edit):
                w.setVisible(show_range)
            if search_type == "Aspect":
                self.help_label.setText(tr("Enter aspect name (legendary + unique). Optional Min/Max % roll filter."))
                self._populate_simple_combo("aspect")
            else:
                self.help_label.setText(tr("Enter unique item name. Items with this name will be marked."))
                self._populate_simple_combo("unique")

    def _populate_simple_combo(self, catalog_type: str) -> None:
        """Fill the simple combobox with aspect names or unique names."""
        gc = GameCatalog()
        self.simple_combo.clear()
        if catalog_type == "aspect":
            # Combine legendary aspects (aspect_list) + unique aspects
            # (aspect_unique_dict keys) so search covers both.
            legendary = set(gc.aspect_list) if gc.aspect_list else set()
            unique = set(str(k) for k in gc.aspect_unique_dict.keys()) if gc.aspect_unique_dict else set()
            all_aspects = sorted(legendary | unique)
            self.simple_combo.addItems(all_aspects)
        else:
            items = sorted(str(k) for k in gc.aspect_unique_dict.keys()) if gc.aspect_unique_dict else []
            self.simple_combo.addItems(items)

    def _sync_match_toggle(self, _checked: bool) -> None:
        sender = self.sender()
        if sender is self.and_btn and self.and_btn.isChecked():
            self.or_btn.setChecked(False)
        elif sender is self.or_btn and self.or_btn.isChecked():
            self.and_btn.setChecked(False)
        if not self.and_btn.isChecked() and not self.or_btn.isChecked():
            self.and_btn.setChecked(True)

    def set_match_mode(self, mode: str) -> None:
        """Public — called by operator buttons to flip AND/OR globally."""
        self._match_mode = mode
        for op in self._operators:
            op.refresh(mode)

    def _refresh_operators(self) -> None:
        """Rebuild operator buttons between rows. Called after add/remove."""
        # Remove old operators
        for op in self._operators:
            self.rows_layout.removeWidget(op)
            op.deleteLater()
        self._operators.clear()
        # Insert operator between each pair of consecutive rows
        for i in range(len(self.rows) - 1):
            op = _OperatorButton(self, self.rows_container)
            op.refresh(self._match_mode)
            # Insert after row[i] — rows_layout index = 2*i + 1 (row, op, row, op, ...)
            self.rows_layout.insertWidget(2 * i + 1, op)
            self._operators.append(op)

    def _add_row(self) -> None:
        row = AffixSearchRow()
        row.remove_requested.connect(self._remove_row)
        self.rows.append(row)
        self.rows_layout.addWidget(row)
        self._refresh_operators()

    def _remove_row(self, row: AffixSearchRow) -> None:
        if len(self.rows) <= 1:
            return
        if row in self.rows:
            self.rows.remove(row)
            row.setParent(None)
            row.deleteLater()
            self._refresh_operators()

    def _remove_row(self, row: AffixSearchRow) -> None:
        if len(self.rows) <= 1:
            return
        if row in self.rows:
            self.rows.remove(row)
            row.setParent(None)
            row.deleteLater()

    def _build_pool(self) -> tuple[AffixFilterCountModel | None, str]:
        from src.profiles.affixes import AffixFilterCountModel

        affixes: list = []
        for i, row in enumerate(self.rows):
            model, error = row.to_filter()
            if model is None:
                if error == "empty":
                    continue
                return None, f"Row {i + 1}: {error}"
            affixes.append(model)
        if not affixes:
            return None, "no affixes entered"
        try:
            min_count = self.min_count_spin.value()
            # If min_count is 0, use default logic (all for AND, 1 for OR)
            kwargs = {"count": affixes, "match_mode": self._match_mode}
            if min_count > 0:
                kwargs["min_count"] = min_count
            return AffixFilterCountModel(**kwargs), ""
        except Exception as exc:
            return None, str(exc)

    def _start_search(self) -> None:
        """Build search criteria based on current search type, then scan."""
        if self._search_type == "Affix":
            pool, error = self._build_pool()
            if pool is None:
                self.status_label.setText(f"ERROR: {error}")
                return
            search_params = {"type": "affix", "pool": pool}
            LOGGER.info(
                "Search rule: mode=%s, count=%d, affixes=%s",
                pool.match_mode,
                len(pool.count),
                [(c.name, c.want_greater, c.min_value, c.max_value) for c in pool.count],
            )
        else:
            text = self.simple_combo.currentText().strip()
            if not text:
                self.status_label.setText("ERROR: select from list")
                return
            # Validate: text must be in the combobox items (autocomplete only)
            all_items = [self.simple_combo.itemText(i) for i in range(self.simple_combo.count())]
            if text not in all_items:
                self.status_label.setText(f"ERROR: '{text}' not in catalog — select from dropdown")
                return
            if self._search_type == "Aspect":
                min_val = None
                max_val = None
                try:
                    min_val = float(self.aspect_min_edit.text()) if self.aspect_min_edit.text().strip() else None
                except ValueError:
                    pass
                try:
                    max_val = float(self.aspect_max_edit.text()) if self.aspect_max_edit.text().strip() else None
                except ValueError:
                    pass
                search_params = {"type": "aspect", "name": text, "min_value": min_val, "max_value": max_val}
                LOGGER.info("Search rule: aspect=%s min=%s max=%s", text, min_val, max_val)
            else:
                search_params = {"type": "name", "name": text}
                LOGGER.info("Search rule: name=%s", text)
        if self._scan_thread is not None and self._scan_thread.is_alive():
            from src.giaoit.stash_scan import request_cancel

            request_cancel()
            self.status_label.setText(tr("Cancelling after current slot..."))
            return
        self.search_btn.setEnabled(False)
        self.status_label.setText(tr("Scanning + marking junk..."))
        self.result_list.clear()

        def _progress(scanned: int, matches: int) -> None:
            self.scan_complete.emit(("progress", scanned, matches))

        def _run() -> None:
            try:
                from src.giaoit.stash_scan import search_and_mark

                results = search_and_mark(pool, callback=_progress)
            except Exception as exc:
                LOGGER.exception("Affix search scan failed")
                self.scan_complete.emit(("error", str(exc)))
                return
            self.scan_complete.emit(("done", results))

        # Run via ScriptHandler._start_or_stop_loot_interaction_thread so
        # vision mode is STOPPED first — preventing TTS interference that
        # causes stale reads + duplicate items.
        def _run_via_handler(params, progress_cb):
            """Inline closure that calls search_and_mark and emits results."""
            try:
                from src.giaoit.stash_scan import search_and_mark

                results = search_and_mark(params, callback=progress_cb)
            except Exception as exc:
                LOGGER.exception("Search scan failed")
                self.scan_complete.emit(("error", str(exc)))
                return
            self.scan_complete.emit(("done", results))

        try:
            from PyQt6.QtWidgets import QApplication

            app = QApplication.instance()
            if app is not None:
                for widget in app.topLevelWidgets():
                    worker = getattr(widget, "worker", None)
                    handler = getattr(worker, "script_handler", None) if worker else None
                    if handler is not None and hasattr(handler, "_start_or_stop_loot_interaction_thread"):
                        handler._start_or_stop_loot_interaction_thread(_run_via_handler, (search_params, _progress))
                        return
        except Exception:
            LOGGER.debug("Could not find ScriptHandler; falling back to raw thread")

        self._scan_thread = threading.Thread(
            target=_run_via_handler, args=(search_params, _progress), daemon=True, name="item-search"
        )
        self._scan_thread.start()

    def _on_scan_complete(self, payload: object) -> None:
        if not isinstance(payload, tuple):
            return
        kind = payload[0]
        if kind == "progress":
            scanned, matches = payload[1], payload[2]  # type: ignore[misc]
            self.status_label.setText(tr(f"Scanning... {matches} matches in {scanned} items"))
            return
        # "done" or "error" — re-enable the search button.
        self.search_btn.setEnabled(True)
        if kind == "error":
            self.status_label.setText(f"❌ {payload[1]}")
            return
        results = payload[1]  # type: ignore[misc]
        if not results:
            self.status_label.setText(tr("No items matched (or scan was cancelled)"))
            return
        for item_descr, matched_affixes in results:
            self._add_result_item_from_item(item_descr, matched_affixes)
        self.status_label.setText(tr(f"{len(results)} items matched and marked as junk"))

    def _add_result_item_from_item(self, item_descr, matched_affixes: list) -> None:
        item: Item = item_descr
        name = item.original_name or item.name or (item.item_type.value if item.item_type else "(unknown)")
        power_str = f" power={item.power}" if item.power else ""
        rarity_str = f" [{item.rarity.value}]" if item.rarity else ""
        text = f"{name}{power_str}{rarity_str}"
        list_item = QListWidgetItem(text)
        tooltip_lines = ["Matched affixes:"]
        for aff in matched_affixes:
            value_str = f" = {aff.value}" if aff.value is not None else ""
            range_str = ""
            if aff.min_value is not None or aff.max_value is not None:
                range_str = f" (range {aff.min_value}-{aff.max_value})"
            ga = " [GA]" if aff.type.name == "greater" else ""
            tooltip_lines.append(f"  • {aff.name}{value_str}{range_str}{ga}")
        list_item.setToolTip("\n".join(tooltip_lines))
        self.result_list.addItem(list_item)


class AffixSearchDialog(QDialog):
    """Standalone dialog wrapping AffixSearchPanel — opened via Ctrl+F hotkey."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(tr("Affix Search (Ctrl+F)"))
        self.setModal(False)
        self.resize(900, 700)
        layout = QVBoxLayout(self)
        self.panel = AffixSearchPanel(self)
        layout.addWidget(self.panel)
