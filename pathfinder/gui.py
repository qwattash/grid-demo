"""
Qt5 GUI interface.
"""

import sys
import enum
import logging

from itertools import starmap, repeat, chain

import numpy as np

from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow
from PyQt5.QtWidgets import QHBoxLayout, QVBoxLayout, QSizePolicy, QGridLayout
from PyQt5.QtWidgets import QGroupBox
from PyQt5.QtWidgets import QPushButton, QLabel, QSpinBox
from PyQt5.QtGui import QPainter, QBrush, QColor, QPen, QTransform
from PyQt5.QtCore import QRect, QLineF
from PyQt5.QtCore import pyqtSignal, pyqtSlot

from pathfinder.world import WorldModelND, Material
from pathfinder.worldmanager import QtWorldManager, WorldManager

logger = logging.getLogger(__name__)

class Window(QMainWindow):
    """Top level GUI handler."""

    @staticmethod
    def mainloop():
        """Create the main window and enter the qt main loop."""
        app = QApplication(sys.argv)
        w_main = Window()
        w_main.show()
        sys.exit(app.exec_())

    def __init__(self):
        """
        Main window constructor.

        Initialize the layout and connections between signals in
        the widget and the world/algorithm managers.
        """
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

        self.world_mgr = QtWorldManager(WorldModelND((0, 0)))
        self.grid = GridView()
        self.grid.setSizePolicy(main_size)
        self.selector = Selector()
        self.selector.setSizePolicy(bar_size)

        self.selector.grid_update.connect(self.world_mgr.model_update)
        self.selector.select_material.connect(self.world_mgr.select_material)
        self.world_mgr.model_changed.connect(self.grid.model_changed)
        self.world_mgr.model_shape_changed.connect(
            self.grid.model_shape_changed)
        self.grid.pick_position.connect(self.world_mgr.pick_position)

        self.layout.addSpacing(5)
        self.layout.addWidget(self.grid)
        self.layout.addSpacing(5)
        self.layout.addWidget(self.selector)
        self.layout.addSpacing(5)


class Selector(QWidget):
    """
    The selector widget handles the grid setup options in the GUI.
    """

    grid_update = pyqtSignal(tuple)
    """Signal emitted when the user resizes the grid."""

    select_material = pyqtSignal(Material)
    """Signal emitted when the user selects a material to use."""

    def __init__(self):
        """
        Selector widget constructor.
        Build the internal layout of the widget and connect signals
        to sub-widgets.
        """
        super().__init__()

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
        self.tgl_wall = QPushButton("Wall")
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

        # initial suggested size
        self.in_grid_w.setValue(10)
        self.in_grid_h.setValue(10)

        self.layout.addWidget(box)

    def _apply_settings(self, event): # pylint: disable=unused-argument
        """
        Qt click event slot on the settings confirmation button.

        Trigger the grid_update signal.
        """
        new_shape = (
            self.in_grid_w.value(),
            self.in_grid_h.value()
        )
        self.grid_update.emit(new_shape)

    def _start_toggle(self, checked):
        """
        Qt toggle event slot on the start location selector button.
        """
        if not checked:
            return
        self.tgl_end.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.tgl_clear.setChecked(False)
        # self.grid_item_type.emit(Material.AIR)

    def _end_toggle(self, checked):
        """
        Qt toggle event slot on the end location selector button.
        """
        if not checked:
            return
        self.tgl_start.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.tgl_clear.setChecked(False)
        # self.select_material.emit(Material.AIR)

    def _wall_toggle(self, checked):
        """
        Qt toggle event slot on the WALL material selector button.

        Trigger the select_material signal.
        """
        if not checked:
            return
        self.tgl_start.setChecked(False)
        self.tgl_end.setChecked(False)
        self.tgl_clear.setChecked(False)
        self.select_material.emit(Material.WALL)

    def _clear_toggle(self, checked):
        """
        Qt toggle event slot on the AIR material selector button.

        Trigger the select_material signal.
        """
        if not checked:
            return
        self.tgl_start.setChecked(False)
        self.tgl_end.setChecked(False)
        self.tgl_wall.setChecked(False)
        self.select_material.emit(Material.AIR)


