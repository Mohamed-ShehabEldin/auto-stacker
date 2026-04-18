from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget,QWidget
from PyQt5 import uic
import sys
from PyQt5.QtCore import QTimer, Qt

from window_interaction_handler import WindowInteractionHandler

from settings_tab import SettingsTab
from pickup_tab import PickupTab

from image_frame_manager import ImageFrameManager
from star_marker import StarMarker
from homo_twist_tab import HomoTwistTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("main_window.ui", self)

        #making the window transparent
        self.setWindowFlags(Qt.WindowStaysOnTopHint)  # Window stays on top
        self.setWindowFlags(Qt.FramelessWindowHint) 
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_TranslucentBackground, True)      
        self.show()
        self.setMouseTracking(True)

        # Setup interaction handler for resizing/drags
        self.interaction_handler = WindowInteractionHandler(self)

        #put the target star in the immage frame:
        self.image_frame: QWidget = self.findChild(QWidget, "image_frame")
        self.target_star_marker = StarMarker(self.image_frame, color = "red")
        self.target_star_marker.move(100, 100)
        self.target_star_marker.show()
        #put the receiver star in the immage frame:
        self.receiver_star_marker = StarMarker(self.image_frame, color = "blue")
        self.receiver_star_marker.move(150, 150)
        self.receiver_star_marker.show()
        # to make the pickup tab know where is the star, we need:
        self.image_frame_manager = ImageFrameManager(self.image_frame, target_star_marker=self.target_star_marker,receiver_star_marker=self.receiver_star_marker)

        # import settings tab
        self.tab_widget: QTabWidget = self.findChild(QTabWidget, "all_tabWidget")
        self.settings_tab = SettingsTab()
        self.tab_widget.addTab(self.settings_tab, "setting") 
        #note it was a whole tab with title and I demoted it to widget for simplicity, so I gave it the title here

        #import pickup_tab
        self.tab_widget: QTabWidget = self.findChild(QTabWidget, "all_tabWidget")
        self.pickup_tab = PickupTab(self.image_frame_manager,self.settings_tab)
        self.tab_widget.addTab(self.pickup_tab, "pick up")

        #import homo_twist_tab
        self.tab_widget: QTabWidget = self.findChild(QTabWidget, "all_tabWidget")
        self.HomoTwistTab = HomoTwistTab(self.image_frame_manager,self.settings_tab)
        self.tab_widget.addTab(self.HomoTwistTab, "HomoTwist up")

        self.show()

    def mousePressEvent(self, event):
        self.interaction_handler.mousePressEvent(event)

    def mouseMoveEvent(self, event):
        self.interaction_handler.mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        self.interaction_handler.mouseReleaseEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
