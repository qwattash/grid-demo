"""
Pathfinder GUI entry point
"""

import logging

from pathfinder.gui import Window

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    Window.mainloop()