class GridView(QWidget):
    """
    Top level widget for the world grid view region.

    This will have different internal representations depending on the
    world configuration that the user selects.
    """

    pick_position = pyqtSignal(tuple)
    """Signal emitted when a position is picked by the user on the grid."""

    class ColorPalette(enum.Enum):
        """Color palette enum."""

        BACKGROUND = QColor(250, 250, 250)
        GRID_LINE = QColor(40, 40, 40)
        WALL = QColor(100, 100, 100)
        START = QColor(0, 100, 0)
        END = QColor(100, 0, 0)


    def __init__(self):
        """
        Top level grid widget constructor.

        Initialize common structure and signal handler that are dispatched
        to sub-widgets.
        """
        super().__init__()

        self.layout = QGridLayout(self)
        """Widget layout."""

        self.display_strategy = None
        """Display strategy for 2D, 3D and other world sizes."""

        self.grid_ticks = []
        """
        nxm array of coordinates of natural unit grid lines.
        n = dimension of the world
        m = max dimension coordinate
        """

    @pyqtSlot(WorldManager)
    def model_changed(self, manager):
        """
        Qt signal slot that receives updates from the world manager,
        whenever some position state has changed.
        """
        self.update_grid_ticks(manager.size)
        self.display_strategy.model_changed(manager)

    @pyqtSlot(WorldManager)
    def model_shape_changed(self, manager):
        """
        Qt signal slot that receives update from the world manager,
        whenever the world is reshaped.
        """
        if len(manager.size) == 2:
            self.display_strategy = Grid2dDisplay(self, manager)
        elif len(manager.size) == 3:
            # self.display_strategy = Grid3dDisplay(self, manager)
            assert False
        else:
            logger.error("Unsupported world dimension %d, coerce to 3D",
                         len(manager.size))
            # self.display_strategy = Grid3dDisplay(self, manager)
            assert False
        self.model_changed(manager)

    def update_grid_ticks(self, size):
        """
        Generate the coordinates for the unit ticks of
        the grid.

        :param size: n-d array with the maximum coordinate for
        each dimension.
        """
        self.grid_ticks = [np.arange(0, m) for m in size]


class Grid2dDisplay(QWidget):
    """
    XXX refactor
    """

    def __init__(self, view, manager):
        """
        Initialize brushes and pens, add the display
        viewport to the parent layout.
        """
        super().__init__()

        self.view = view
        """Top level grid view widget with common state."""

        layout = view.layout()
        layout.addWidget(self, 0, 0)

        self.manager = manager
        """World manager."""

        self.background = QBrush(view.palette.background)
        self.grid_pen = QPen(view.palette.grid_line)
        self.wall_brush = QBrush(view.palette.wall)
        self.start_brush = QBrush(view.palette.start)
        self.end_brush = QBrush(view.palette.end)

        self.last_selected_cell = None
        """Coords of the last grid cell selected by the user."""

    def __del__(self):
        """
        Remove display viewport from parent layout.
        """
        layout = self.view.layout()
        layout.removeWidget(self)

    def model_changed(self, manager):
        """
        Propagate the model chanved event
        """
        self.manager = manager
        self.repaint()

    def coords2cell(self, x, y):
        """Convert event coordinates to cell coordinates."""
        max_x, max_y = self.manager.size[:2]
        cell_width = self.width() / max_x
        cell_height = self.height() / max_y
        cell_x = int(x / cell_width)
        cell_y = int(y / cell_height)
        return (cell_x, cell_y)

    def paintEvent(self, event):
        """
        Qt paint event slot handler.
        """
        # get the draw rectangle
        rect = event.rect()
        max_x, max_y = self.manager.size[:2]
        assert max_x > 0 and max_y > 0
        # build the painter and set the coordinates scale
        # transformation + the zoom transform
        painter = QPainter(self)
        transform = QTransform()
        transform.scale((rect.right() - rect.left()) / max_x,
                        (rect.bottom() - rect.top()) / max_y)
        painter.setTransform(transform)

        # draw the frame rect
        self.grid_pen.setWidth(0)
        painter.fillRect(event.rect(), self.background)
        painter.setPen(self.grid_pen)
        painter.drawRect(0, 0, max_x, max_y)
        # draw the grid
        x_ticks, y_ticks = self.view.grid_ticks[:2]
        x_segs = zip(x_ticks, repeat(0), x_ticks, repeat(max_y))
        y_segs = zip(repeat(0), y_ticks, repeat(max_x), y_ticks)
        grid_lines = chain(starmap(QLineF, x_segs), starmap(QLineF, y_segs))
        painter.drawLines(grid_lines)

        # fill the grid cells
        world_grid = self.manager.world.query((0, 0), (max_x, max_y))
        for (x, y), val in np.ndenumerate(world_grid):
            if val == Material.WALL:
                painter.fillRect(QRect(x, y, 1, 1), self.wall_brush)
            # these will be in the algorithm manager
            # if v == GridModel.GridItem.START:
            #     painter.fillRect(QRect(x, y, 1, 1), self.start_brush)
            # elif v == GridModel.GridItem.END:
            #     painter.fillRect(QRect(x, y, 1, 1), self.end_brush)

    def mouseMoveEvent(self, evt):
        """
        Qt mouse event handler.
        """
        cell = self.coords2cell(evt.x(), evt.y())
        if cell != self.last_selected_cell:
            self.last_selected_cell = cell
            self.view.pick_position.emit(cell)

    def mousePressEvent(self, evt):
        """
        Qt mouse press event handler.
        """
        cell = self.coords2cell(evt.x(), evt.y())
        if cell != self.last_selected_cell:
            self.last_selected_cell = cell
            self.view.pick_position.emit(cell)

    def mouseReleaseEvent(self, evt): # pylint: disable=unused-argument
        """
        Qt mouse release event handler.
        """
        self.last_selected_cell = None
