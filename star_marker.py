# star_marker.py

from PyQt5 import QtWidgets, QtGui, QtCore

class StarMarker(QtWidgets.QLabel):
    """
    A draggable star-shaped marker widget.

    This widget appears as a small star, which can be clicked and dragged around inside its parent widget.
    It's useful as a visual marker for selecting or annotating positions in a GUI.

    Parameters:
    ----------
    parent : QWidget
        The parent widget (e.g., a QLabel or QWidget where this marker will be placed).
    color : str
        Color of the star (e.g., 'red', 'blue', 'yellow').

    Usage:
    ------
    star = StarMarker(parent=image_frame, color='red')
    star.move(100, 100)
    star.show()
    """

    def __init__(self, parent=None, color='red'):
        super(StarMarker, self).__init__(parent)
        self.color = color
        self.setFixedSize(20, 20)
        self.setStyleSheet("background: transparent;")
        self.setCursor(QtCore.Qt.OpenHandCursor)
        self.dragging = False
        self.offset = QtCore.QPoint()

    def paintEvent(self, event):
        """
        Paints the star shape using QPainter.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QBrush(QtGui.QColor(self.color)))
        painter.setPen(QtGui.QPen(QtGui.QColor('black'), 1))

        star = QtGui.QPolygon([
            QtCore.QPoint(10, 0), QtCore.QPoint(12, 7), QtCore.QPoint(20, 7),
            QtCore.QPoint(14, 12), QtCore.QPoint(16, 20), QtCore.QPoint(10, 15),
            QtCore.QPoint(4, 20), QtCore.QPoint(6, 12), QtCore.QPoint(0, 7), QtCore.QPoint(8, 7),
        ])
        painter.drawPolygon(star)

    def mousePressEvent(self, event):
        """
        Starts dragging the star.
        """
        if event.button() == QtCore.Qt.LeftButton:
            self.dragging = True
            self.setCursor(QtCore.Qt.ClosedHandCursor)
            self.offset = event.pos()

    def mouseMoveEvent(self, event):
        """
        Updates the position of the star while dragging.
        """
        if self.dragging:
            new_pos = self.mapToParent(event.pos() - self.offset)
            self.move(new_pos)

    def mouseReleaseEvent(self, event):
        """
        Ends the dragging action.
        """
        self.dragging = False
        self.setCursor(QtCore.Qt.OpenHandCursor)
