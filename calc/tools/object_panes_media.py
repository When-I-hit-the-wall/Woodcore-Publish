"""The editors of an image, a plan, a fire plan, an extract and the annexes in the right pane -- what a picture's width, a plan's options and an extract's pages are -- split out of calc/tools/object_panes.py (issue #30), moved verbatim. object_panes.py imports every name back.
"""

from PySide6.QtCore import QEvent, QSize, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView, QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QFileDialog, QHBoxLayout, QLabel,
    QLineEdit, QListWidget, QListWidgetItem, QPlainTextEdit, QPushButton, QSpinBox, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QWidget,
)
import cards  # the cards a pane is made of (cards.py)
import typst_objects as objects  # the models the panes edit (calc/typst_objects.py)
from typst_objects import AUTO, Content, Expr, ModelError
from object_panes_fields import (  # split out of this module (issue #30): every name it had is still importable from it
    CellField,
    DEBOUNCE_MS,
    ListBox,
    Pane,
    Switch,
    Text,
    _STRING,
    _VARIABLE,
    _between,
    _drop,
    _unescape,
    as_context,
    call_of,
    parse_number,
    plain,
    show_number,
    variable_of,
)


def set_width(edit, value, expression_words):
    """A width field shown as the model holds it: `60%`; an expression read only."""
    was = edit.blockSignals(True)
    if isinstance(value, Expr):
        edit.setText("")
        edit.setPlaceholderText(expression_words)
        edit.setEnabled(False)
    else:
        edit.setText(objects.inline(value))
        edit.setEnabled(True)
    edit.blockSignals(was)

