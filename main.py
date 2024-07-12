from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QToolBar, QAction
from PyQt5.QtWidgets import QLabel, QLineEdit, QFileDialog, QDialog, QColorDialog
from PyQt5.QtGui import QIcon, QPixmap, QPainter, QPen, QImage, QColor, QCursor, QIntValidator
from PyQt5.QtCore import Qt, QSize, QDir
import numpy as np
import pyperclip
import cv2

from ui_manager import UIManager
from cv_manager import CVManager


class Core(QMainWindow):
    def __init__(self, app, width, height, title):
        super().__init__()

        # Initialize the main window
        self.local_width, self.local_height = app.desktop().screenGeometry().getRect()[2:]
        self.setGeometry(self.local_width // 2 - width // 2, self.local_height // 2 - height // 2, width, height)
        self.resize(width, height)
        self.setWindowTitle(title)
        self.setMouseTracking(True)

        # Initialize UI and CV managers
        self.UI = UIManager()
        self.CV = CVManager()
        self.app = app

        # Initialize main container
        self.main_container = QWidget()
        self.main_container.setStyleSheet("background-color:#E0E0E0;")
        self.main_container.setMouseTracking(True)

        # Set layout for the main container
        self.layout = QHBoxLayout(self.main_container)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setAlignment(Qt.AlignCenter)

        # Set main container as central widget
        self.setCentralWidget(self.main_container)

        # Initialize variables for image manipulation
        self.canvas = None
        self.image = None
        self.image_copy = None
        self.image_effect = None
        self.hold = None
        self.start_pos = None
        self.pointer_position = None
        self.primary_color = [None, (0, 0, 0)]
        self.secondary_color = [None, (255, 255, 255)]
        self.active_color = self.primary_color[1]
        self.font_data = [0, 0 + (0.05 * 6)]
        self.thickness = 1
        self.shape_state = [None, None]
        self.active_tool = None
        self.text_block = None
        self.text_block_content = ''
        self.text_caps = 1
        self.text_mode = False
        self.text_color = self.active_color
        self.last_key = None
        self.selection = None
        self.selection_move = False
        self.selection_state = False
        self.cropped_image = None

        # Load menu bar, status bar, and tool bar
        self.loadMenuBar()
        self.loadStatusBar()
        self.loadToolBar()

    # Mouse press event handler
    def mousePressEvent(self, event):
        """
        Handle mouse press events based on active tool and canvas
        """
        if self.canvas and self.active_tool:
            if self.canvas.underMouse():
                x, y = self.innerMousePos(event, self.canvas.geometry())
                if event.button() == Qt.MouseButton.LeftButton and not self.hold:
                    if not self.text_mode:
                        self.start_pos = (x, y)
                    self.hold = True
                    self.active_color = self.primary_color[1]
                elif event.button() == Qt.MouseButton.RightButton and not self.hold:
                    if not self.text_mode:
                        self.start_pos = (x, y)
                    self.hold = True
                    self.active_color = self.secondary_color[1]

                if event.button() == Qt.MouseButton.RightButton or event.button() == Qt.MouseButton.LeftButton:
                    if self.active_tool[1] == 'pointer':
                        if self.selection_state:
                            t_x, t_y = self.getMinMax(self.selection[0], self.selection[1])
                            if t_x[0] < x < t_x[1] and t_y[0] < y < t_y[1]:
                                self.selection_move = True
                    elif self.active_tool[1] == 'dropper':
                        if event.button() == event.button() == Qt.MouseButton.RightButton:
                            self.secondary_color[1] = [int(num) for num in self.image[y][x]]
                            square = np.full((20, 20, 3), self.secondary_color[1], dtype=np.uint8)
                            self.secondary_color[0].setIcon(self.CV.toIcon(square))
                            self.active_color = self.secondary_color[1]
                        else:
                            self.primary_color[1] = [int(num) for num in self.image[y][x]]
                            square = np.full((20, 20, 3), self.primary_color[1], dtype=np.uint8)
                            self.primary_color[0].setIcon(self.CV.toIcon(square))
                            self.active_color = self.primary_color[1]
                    elif self.active_tool[1] == 'text':
                        if self.text_mode:
                            self.text_mode = False
                            self.text_block_content = ''
                            cv2.putText(self.image, self.text_block.text(), (self.start_pos[0], self.start_pos[1]),
                                        self.font_data[0],
                                        self.font_data[1], self.text_color, self.thickness)
                            self.text_color = None
                        else:
                            self.text_mode = True
                            self.text_block = QLineEdit(self)
                            self.text_color = self.active_color
                            self.text_block.setText('Enter Text')
                            self.image_copy = self.image.copy()
                            cv2.putText(self.image, self.text_block.text(), (self.start_pos[0], self.start_pos[1]),
                                        self.font_data[0], self.font_data[1], self.text_color, self.thickness)
                            self.renderImage()
                            self.image = self.image_copy

    # Mouse release event handler
    def mouseReleaseEvent(self, event):
        """
        Handle mouse release events based on active tool and canvas
        """
        if self.canvas and self.active_tool:
            if event.button() == Qt.MouseButton.LeftButton or event.button() == Qt.MouseButton.RightButton:
                x, y = self.innerMousePos(event, self.canvas.geometry())
                if not self.active_tool[1] == 'text':
                    self.image_copy = self.image.copy()
                    if self.active_tool[1] == 'pointer':
                        if self.selection_state:
                            t_x, t_y = self.getMinMax(self.selection[0], self.selection[1])
                            if t_x[0] < x < t_x[1] and t_y[0] < y < t_y[1]:
                                self.CV.drawDashRect(self.image, self.selection[0], self.selection[1], (0, 0, 0))
                                self.image = self.CV.drawImage(self.image, self.selection[0], self.selection[1],
                                                               self.cropped_image,
                                                               (self.canvas.width(), self.canvas.height()))
                                self.renderImage()
                                self.image = self.image_copy
                                self.selection_move = False
                            else:
                                self.image = self.CV.drawImage(self.image, self.selection[0], self.selection[1],
                                                               self.cropped_image,
                                                               (self.canvas.width(), self.canvas.height()))
                                self.renderImage()
                                self.selection = None
                                self.selection_state = None
                                self.cropped_image = None
                            self.hold = False
                            return
                        else:
                            self.CV.drawDashRect(self.image, self.start_pos, (x, y), (0, 0, 0))
                            self.selection = (self.start_pos, (x, y))
                            self.cropped_image = self.CV.cropImage(self.image, self.selection[0], self.selection[1])
                            self.renderImage()
                            self.image = self.image_copy
                            white_refiller = np.full(self.cropped_image.shape, (255, 255, 255), dtype=np.uint8)
                            self.image_copy = self.CV.drawImage(self.image, self.selection[0], self.selection[1],
                                                                white_refiller,
                                                                (self.canvas.width(), self.canvas.height()))
                            self.selection_state = True
                            self.hold = False
                            return
                    elif self.active_tool[1] == 'line':
                        self.CV.drawLine(self.image, self.start_pos, (x, y), self.active_color, self.thickness)
                    elif self.active_tool[1] == 'circle':
                        self.CV.drawElipse(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                           self.secondary_color[1], self.shape_state[1])
                    elif self.active_tool[1] == 'triangle':
                        self.CV.drawTriangle(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                             self.secondary_color[1], self.shape_state[1])
                    elif self.active_tool[1] == 'rectangle':
                        self.CV.drawRectangle(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                              self.secondary_color[1], self.shape_state[1])
                    elif self.active_tool[1] == 'pentagon':
                        self.CV.drawPentagon(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                             self.secondary_color[1], self.shape_state[1])
                    elif self.active_tool[1] == 'hexagon':
                        self.CV.drawHexagon(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                            self.secondary_color[1], self.shape_state[1])
                    elif self.active_tool[1] == 'diamond':
                        self.CV.drawDiamond(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                            self.secondary_color[1], self.shape_state[1])
                    elif self.active_tool[1] == 'crop':
                        if self.selection:
                            self.image = np.full((self.cropped_image.shape[0], self.cropped_image.shape[1], 3),
                                                 [255, 255, 255],
                                                 dtype=np.uint8)

                            self.image[0:self.cropped_image.shape[0],
                            0:self.cropped_image.shape[1]] = self.cropped_image
                            self.setNewCanvas(self.canvas.width() * 2, self.canvas.height() * 2, image=self.image)

                    self.renderImage()
                self.hold = False

    def mouseMoveEvent(self, event):
        """
        Handle mouse move events based on active tool and canvas
        """
        if self.canvas:
            if self.canvas.underMouse():
                x, y = self.innerMousePos(event, self.canvas.geometry())
                self.pointer_position.setText(f"{x} , {y}")

                # Check if a tool is active and if the mouse is held down
                if self.hold and self.active_tool:
                    self.image_copy = self.image.copy()

                    # Handle drawing and erasing tools
                    if self.active_tool[1] == 'draw' or self.active_tool[1] == 'eraser':
                        if self.active_tool[1] == 'eraser':
                            self.active_color = [255, 255, 255]

                        # Calculate distance between current and previous position for smoother drawing
                        if self.start_pos:
                            dist = np.sqrt((x - self.start_pos[0]) ** 2 + (y - self.start_pos[1]) ** 2)
                            if dist < 5:
                                cv2.line(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                         cv2.LINE_AA)
                            else:
                                num_points = max(int(dist), 1)
                                xs = np.linspace(self.start_pos[0], x, num_points).astype(int)
                                ys = np.linspace(self.start_pos[1], y, num_points).astype(int)

                                for i in range(num_points - 1):
                                    cv2.line(self.image, (xs[i], ys[i]), (xs[i + 1], ys[i + 1]), self.active_color,
                                             self.thickness,
                                             cv2.LINE_AA)

                        else:
                            cv2.circle(self.image, (x, y), self.thickness // 2, self.active_color, -1)

                        self.start_pos = (x, y)
                        self.renderImage()
                        return

                    # Handle other drawing tools
                    else:
                        if self.active_tool[1] == 'pointer':
                            if not self.selection_state:
                                self.CV.drawDashRect(self.image, self.start_pos, (x, y), (0, 0, 0))
                            else:
                                t_x, t_y = self.getMinMax(self.selection[0], self.selection[1])
                                if t_x[0] < x < t_x[1] and t_y[0] < y < t_y[1]:
                                    start_pos, current_pos = self.CV.drawDashRect(self.image, self.selection[0],
                                                                                  self.selection[1], (0, 0, 0),
                                                                                  (self.start_pos, (x, y)))

                                    self.image = self.CV.drawImage(self.image, start_pos, current_pos,
                                                                   self.cropped_image,
                                                                   (self.canvas.width(), self.canvas.height()))
                                    self.selection = (start_pos, current_pos)
                                    self.renderImage()
                                    self.start_pos = (x, y)
                        elif self.active_tool[1] == 'line':
                            self.CV.drawLine(self.image, self.start_pos, (x, y), self.active_color, self.thickness)
                        elif self.active_tool[1] == 'circle':
                            self.CV.drawElipse(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                               self.secondary_color[1], self.shape_state[1])
                        elif self.active_tool[1] == 'triangle':
                            self.CV.drawTriangle(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                                 self.secondary_color[1], self.shape_state[1])
                        elif self.active_tool[1] == 'rectangle':
                            self.CV.drawRectangle(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                                  self.secondary_color[1], self.shape_state[1])
                        elif self.active_tool[1] == 'pentagon':
                            self.CV.drawPentagon(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                                 self.secondary_color[1], self.shape_state[1])
                        elif self.active_tool[1] == 'hexagon':
                            self.CV.drawHexagon(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                                self.secondary_color[1], self.shape_state[1])
                        elif self.active_tool[1] == 'diamond':
                            self.CV.drawDiamond(self.image, self.start_pos, (x, y), self.active_color, self.thickness,
                                                self.secondary_color[1], self.shape_state[1])

                    self.renderImage()
                    self.image = self.image_copy

                # Set cursor based on active tool
                if self.active_tool:
                    if self.canvas.underMouse():
                        if self.active_tool[1] == 'pointer' and self.selection_state:
                            t_x, t_y = self.getMinMax(self.selection[0], self.selection[1])
                            if t_x[0] < x < t_x[1] and t_y[0] < y < t_y[1]:
                                self.app.setOverrideCursor(Qt.SizeAllCursor)
                            else:
                                self.app.setOverrideCursor(Qt.ArrowCursor)
                        elif self.active_tool[1] == 'draw':
                            curs = QPixmap('assets/draw.png')
                            self.app.setOverrideCursor(QCursor(curs.scaled(20, 20), 0, 20))
                        elif self.active_tool[1] == 'eraser':
                            curs = QPixmap('assets/eraser.png')
                            self.app.setOverrideCursor(QCursor(curs.scaled(20, 20), 0, 20))
                        elif self.active_tool[1] == 'dropper':
                            curs = QPixmap('assets/dropper.png')
                            self.app.setOverrideCursor(QCursor(curs.scaled(20, 20), 0, 20))
                        elif self.active_tool[1] == 'text':
                            curs = QPixmap('assets/text.png')
                            self.app.setOverrideCursor(QCursor(curs.scaled(20, 20), 0, 20))
                        else:
                            self.app.setOverrideCursor(Qt.ArrowCursor)

    def keyPressEvent(self, event):
        """
        Handle key press events, especially for text editing mode
        """
        if event.key() == Qt.Key_Z and self.last_key == Qt.Key_Control:
            temp = self.image.copy()
            self.image = self.image_copy
            self.image_copy = temp
            self.renderImage()
        elif self.text_mode:
            if event.key() == Qt.Key_V and self.last_key == Qt.Key_Control:
                self.text_block_content += pyperclip.paste()
            elif event.key() == Qt.Key_C and self.last_key == Qt.Key_Control:
                pyperclip.copy(self.text_block_content)
                return
            elif event.key() == Qt.Key_Backspace:
                self.text_block_content = self.text_block_content[:-1]
            elif event.key() == Qt.Key_Return:
                self.text_mode = False
                self.text_block_content = ''
                cv2.putText(self.image, self.text_block.text(), (self.start_pos[0], self.start_pos[1]),
                            self.font_data[0],
                            self.font_data[1], self.active_color, self.thickness)
                return
            elif event.key() == Qt.Key_CapsLock:
                self.text_caps = 1 if self.text_caps == 0 else 0
            elif event.key() == Qt.Key_Control or event.key() == Qt.Key_Escape or event.key() == Qt.Key_Tab \
                    or event.key() == Qt.Key_Alt or event.key() == Qt.Key_Shift:
                pass
            else:
                key = event.key() + (32 * self.text_caps)
                self.text_block_content += chr(key)
            self.text_block.setText(self.text_block_content)
            self.image_copy = self.image.copy()
            cv2.putText(self.image, self.text_block.text(), (self.start_pos[0], self.start_pos[1]), self.font_data[0],
                        self.font_data[1], self.active_color, self.thickness)
            self.renderImage()
            self.image = self.image_copy

        self.last_key = event.key()

    def loadMenuBar(self):
        """
        Load menu bar with file-related menu items
        """
        menu = self.menuBar()
        file_menu = menu.addMenu('&File')

        # Add menu items for file operations
        self.UI.MenuItem(menu=file_menu, name="&New", action=lambda: self.setCanvasDialog(), short_key='Ctrl+N',
                         icon='assets/new.jpg')
        self.UI.MenuItem(menu=file_menu, name="&Open", action=lambda: self.fileDialog(mode='open'), short_key='Ctrl+O',
                         icon='assets/open.jpg')
        self.UI.MenuItem(menu=file_menu, name="&Save", action=lambda: self.fileDialog(mode='save'), short_key='Ctrl+S',
                         icon='assets/save.jpg')
        self.UI.MenuItem(menu=file_menu, name="&Exit", action=lambda: self.close(), short_key='Ctrl+E',
                         icon='assets/exit.jpg')

    def loadStatusBar(self):
        """
        Load status bar with pointer icon and position label.
        """
        statusbar = self.statusBar()
        statusbar.setStyleSheet("QStatusBar::item {border: none;}")
        statusbar.setContentsMargins(0, 0, 0, 0)

        # Add pointer icon
        pointer_icon = QLabel(self)
        pointer_icon.setPixmap(QIcon('assets/pointer.png').pixmap(QSize(15, 15)))

        # Add pointer position label
        self.pointer_position = QLabel(self)
        self.pointer_position.setText("0 , 0")

        statusbar.addWidget(pointer_icon)
        statusbar.addWidget(self.pointer_position)

    def loadToolBar(self):
        """
        Load toolbar with various tools, shapes, pen options, brush options, and effects.
        """
        toolbar = QToolBar("Toolbar")
        toolbar.setFixedHeight(35)
        toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(toolbar)

        # IMAGE tools
        image_tag = QLabel(self)
        image_tag.setText('Image: ')
        toolbar.addWidget(image_tag)
        # Add rotate left tool
        self.UI.ToolItem(toolbar, 'rotate left', icon='assets/rotate-left.png', tooltip="rotate 90° left",
                         action=lambda: self.rotateImage(side='left'), short_key='CTRL+SHIFT+R')
        # Add rotate right tool
        self.UI.ToolItem(toolbar, 'rotate right', icon='assets/rotate-right.png', tooltip="rotate 90° right",
                         action=lambda: self.rotateImage(side='right'), short_key='CTRL+SHIFT+L')
        # Add flip vertical tool
        self.UI.ToolItem(toolbar, 'flip vertical', icon='assets/flip_v.png', tooltip="flip vertical",
                         action=lambda: self.flipImage('v'), short_key='CTRL+SHIFT+V')
        # Add flip horizontal tool
        self.UI.ToolItem(toolbar, 'flip horizontal', icon='assets/flip_h.png', tooltip="flip horizontal",
                         action=lambda: self.flipImage('h'), short_key='CTRL+SHIFT+H')
        toolbar.addSeparator()

        # TOOLS
        tools_tag = QLabel(self)
        tools_tag.setText('Tools: ')
        toolbar.addWidget(tools_tag)
        tools = ['pointer', 'crop', 'draw', 'eraser', 'dropper', 'text']
        for tool in tools:
            self.UI.ToolItem(toolbar, tool, icon=f'assets/{tool}.png', tooltip=tool, action=self.setActiveTool,
                             editable=True)
        toolbar.addSeparator()

        # SHAPES
        shapes_tag = QLabel(self)
        shapes_tag.setText('Shapes: ')
        toolbar.addWidget(shapes_tag)
        shapes = ['line', 'circle', 'triangle', 'rectangle', 'pentagon', 'hexagon', 'diamond']
        for shape in shapes:
            self.UI.ToolItem(toolbar, shape, icon=f'assets/{shape}.png', tooltip=f'{shape}',
                             action=self.setActiveTool, editable=True)
        toolbar.addSeparator()

        # PEN
        pen_tag = QLabel(self)
        pen_tag.setText('Pen: ')
        toolbar.addWidget(pen_tag)
        fonts = ['hershey complex', 'hershey complex small', 'hershey duplex', 'hershey plain',
                 'hershey script complex', 'hershey script simplex', 'hershey triplex', 'italic']
        fonts_combo = self.UI.ComboItem(toolbar, icon_size=(100, 40), action=self.fontDialog, pass_index=True)
        for font in fonts:
            fonts_combo.addItem(QIcon(f'assets/{font}.png'), '')

        fonts_combo.setFixedHeight(30)

        fonts_spin = self.UI.SpinItem(toolbar, action=self.fontSizeDialog, num_range=(36, 72), step=2)
        fonts_spin.setFixedSize(50, 30)

        toolbar.addSeparator()

        # BRUSH
        brush_tag = QLabel(self)
        brush_tag.setText('Brush: ')
        toolbar.addWidget(brush_tag)
        line_thickness = ['1px', '3px', '5px', '8px', '10px']

        thickness_combo = self.UI.ComboItem(toolbar, icon_size=(100, 40), action=self.thicknessDialog)
        for thickness in line_thickness:
            thickness_combo.addItem(QIcon(f'assets/{thickness}.png'), thickness)

        self.primary_color[0] = self.UI.ToolItem(toolbar, 'primary',
                                                 icon=self.CV.toIcon(
                                                     np.full((20, 20, 3), self.primary_color[1], dtype=np.uint8)),
                                                 tooltip='primary color', action=self.colorDialog, editable=True)
        self.secondary_color[0] = self.UI.ToolItem(toolbar, 'secondary',
                                                   icon=self.CV.toIcon(
                                                       np.full((20, 20, 3), self.secondary_color[1], dtype=np.uint8)),
                                                   tooltip='secondary color', action=self.colorDialog, editable=True)
        self.shape_state[0] = self.UI.ToolItem(toolbar, 'shape_state', icon='assets/outline.png',
                                               tooltip='Outline shape', action=self.shape_stateDialog)
        toolbar.addSeparator()

        # IMAGE EFFECT
        effects_tag = QLabel(self)
        effects_tag.setText('Effects: ')
        toolbar.addWidget(effects_tag)
        effects = ['None', 'grey', 'invert', 'cartoon', 'blur 1', 'blur 2', 'blur 3', 'blur 4', 'sketch']
        effects_combo = self.UI.ComboItem(toolbar, icon_size=(100, 40), action=self.setImageEffect)
        for effect in effects:
            effects_combo.addItem(effect)

    def setNewCanvas(self, width, height, dialog=None, image=None):
        """
        Set a new canvas with given width and height.
        """
        width = int(width)
        height = int(height)
        if self.canvas:
            self.layout.removeWidget(self.canvas)
        if image is not None:
            self.image = image
        else:
            self.image = np.full((height, width, 3), [255, 255, 255], dtype=np.uint8)
        h, w, _ = self.image.shape
        if w > self.width():
            w = self.width()
        if h > self.height():
            h = self.height() - 75
        self.image = self.CV.resizeImage(self.image, (w, h))
        self.canvas = self.UI.createCanvas(self.CV.toQImage(self.image))
        self.canvas.setMouseTracking(True)
        self.layout.addWidget(self.canvas)
        self.renderImage()
        if dialog:
            dialog.close()

        if self.selection_state:
            self.selection = None
            self.selection_state = None
            self.cropped_image = None

    def renderImage(self):
        """
        Render the current image on the canvas.
        """
        self.canvas.setPixmap(QPixmap(self.CV.toQImage(self.image, self.image_effect)))

    def setActiveTool(self, tool, name):
        """
        Set the active tool.
        """
        if self.active_tool:
            self.active_tool[0].setStyleSheet('background-color:none;')

        if name == 'crop':
            if self.selection_state:
                self.setNewCanvas(self.canvas.width(), self.canvas.height(), image=self.cropped_image)
                self.selection = None
                self.selection_state = None
                self.cropped_image = None
            self.active_tool = None
            return
        elif self.selection_state and self.cropped_image is not None:
            self.image = self.CV.drawImage(self.image, self.selection[0], self.selection[1],
                                           self.cropped_image,
                                           (self.canvas.width(), self.canvas.height()))
            self.renderImage()
            self.selection = None
            self.selection_state = None
            self.cropped_image = None
            self.renderImage()

        self.active_tool = (tool, name)
        tool.setStyleSheet('border:2px solid black;')

    def fileDialog(self, mode):
        """
        Open or save file dialog based on mode.
        """
        image_filter = "Images (*.png *.jpg *.jpeg)"
        if mode == 'open':
            file_path, _ = QFileDialog.getOpenFileName(self, caption="File Directory",filter=image_filter)
            if file_path != '':
                print(file_path)
                self.image = self.CV.loadImage(file_path)
                self.setNewCanvas(0, 0, image=self.image)
        elif mode == 'save':
            file_path, _ = QFileDialog.getSaveFileName(self, "Save File","PNG(*.png);;JPEG(*.jpg *.jpeg)")
            if file_path != '' and self.image is not None:
                self.image = self.CV.apply_filter(self.image, self.image_effect)
                if self.image_effect is None:
                    self.CV.saveImage(file_path, self.image,False)
                self.CV.saveImage(file_path, self.image,True)

    def setCanvasDialog(self):
        """
        Show dialog to set canvas properties.
        """
        dialog = QDialog(self)
        dialog.setStyleSheet("background-color:white;")
        dialog.setFixedSize(300, 200)

        dialog_layout = QVBoxLayout(dialog)
        header_layout = QHBoxLayout(dialog)
        width_layout = QHBoxLayout(dialog)
        height_layout = QHBoxLayout(dialog)
        button_layout = QHBoxLayout(dialog)

        header = self.UI.simpleText(text='Canvas properties', font=("Times New Romans", 16), color="black")

        width_prop = self.UI.simpleText(text='Width:', font=("Ariel", 12))
        width_value = self.UI.LineEdit("700", size=(80, 30), align=Qt.AlignCenter,
                                       valid=QIntValidator(bottom=0, top=1980))

        height_prop = self.UI.simpleText(text='Height:', font=("Ariel", 12))
        height_value = self.UI.LineEdit(text='500', size=(80, 30), align=Qt.AlignCenter,
                                        valid=QIntValidator(bottom=0, top=1180))

        create_button = self.UI.PushButton(text="Create", color="lightblue",
                                           action=lambda: self.setNewCanvas(width=width_value.displayText(),
                                                                            height=height_value.displayText(),
                                                                            dialog=dialog))
        cancel_button = self.UI.PushButton(text="Cancel", action=lambda: dialog.close())

        dialog_layout.addStretch(1)
        dialog_layout.addLayout(header_layout)
        dialog_layout.addStretch(1)
        dialog_layout.addLayout(width_layout)
        dialog_layout.addStretch(1)
        dialog_layout.addLayout(height_layout)
        dialog_layout.addStretch(1)
        dialog_layout.addLayout(button_layout)
        dialog_layout.addStretch(1)

        header_layout.addStretch(2)
        header_layout.addWidget(header)
        header_layout.addStretch(2)

        width_layout.addStretch(1)
        width_layout.addWidget(width_prop)
        width_layout.addStretch(1)
        width_layout.addWidget(width_value)
        width_layout.addStretch(1)

        height_layout.addStretch(1)
        height_layout.addWidget(height_prop)
        height_layout.addStretch(1)
        height_layout.addWidget(height_value)
        height_layout.addStretch(1)

        button_layout.addWidget(create_button)
        button_layout.addWidget(cancel_button)

        dialog.exec_()

    def fontDialog(self, font):
        """
        Set font data based on user selection.
        """
        self.font_data[0] = font

    def fontSizeDialog(self, size):
        """
        Set font size based on user selection.
        """
        self.font_data[1] = 0 + (0.05 * size)

    def colorDialog(self, item, color_type):
        """
        Set color based on user selection.
        """
        if color_type == 'primary':
            self.primary_color[1] = QColorDialog().getColor().getRgb()[:3]
            self.primary_color[1] = self.primary_color[1][::-1]
            self.active_color = self.primary_color[1]
            self.primary_color[0] = item
        elif color_type == 'secondary':
            self.secondary_color[1] = QColorDialog().getColor().getRgb()[:3]
            self.secondary_color[1] = self.secondary_color[1][::-1]
            self.active_color = self.secondary_color[1]
            self.secondary_color[0] = item

        square = np.full((20, 20, 3), self.active_color, dtype=np.uint8)
        item.setIcon(self.CV.toIcon(square))

    def thicknessDialog(self, thickness):
        """
        Set thickness based on user selection.
        """
        self.thickness = int(thickness[:-2])

    def shape_stateDialog(self):
        """
        Toggle between filled and outline shape state.
        """
        if not self.shape_state[1]:
            self.shape_state[0].setIcon(QIcon('assets/filled.png'))
            self.shape_state[0].setToolTip('Filled shape')
            self.shape_state[1] = True
        else:
            self.shape_state[0].setIcon(QIcon('assets/outline.png'))
            self.shape_state[0].setToolTip('Outline shape')
            self.shape_state[1] = False

    def innerMousePos(self, event, rect_object):
        """
        Get mouse position relative to a rectangle.
        """
        x, y, width, height = rect_object.getRect()
        x = event.x() - x
        y = event.y() - y - 56
        return x, y

    def getMinMax(self, pt1, pt2):
        """
        Get minimum and maximum coordinates from two points.
        """
        min_x = min(pt1[0], pt2[0])
        max_x = max(pt1[0], pt2[0])
        min_y = min(pt1[1], pt2[1])
        max_y = max(pt1[1], pt2[1])
        return (min_x, max_x), (min_y, max_y)

    def rotateImage(self, side=None):
        """
        Rotate the image clockwise or counterclockwise.
        """
        if self.canvas:
            self.image = self.CV.rotateImage(self.image, side)
            self.canvas.setFixedSize(self.image.shape[1], self.image.shape[0])
            self.setFixedSize(self.image.shape[1] + 200, self.image.shape[0] + 50)
            self.setMaximumSize(self.local_width, self.local_height)
            self.renderImage()

    def flipImage(self, side=None):
        """
        Flip the image vertically or horizontally.
        """
        if self.canvas:
            self.image = self.CV.flipImage(self.image, side)
            self.renderImage()

    def setImageEffect(self, effect):
        """
        Set image effect based on user selection.
        """
        if self.canvas:
            if effect == 'none':
                effect = None
            self.image_effect = effect
            self.renderImage()

if __name__ == '__main__':
    # Initialize the application
    pyPaint = QApplication([])
    QApplication.setOverrideCursor(Qt.ArrowCursor)

    pyPaint.setWindowIcon(QIcon('assets/logo.png'))
    core = Core(app=pyPaint, width=1200, height=720, title='PyPaint')
    core.show()
    pyPaint.exec_()
