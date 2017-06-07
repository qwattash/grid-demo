
import sys
import numpy as np
import enum

from itertools import starmap, repeat, chain

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QSizePolicy, QGridLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QPushButton, QLabel, QSpinBox
from PyQt5.QtGui import QPainter, QPixmap, QBrush, QColor, QPen, QTransform
from PyQt5.QtCore import QRect, QPoint, QSize, QLineF
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot

class GridModel(QObject):

    class GridItem(enum.IntEnum):
        WALL = 3
        START = 1
        END = 2
        EMPTY = 0

    class GridModelChanged:
        """Model changed event"""
        def __init__(self, model):
            self.model = model

    class GridModelUpdate:
        """Model update event"""
        def __init__(self, **kwargs):
            self.params = kwargs

    model_changed = pyqtSignal(GridModelChanged)

    def __init__(self, w, h):
        super().__init__()
        self.grid = None
        self.max_x = None
        self.max_y = None
        self._set_size(w, h)

        self._item_type = None
        self._start = None
        self._end = None

    @pyqtSlot(GridModelUpdate)
    def model_update(self, evt):
        w = evt.params.get("width", self.max_x)
        h = evt.params.get("height", self.max_y)
        self._set_size(w, h)

    @pyqtSlot(GridItem)
    def pick_item_type(self, itype):
        self._item_type = itype

    def pick_position(self, x, y):
        if self._item_type == GridModel.GridItem.START:
            if self._start:
                self.grid[self._start] = GridModel.GridItem.EMPTY
            self.grid[x, y] = GridModel.GridItem.START
            self._start = (x, y)
        elif self._item_type == GridModel.GridItem.END:
            if self._end:
                self.grid[self._end] = GridModel.GridItem.EMPTY
            self.grid[x, y] = GridModel.GridItem.END
            self._end = (x, y)
        elif self._item_type == GridModel.GridItem.WALL:
            self.grid[x, y] = GridModel.GridItem.WALL
        else:
            self.grid[x, y] = GridModel.GridItem.EMPTY
        self.model_changed.emit(GridModel.GridModelChanged(self))

    def _set_size(self, w, h):
        if self.max_x == w and self.max_y == h:
            return
        self.grid = np.zeros((w, h))
        self.max_x = w
        self.max_y = h
        self.model_changed.emit(GridModel.GridModelChanged(self))

    def get_size(self):
        return self.max_x, self.max_y


class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Pathfinder test")
        self.resize(1024, 768)

        self.main = QWidget()        
        self.layout = QHBoxLayout(self.main)
        self.setCentralWidget(self.main)

        # build subwidgets
        main_size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        main_size.setHorizontalStretch(6)
        bar_size = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        bar_size.setHorizontalStretch(1)

        self.model = GridModel(10, 10)
        self.grid = Grid(self.model)
        self.grid.setSizePolicy(main_size)
        self.selector = Selector(self.model)
        self.selector.setSizePolicy(bar_size)

        self.selector.grid_update.connect(self.model.model_update)
        self.selector.grid_item_type.connect(self.model.pick_item_type)
        self.model.model_changed.connect(self.grid.model_changed)
        self.grid.pick_position.connect(self.model.pick_position)

        self.layout.addSpacing(5)
        self.layout.addWidget(self.grid)
        self.layout.addSpacing(5)
        self.layout.addWidget(self.selector)
        self.layout.addSpacing(5)


