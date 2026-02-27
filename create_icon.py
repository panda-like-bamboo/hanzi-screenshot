import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QIcon
from PyQt5.QtCore import Qt, QSize

def create_tray_icon():
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    painter.setPen(QPen(QColor('#00a8ff'), 3))
    painter.setBrush(Qt.NoBrush)
    painter.drawRect(10, 10, 44, 44)
    
    painter.setPen(QPen(QColor('#00a8ff'), 2))
    painter.drawLine(10, 10, 54, 54)
    painter.drawLine(10, 54, 54, 10)
    
    painter.end()
    
    return QIcon(pixmap)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    icon = create_tray_icon()
    pixmap = icon.pixmap(QSize(64, 64))
    pixmap.save('tray-icon.png', 'PNG')
    print('Icon created: tray-icon.png')
    sys.exit(0)
