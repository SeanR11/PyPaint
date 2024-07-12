from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np
import cv2


class UIManager(QWidget):
    def __init__(self):
        super().__init__()

    def simpleText(self, text, font=None, color=None, bg_color=None):
        label = QLabel(text,self)
        if font:
            label.setFont(QFont(font[0], font[1]))
        if color:
            label.setStyleSheet(f"color:{color}")
        if bg_color:
            label.setStyleSheet(f"background-color:{color}")
        return label

    def LineEdit(self, text, action=None, size=None, valid=None, align=None):
        line_edit = QLineEdit(text,self)
        if size:
            line_edit.setFixedSize(size[0], size[1])
        if align:
            line_edit.setAlignment(align)
        if valid:
            line_edit.setValidator(valid)
        if action:
            line_edit.textChanged.connect(action)
        return line_edit

    def PushButton(self, text, action, color=None):
        button = QPushButton(text,self)
        button.clicked.connect(action)
        if color:
            button.setStyleSheet(f"background-color: {color}")

        return button

    def createCanvas(self, image):
        canvas = QLabel()
        canvas.setPixmap(QPixmap(image))
        canvas.setFixedSize(image.size())
        return canvas

    def MenuItem(self, menu, name, action=None, icon=None, short_key=None, inner_function=None):
        act = QAction(QIcon(icon),name,self) if icon else QAction(name,self)
        if action:
            if inner_function:
                act.triggered.connect(lambda: inner_function(action, name))
            else:
                act.triggered.connect(action)
        if short_key:
            act.setShortcut(short_key)
        menu.addAction(act)
        return act

    def ToolItem(self, toolbar, name, tooltip=None, action=None, editable=None, icon=None, short_key=None):
        item = QToolButton(self)
        if icon:
            item.setIcon(QIcon(icon))
        if action:
            if editable:
                item.clicked.connect(lambda: action(item, name))
            else:
                item.clicked.connect(action)
        if short_key:
            item.setShortcut(short_key)
        if tooltip:
            item.setToolTip(tooltip.title())
        item.setFocusPolicy(Qt.NoFocus)
        toolbar.addWidget(item)
        return item

    def ComboItem(self, toolbar, icon_size, action, pass_index=False):
        combo = QComboBox(self)
        if icon_size:
            combo.setIconSize(QSize(icon_size[0], icon_size[1]))
        if pass_index:
            combo.currentIndexChanged.connect(lambda: action(combo.currentIndex()))
        else:
            combo.currentIndexChanged.connect(lambda: action(combo.currentText()))

        combo.setMaximumWidth(200)
        combo.setStyleSheet("QComboBox{selection-background-color:white;selection-color:black;}")
        combo.setFocusPolicy(Qt.NoFocus)
        toolbar.addWidget(combo)
        return combo

    def SpinItem(self, toolbar, action, num_range, step):
        spin = QSpinBox(self)
        if action:
            spin.valueChanged.connect(lambda: action(spin.value()))
        if num_range:
            spin.setRange(num_range[0], num_range[1])
        if step:
            spin.setSingleStep(step)
        spin.setStyleSheet('QSpinBox::up-button {background-image: url("assets/small_up_arrow.png");}' + \
                           'QSpinBox::down-button {background-image: url("assets/small_down_arrow.png");}' + \
                           'QSpinBox { selection-background-color:white;selection-color:black;}')
        spin.setFocusPolicy(Qt.NoFocus)
        toolbar.addWidget(spin)
        return spin