class Selector(QWidget):

    grid_update = pyqtSignal(GridModel.GridModelUpdate)
    grid_item_type = pyqtSignal(GridModel.GridItem)

    def __init__(self, model):
        super().__init__()

        self.model = model

        self.layout = QVBoxLayout(self)

        box = QGroupBox("Grid Settings", self)
        box_layout = QVBoxLayout(box)
        # width and height of grid and labels
        self.in_grid_w = QSpinBox()
        self.in_grid_w.setRange(1, 100000)
        self.in_grid_h = QSpinBox()
        self.in_grid_h.setRange(1, 100000)
        self.tgl_start = QPushButton("Start")
        self.tgl_start.setCheckable(True)
        self.tgl_end = QPushButton("Target")
        self.tgl_end.setCheckable(True)
        self.tgl_wall =  QPushButton("Wall")
        self.tgl_wall.setCheckable(True)
        self.tgl_clear = QPushButton("Clear")
        self.tgl_clear.setCheckable(True)
        lb_grid_w = QLabel("Grid width:")
        lb_grid_h = QLabel("Grid height:")
        btn_apply_settings = QPushButton("Apply")        
        # append widgets
        btn_apply_settings.clicked.connect(self._apply_settings)
        self.tgl_start.toggled.connect(self._start_toggle)
        self.tgl_end.toggled.connect(self._end_toggle)
        self.tgl_wall.toggled.connect(self._wall_toggle)
        self.tgl_clear.toggled.connect(self._clear_toggle)
        box_layout.addWidget(lb_grid_w)
        box_layout.addWidget(self.in_grid_w)
        box_layout.addWidget(lb_grid_h)
        box_layout.addWidget(self.in_grid_h)
        box_layout.addWidget(self.tgl_start)
        box_layout.addWidget(self.tgl_end)
        box_layout.addWidget(self.tgl_wall)
        box_layout.addWidget(self.tgl_clear)
        box_layout.addSpacing(10)
        box_layout.addWidget(btn_apply_settings)
        self._update_settings()

        self.layout.addWidget(box)

    def _update_settings(self):
        w, h = self.model.get_size()
        self.in_grid_w.setValue(w)
        self.in_grid_h.setValue(h)

    def _apply_settings(self, event):
        update_evt = GridModel.GridModelUpdate(
            width=self.in_grid_w.value(),
            height=self.in_grid_h.value()
        )
        self.grid_update.emit(update_evt)

    def _start_toggle(self, checked):
        if not checked:
            return 
        self.tgl_end.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.tgl_clear.setChecked(False)
        self.grid_item_type.emit(GridModel.GridItem.START)

    def _end_toggle(self, checked):
        if not checked:
            return 
        self.tgl_start.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.tgl_clear.setChecked(False)
        self.grid_item_type.emit(GridModel.GridItem.END)

    def _wall_toggle(self, checked):
        if not checked:
            return 
        self.tgl_start.setChecked(False)
        self.tgl_end.setChecked(False)
        self.tgl_clear.setChecked(False)
        self.grid_item_type.emit(GridModel.GridItem.WALL)

    def _clear_toggle(self, checked):
        if not checked:
            return 
        self.tgl_start.setChecked(False)
        self.tgl_end.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.grid_item_type.emit(GridModel.GridItem.EMPTY)


class Grid(QWidget):

    pick_position = pyqtSignal("int", "int")

    def __init__(self, model):
        super().__init__()

        self.model = model

        self.grid_x = None
        self.grid_y = None
        self.last_cell = None
        
        self.background = QBrush(QColor(250, 250, 250))
        self.grid_pen = QPen(QColor(40, 40, 40))
        self.wall_brush = QBrush(QColor(100, 100, 100))
        self.start_brush = QBrush(QColor(0, 100, 0))
        self.end_brush = QBrush(QColor(100, 0, 0))

    def update_gridlines(self):
        x = np.arange(0, self.model.max_x)
        y = np.arange(0, self.model.max_y)
        x_args = zip(x, repeat(0), x, repeat(self.model.max_y))
        y_args = zip(repeat(0), y, repeat(self.model.max_x), y)
        self.grid_lines = chain(starmap(QLineF, x_args),
                                starmap(QLineF, y_args))
        self.grid_x = x
        self.grid_y = y

    def coords2cell(self, x, y):
        cell_width = self.width() / self.model.max_x
        cell_height = self.height() / self.model.max_y
        cell_x = int(x / cell_width)
        cell_y = int(y / cell_height)
        return (cell_x, cell_y)

    @pyqtSlot(GridModel.GridModelChanged)
    def model_changed(self, evt):
        self.repaint()

    def paintEvent(self, event):
        rect = event.rect()
        x0, y0, x1, y1 = rect.getCoords()
        painter = QPainter(self)
        transform = QTransform()
        transform.scale((x1 - x0) / self.model.max_x,
                        (y1 - y0) / self.model.max_y)
        painter.setTransform(transform)
        self.grid_pen.setWidth(0)

        self.update_gridlines()
        painter.fillRect(event.rect(), self.background)
        painter.setPen(self.grid_pen)
        painter.drawRect(0, 0, self.model.max_x, self.model.max_y)
        painter.drawLines(self.grid_lines)
        for (x, y), v in np.ndenumerate(self.model.grid):
            if v == GridModel.GridItem.START:
                painter.fillRect(QRect(x, y, 1, 1), self.start_brush)
            elif v == GridModel.GridItem.END:
                painter.fillRect(QRect(x, y, 1, 1), self.end_brush)
            elif v == GridModel.GridItem.WALL:
                painter.fillRect(QRect(x, y, 1, 1), self.wall_brush)

    def mouseMoveEvent(self, evt):
        cell = self.coords2cell(evt.x(), evt.y())
        if cell != self.last_cell:
            self.last_cell = cell
            self.pick_position.emit(*cell)

    def mousePressEvent(self, evt):
        cell = self.coords2cell(evt.x(), evt.y())
        if cell != self.last_cell:
            self.last_cell = cell
            self.pick_position.emit(*cell)

    def mouseReleaseEvent(self, event):
        self.last_cell = None

if __name__ == "__main__":

    app = QApplication(sys.argv)

    w = Window()
    w.show()

    sys.exit(app.exec_())
