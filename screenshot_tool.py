"""
Screenshot Tool - A full-featured desktop screenshot application
Uses Windows native hotkey API for better compatibility
"""

import sys
import os
import json
import math
import random
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QGridLayout, QSystemTrayIcon,
    QMenu, QAction, QDialog, QFileDialog, QColorDialog,
    QSpinBox, QCheckBox, QComboBox, QGroupBox, QMessageBox,
    QListWidget, QListWidgetItem, QScrollArea, QFrame, QLineEdit,
    QShortcut, QInputDialog, QSlider, QTextEdit, QProgressBar
)
from PyQt5.QtCore import (
    Qt, QPoint, QRect, QSize, QTimer, pyqtSignal, QSettings,
    QBuffer, QByteArray
)
from PyQt5.QtGui import (
    QPainter, QColor, QPen, QBrush, QFont, QPixmap, QIcon,
    QCursor, QFontMetrics, QKeySequence, QPolygon
)

from PIL import Image, ImageGrab, ImageDraw, ImageFont

if sys.platform == 'win32':
    import ctypes
    import ctypes.wintypes
    
    user32 = ctypes.windll.user32
    
    MOD_CONTROL = 0x0002
    MOD_SHIFT = 0x0004
    MOD_ALT = 0x0001
    MOD_NOREPEAT = 0x4000
    
    WM_HOTKEY = 0x0312


class Config:
    DEFAULT_CONFIG = {
        'shortcut': 'ctrl+shift+a',
        'save_path': str(Path.home() / 'Pictures' / 'screenshots'),
        'default_format': 'PNG',
        'default_color': '#FF0000',
        'default_line_width': 2,
        'auto_copy': True,
        'show_magnifier': True,
        'max_history': 50,
        'auto_start': False
    }
    
    def __init__(self):
        self.config_file = Path.home() / '.screenshot_tool' / 'config.json'
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config = self.load()
    
    def load(self) -> dict:
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    return {**self.DEFAULT_CONFIG, **saved}
            except Exception:
                pass
        return self.DEFAULT_CONFIG.copy()
    
    def save(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, indent=2, ensure_ascii=False)
    
    def get(self, key: str, default=None):
        return self.config.get(key, default)
    
    def set(self, key: str, value):
        self.config[key] = value
        self.save()


class AutoStartManager:
    APP_NAME = 'ScreenshotTool'
    
    def __init__(self):
        self.app_path = self._get_app_path()
    
    def _get_app_path(self) -> str:
        if getattr(sys, 'frozen', False):
            return sys.executable
        return str(Path(__file__).absolute())
    
    def is_enabled(self) -> bool:
        if sys.platform == 'win32':
            return self._is_enabled_windows()
        elif sys.platform == 'darwin':
            return self._is_enabled_macos()
        else:
            return self._is_enabled_linux()
    
    def enable(self) -> bool:
        try:
            if sys.platform == 'win32':
                return self._enable_windows()
            elif sys.platform == 'darwin':
                return self._enable_macos()
            else:
                return self._enable_linux()
        except Exception as e:
            print(f'Failed to enable auto-start: {e}')
            return False
    
    def disable(self) -> bool:
        try:
            if sys.platform == 'win32':
                return self._disable_windows()
            elif sys.platform == 'darwin':
                return self._disable_macos()
            else:
                return self._disable_linux()
        except Exception as e:
            print(f'Failed to disable auto-start: {e}')
            return False
    
    def _is_enabled_windows(self) -> bool:
        import winreg
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            winreg.QueryValueEx(key, self.APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return False
        except Exception:
            return False
    
    def _enable_windows(self) -> bool:
        import winreg
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.SetValueEx(key, self.APP_NAME, 0, winreg.REG_SZ, f'"{self.app_path}"')
            winreg.CloseKey(key)
            return True
        except Exception as e:
            print(f'Windows auto-start enable failed: {e}')
            return False
    
    def _disable_windows(self) -> bool:
        import winreg
        key_path = r'Software\Microsoft\Windows\CurrentVersion\Run'
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            winreg.DeleteValue(key, self.APP_NAME)
            winreg.CloseKey(key)
            return True
        except FileNotFoundError:
            return True
        except Exception as e:
            print(f'Windows auto-start disable failed: {e}')
            return False
    
    def _is_enabled_macos(self) -> bool:
        plist_path = Path.home() / 'Library' / 'LaunchAgents' / f'com.{self.APP_NAME.lower()}.plist'
        return plist_path.exists()
    
    def _enable_macos(self) -> bool:
        plist_path = Path.home() / 'Library' / 'LaunchAgents' / f'com.{self.APP_NAME.lower()}.plist'
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.{self.APP_NAME.lower()}</string>
    <key>ProgramArguments</key>
    <array>
        <string>{self.app_path}</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>'''
        try:
            plist_path.parent.mkdir(parents=True, exist_ok=True)
            plist_path.write_text(plist_content)
            return True
        except Exception as e:
            print(f'macOS auto-start enable failed: {e}')
            return False
    
    def _disable_macos(self) -> bool:
        plist_path = Path.home() / 'Library' / 'LaunchAgents' / f'com.{self.APP_NAME.lower()}.plist'
        try:
            if plist_path.exists():
                plist_path.unlink()
            return True
        except Exception as e:
            print(f'macOS auto-start disable failed: {e}')
            return False
    
    def _is_enabled_linux(self) -> bool:
        desktop_path = Path.home() / '.config' / 'autostart' / f'{self.APP_NAME.lower()}.desktop'
        return desktop_path.exists()
    
    def _enable_linux(self) -> bool:
        desktop_path = Path.home() / '.config' / 'autostart' / f'{self.APP_NAME.lower()}.desktop'
        desktop_content = f'''[Desktop Entry]
Type=Application
Name={self.APP_NAME}
Exec={self.app_path}
Icon={self.APP_NAME.lower()}
Comment=Screenshot Tool
Terminal=false
Categories=Utility;
'''
        try:
            desktop_path.parent.mkdir(parents=True, exist_ok=True)
            desktop_path.write_text(desktop_content)
            return True
        except Exception as e:
            print(f'Linux auto-start enable failed: {e}')
            return False
    
    def _disable_linux(self) -> bool:
        desktop_path = Path.home() / '.config' / 'autostart' / f'{self.APP_NAME.lower()}.desktop'
        try:
            if desktop_path.exists():
                desktop_path.unlink()
            return True
        except Exception as e:
            print(f'Linux auto-start disable failed: {e}')
            return False


class HistoryManager:
    def __init__(self, config: Config):
        self.config = config
        self.history_file = Path.home() / '.screenshot_tool' / 'history.json'
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self.history: List[Dict[str, Any]] = self.load()
    
    def load(self) -> List[Dict[str, Any]]:
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return[]
    
    def save(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def add(self, image_path: str, thumbnail: str = None):
        entry = {
            'id': datetime.now().timestamp(),
            'timestamp': datetime.now().isoformat(),
            'path': image_path,
            'thumbnail': thumbnail
        }
        self.history.insert(0, entry)
        
        max_history = self.config.get('max_history', 50)
        if len(self.history) > max_history:
            removed = self.history[max_history:]
            for item in removed:
                try:
                    if item.get('path') and os.path.exists(item['path']):
                        os.remove(item['path'])
                except Exception:
                    pass
            self.history = self.history[:max_history]
        
        self.save()
    
    def remove(self, entry_id: float):
        for i, item in enumerate(self.history):
            if item['id'] == entry_id:
                try:
                    if item.get('path') and os.path.exists(item['path']):
                        os.remove(item['path'])
                except Exception:
                    pass
                self.history.pop(i)
                self.save()
                break
    
    def clear(self):
        for item in self.history:
            try:
                if item.get('path') and os.path.exists(item['path']):
                    os.remove(item['path'])
            except Exception:
                pass
        self.history =[]
        self.save()


class DrawingTool:
    RECT = 'rect'
    ELLIPSE = 'ellipse'
    ARROW = 'arrow'
    LINE = 'line'
    DASHED = 'dashed'
    PEN = 'pen'
    TEXT = 'text'
    MOSAIC = 'mosaic'
    SMART_MOSAIC = 'smart_mosaic'


class SensitiveDataDetector:
    PHONE = 'phone'
    ID_CARD = 'id_card'
    BANK_CARD = 'bank_card'
    EMAIL = 'email'
    IP_ADDRESS = 'ip_address'
    
    PATTERNS = {
        'phone': r'1[3-9]\d{9}',
        'id_card': r'\d{17}[\dXx]',
        'bank_card': r'\d{16,19}',
        'email': r'[\w.-]+@[\w.-]+\.\w+',
        'ip_address': r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}'
    }
    
    LABELS = {
        'phone': '手机号',
        'id_card': '身份证',
        'bank_card': '银行卡',
        'email': '邮箱',
        'ip_address': 'IP地址'
    }
    
    @classmethod
    def detect_all(cls, text: str) -> List[Dict]:
        import re
        results = []
        for data_type, pattern in cls.PATTERNS.items():
            for match in re.finditer(pattern, text):
                results.append({
                    'type': data_type,
                    'label': cls.LABELS.get(data_type, data_type),
                    'value': match.group(),
                    'start': match.start(),
                    'end': match.end()
                })
        return results
    
    @classmethod
    def detect_in_positions(cls, text: str, positions: List[Dict]) -> List[Dict]:
        import re
        results = []
        for pos in positions:
            text_region = text[pos['start']:pos['end']] if 'start' in pos and 'end' in pos else ''
            for data_type, pattern in cls.PATTERNS.items():
                if re.search(pattern, text_region):
                    results.append({
                        'type': data_type,
                        'label': cls.LABELS.get(data_type, data_type),
                        'value': text_region,
                        'rect': pos.get('rect')
                    })
        return results


class OCRManager:
    _instance = None
    _ocr_engine = None
    _is_loading = False
    _is_available = False
    _model_path = None
    
    MODEL_DIR = Path.home() / '.screenshot_tool' / 'models' / 'ocr'
    MODEL_URLS = {
        'det': 'https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_det_infer.tar',
        'rec': 'https://paddleocr.bj.bcebos.com/PP-OCRv3/chinese/ch_PP-OCRv3_rec_infer.tar',
        'cls': 'https://paddleocr.bj.bcebos.com/dygraph_v2.0/ch/ch_ppocr_mobile_v2.0_cls_infer.tar'
    }
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def is_available(cls) -> bool:
        return cls._is_available
    
    @classmethod
    def is_loading(cls) -> bool:
        return cls._is_loading
    
    @classmethod
    def get_model_path(cls) -> Path:
        return cls.MODEL_DIR
    
    @classmethod
    def check_models_exist(cls) -> bool:
        return cls.MODEL_DIR.exists() and any(cls.MODEL_DIR.iterdir()) if cls.MODEL_DIR.exists() else False
    
    @classmethod
    def initialize(cls, callback=None) -> bool:
        if cls._is_available:
            return True
        
        if cls._is_loading:
            return False
        
        cls._is_loading = True
        
        try:
            from paddleocr import PaddleOCR
            import warnings
            warnings.filterwarnings('ignore')
            
            cls._ocr_engine = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                use_gpu=False,
                show_log=False,
                det_model_dir=str(cls.MODEL_DIR / 'det'),
                rec_model_dir=str(cls.MODEL_DIR / 'rec'),
                cls_model_dir=str(cls.MODEL_DIR / 'cls')
            )
            cls._is_available = True
            cls._is_loading = False
            if callback:
                callback(True)
            return True
        except ImportError:
            cls._is_loading = False
            if callback:
                callback(False, 'PaddleOCR not installed. Run: pip install paddlepaddle paddleocr')
            return False
        except Exception as e:
            cls._is_loading = False
            if callback:
                callback(False, str(e))
            return False
    
    @classmethod
    def recognize(cls, image) -> List[Dict]:
        if not cls._is_available or cls._ocr_engine is None:
            return []
        
        try:
            import numpy as np
            
            if isinstance(image, QPixmap):
                buffer = QBuffer()
                buffer.open(QBuffer.ReadWrite)
                image.save(buffer, 'PNG')
                pil_image = Image.open(buffer)
                img_array = np.array(pil_image)
            elif isinstance(image, Image.Image):
                img_array = np.array(image)
            else:
                return []
            
            if len(img_array.shape) == 2:
                img_array = np.stack([img_array] * 3, axis=-1)
            elif img_array.shape[2] == 4:
                img_array = img_array[:, :, :3]
            
            result = cls._ocr_engine.ocr(img_array, cls=True)
            
            ocr_results = []
            if result and result[0]:
                for line in result[0]:
                    if len(line) >= 2:
                        box = line[0]
                        text = line[1][0]
                        confidence = line[1][1]
                        
                        x_coords = [p[0] for p in box]
                        y_coords = [p[1] for p in box]
                        
                        ocr_results.append({
                            'text': text,
                            'confidence': confidence,
                            'box': box,
                            'rect': QRect(
                                int(min(x_coords)),
                                int(min(y_coords)),
                                int(max(x_coords) - min(x_coords)),
                                int(max(y_coords) - min(y_coords))
                            )
                        })
            
            return ocr_results
        except Exception as e:
            print(f'OCR error: {e}')
            return []
    
    @classmethod
    def get_all_text(cls, image) -> str:
        results = cls.recognize(image)
        return '\n'.join([r['text'] for r in results])


class ScreenshotOverlay(QWidget):
    screenshot_taken = pyqtSignal(object)
    cancelled = pyqtSignal()
    
    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setCursor(Qt.CrossCursor)
        
        self.start_pos: Optional[QPoint] = None
        self.end_pos: Optional[QPoint] = None
        self.is_selecting = False
        self.selected_rect: Optional[QRect] = None
        self.is_active = False
        
        self.screen_pixmap: Optional[QPixmap] = None
        self.dark_overlay = QColor(0, 0, 0, 80)
        
        self.show_magnifier = config.get('show_magnifier', True)
        self.magnifier_size = 150
        self.magnifier_zoom = 4
        
        self.init_ui()
    
    def init_ui(self):
        self.hint_label = QLabel('Drag to select screenshot area, press ESC to cancel', self)
        self.hint_label.setStyleSheet('''
            QLabel {
                background-color: rgba(0, 0, 0, 180);
                color: white;
                padding: 12px 24px;
                border-radius: 6px;
                font-size: 14px;
            }
        ''')
        self.hint_label.adjustSize()
    
    def start_screenshot(self):
        if self.is_active:
            print('Screenshot already in progress, ignoring...')
            return
        
        screen = QApplication.primaryScreen()
        self.screen_pixmap = screen.grabWindow(0)
        
        screen_geometry = screen.geometry()
        self.setGeometry(screen_geometry)
        
        self.start_pos = None
        self.end_pos = None
        self.is_selecting = False
        self.selected_rect = None
        self.is_active = True
        
        self.show()
        self.showFullScreen()
        self.setFocus()
        self.activateWindow()
        self.raise_()
        
        hint_width = self.hint_label.width()
        hint_height = self.hint_label.height()
        self.hint_label.move(
            (self.width() - hint_width) // 2,
            (self.height() - hint_height) // 2
        )
        self.hint_label.show()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        if self.screen_pixmap:
            painter.drawPixmap(0, 0, self.screen_pixmap)
        
        if self.start_pos and self.end_pos:
            rect = QRect(self.start_pos, self.end_pos).normalized()
            
            painter.fillRect(self.rect(), self.dark_overlay)
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(rect, Qt.transparent)
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)
            
            pen = QPen(QColor('#00a8ff'), 2)
            painter.setPen(pen)
            painter.drawRect(rect)
            
            size_text = f'{rect.width()} x {rect.height()}'
            font = QFont('Arial', 12)
            painter.setFont(font)
            fm = QFontMetrics(font)
            # Support PyQt5 >= 5.11
            text_width = fm.horizontalAdvance(size_text) if hasattr(fm, 'horizontalAdvance') else fm.width(size_text)
            
            text_bg_rect = QRect(
                rect.x() + (rect.width() - text_width) // 2 - 8,
                rect.y() - 28,
                text_width + 16,
                24
            )
            painter.fillRect(text_bg_rect, QColor(0, 0, 0, 180))
            painter.setPen(Qt.white)
            painter.drawText(
                text_bg_rect.x() + 8,
                text_bg_rect.y() + 17,
                size_text
            )
        
        if self.show_magnifier and self.start_pos is None:
            cursor_pos = self.mapFromGlobal(QCursor.pos())
            self.draw_magnifier(painter, cursor_pos)
    
    def draw_magnifier(self, painter: QPainter, pos: QPoint):
        magnifier_x = pos.x() + 20
        magnifier_y = pos.y() + 20
        
        if magnifier_x + self.magnifier_size > self.width():
            magnifier_x = pos.x() - self.magnifier_size - 20
        if magnifier_y + self.magnifier_size > self.height():
            magnifier_y = pos.y() - self.magnifier_size - 20
        
        painter.setPen(QPen(QColor('#00a8ff'), 2))
        painter.setBrush(Qt.NoBrush)
        painter.drawEllipse(
            magnifier_x, magnifier_y,
            self.magnifier_size, self.magnifier_size
        )
        
        if self.screen_pixmap:
            source_size = self.magnifier_size // self.magnifier_zoom
            source_rect = QRect(
                pos.x() - source_size // 2,
                pos.y() - source_size // 2,
                source_size,
                source_size
            )
            
            target_rect = QRect(
                magnifier_x, magnifier_y,
                self.magnifier_size, self.magnifier_size
            )
            
            painter.save()
            painter.setClipRect(target_rect)
            painter.drawPixmap(target_rect, self.screen_pixmap, source_rect)
            painter.restore()
        
        painter.setPen(QPen(QColor(255, 255, 255, 200), 1))
        painter.drawLine(
            magnifier_x + self.magnifier_size // 2 - 10,
            magnifier_y + self.magnifier_size // 2,
            magnifier_x + self.magnifier_size // 2 + 10,
            magnifier_y + self.magnifier_size // 2
        )
        painter.drawLine(
            magnifier_x + self.magnifier_size // 2,
            magnifier_y + self.magnifier_size // 2 - 10,
            magnifier_x + self.magnifier_size // 2,
            magnifier_y + self.magnifier_size // 2 + 10
        )
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.hint_label.hide()
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.is_selecting = True
            self.update()
    
    def mouseMoveEvent(self, event):
        if self.is_selecting:
            self.end_pos = event.pos()
            self.update()
        elif self.show_magnifier:
            self.update()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.is_selecting:
            self.is_selecting = False
            self.end_pos = event.pos()
            
            rect = QRect(self.start_pos, self.end_pos).normalized()
            if rect.width() > 10 and rect.height() > 10:
                self.selected_rect = rect
                self.is_active = False
                self.screenshot_taken.emit(rect)
            else:
                self.cancel()
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
    
    def cancel(self):
        self.is_active = False
        self.is_selecting = False
        self.start_pos = None
        self.end_pos = None
        self.selected_rect = None
        self.screen_pixmap = None
        self.hint_label.hide()
        self.hide()
        self.cancelled.emit()


class DrawingCanvas(QWidget):
    def __init__(self, parent=None, default_color: QColor = None, default_line_width: int = 2):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StaticContents)
        
        self.pixmap: Optional[QPixmap] = None
        self.original_pixmap: Optional[QPixmap] = None
        self.drawing = False
        self.current_tool = DrawingTool.RECT
        self.current_color = default_color if default_color else QColor('#FF0000')
        self.line_width = default_line_width
        
        self.start_pos = QPoint()
        self.end_pos = QPoint()
        
        self.history: List[QPixmap] =[]
        self.history_index = -1
        
        self.pen_points: List[QPoint] =[]
        
        self.setMouseTracking(True)
    
    def set_pixmap(self, pixmap: QPixmap):
        self.pixmap = pixmap.copy()
        self.original_pixmap = pixmap.copy()
        self.setFixedSize(pixmap.size())
        self.history = [self.pixmap.copy()]
        self.history_index = 0
        self.update()
    
    def get_original_pixmap(self) -> Optional[QPixmap]:
        return self.original_pixmap
    
    def get_final_pixmap(self) -> Optional[QPixmap]:
        return self.pixmap
    
    def save_state(self):
        if self.pixmap:
            self.history = self.history[:self.history_index + 1]
            self.history.append(self.pixmap.copy())
            self.history_index = len(self.history) - 1
    
    def undo(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.pixmap = self.history[self.history_index].copy()
            self.update()
    
    def redo(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.pixmap = self.history[self.history_index].copy()
            self.update()
    
    def paintEvent(self, event):
        painter = QPainter(self)
        if self.pixmap:
            painter.drawPixmap(0, 0, self.pixmap)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drawing = True
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            
            if self.current_tool == DrawingTool.PEN:
                self.pen_points = [event.pos()]
            elif self.current_tool == DrawingTool.TEXT:
                self.draw_text(event.pos())
                self.drawing = False
    
    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_pos = event.pos()
            
            if self.current_tool == DrawingTool.PEN:
                self.pen_points.append(event.pos())
                self.draw_pen_stroke()
            else:
                self.draw_preview()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.drawing = False
            self.end_pos = event.pos()
            
            if self.current_tool != DrawingTool.PEN:
                self.draw_shape()
            
            self.save_state()
    
    def draw_preview(self):
        if not self.pixmap:
            return
        
        temp_pixmap = self.history[self.history_index].copy() if self.history_index >= 0 else self.pixmap
        painter = QPainter(temp_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        self.setup_painter(painter)
        self.draw_shape_on_painter(painter, self.start_pos, self.end_pos)
        
        self.pixmap = temp_pixmap
        self.update()
    
    def draw_shape(self):
        if not self.pixmap:
            return
        
        painter = QPainter(self.pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        self.setup_painter(painter)
        self.draw_shape_on_painter(painter, self.start_pos, self.end_pos)
        
        self.update()
    
    def draw_shape_on_painter(self, painter: QPainter, start: QPoint, end: QPoint):
        rect = QRect(start, end).normalized()
        
        if self.current_tool == DrawingTool.RECT:
            painter.drawRect(rect)
        elif self.current_tool == DrawingTool.ELLIPSE:
            painter.drawEllipse(rect)
        elif self.current_tool == DrawingTool.LINE:
            painter.drawLine(start, end)
        elif self.current_tool == DrawingTool.DASHED:
            self.draw_dashed_line(painter, start, end)
        elif self.current_tool == DrawingTool.ARROW:
            self.draw_arrow(painter, start, end)
        elif self.current_tool == DrawingTool.MOSAIC:
            self.draw_mosaic(painter, rect)
    
    def draw_dashed_line(self, painter: QPainter, start: QPoint, end: QPoint):
        pen = QPen(self.current_color, self.line_width, Qt.DashLine)
        painter.setPen(pen)
        painter.drawLine(start, end)
    
    def draw_arrow(self, painter: QPainter, start: QPoint, end: QPoint):
        painter.drawLine(start, end)
        
        dx = end.x() - start.x()
        dy = end.y() - start.y()
        length = math.sqrt(dx * dx + dy * dy)
        
        if length == 0:
            return
        
        angle = math.atan2(dy, dx)
        arrow_size = 15
        
        p1 = QPoint(
            int(end.x() - arrow_size * math.cos(angle - math.pi / 6)),
            int(end.y() - arrow_size * math.sin(angle - math.pi / 6))
        )
        p2 = QPoint(
            int(end.x() - arrow_size * math.cos(angle + math.pi / 6)),
            int(end.y() - arrow_size * math.sin(angle + math.pi / 6))
        )
        
        painter.setBrush(QBrush(self.current_color))
        painter.drawPolygon(QPolygon([end, p1, p2]))
    
    def draw_mosaic(self, painter: QPainter, rect: QRect):
        if not self.pixmap:
            return
        
        block_size = 10
        for x in range(rect.left(), rect.right(), block_size):
            for y in range(rect.top(), rect.bottom(), block_size):
                colors = [QColor('#333'), QColor('#666'), QColor('#999'), QColor('#ccc')]
                color = random.choice(colors)
                painter.fillRect(x, y, block_size, block_size, color)
    
    def draw_smart_mosaic(self, sensitive_areas: List[Dict]):
        if not self.pixmap or not sensitive_areas:
            return
        
        painter = QPainter(self.pixmap)
        
        for area in sensitive_areas:
            rect = area.get('rect')
            if rect:
                self.draw_mosaic(painter, rect)
        
        self.save_state()
        self.update()
    
    def apply_smart_mosaic_to_text(self, ocr_results: List[Dict], sensitive_types: List[str] = None):
        if not self.pixmap or not ocr_results:
            return []
        
        if sensitive_types is None:
            sensitive_types = ['phone', 'id_card', 'bank_card', 'email', 'ip_address']
        
        sensitive_areas = []
        
        for result in ocr_results:
            text = result.get('text', '')
            detected = SensitiveDataDetector.detect_all(text)
            
            for item in detected:
                if item['type'] in sensitive_types:
                    sensitive_areas.append({
                        'type': item['type'],
                        'label': item['label'],
                        'value': item['value'],
                        'rect': result.get('rect')
                    })
        
        if sensitive_areas:
            self.draw_smart_mosaic(sensitive_areas)
        
        return sensitive_areas
    
    def draw_pen_stroke(self):
        if len(self.pen_points) < 2:
            return
        
        if not self.pixmap:
            return
        
        temp_pixmap = self.history[self.history_index].copy() if self.history_index >= 0 else self.pixmap
        painter = QPainter(temp_pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        
        pen = QPen(self.current_color, self.line_width, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
        painter.setPen(pen)
        
        for i in range(1, len(self.pen_points)):
            painter.drawLine(self.pen_points[i-1], self.pen_points[i])
        
        self.pixmap = temp_pixmap
        self.update()
    
    def draw_text(self, pos: QPoint):
        text, ok = QInputDialog.getText(self, 'Input Text', 'Enter text:')
        
        if ok and text and self.pixmap:
            painter = QPainter(self.pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            
            font = QFont('Arial', 16)
            painter.setFont(font)
            painter.setPen(self.current_color)
            painter.drawText(pos, text)
            
            self.save_state()
            self.update()
    
    def setup_painter(self, painter: QPainter):
        pen = QPen(self.current_color, self.line_width)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)


class EditorWindow(QMainWindow):
    finished = pyqtSignal()
    
    def __init__(self, config: Config, history_manager: HistoryManager):
        super().__init__()
        self.config = config
        self.history_manager = history_manager
        
        self.setWindowTitle('Screenshot Editor')
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        self.original_pixmap: Optional[QPixmap] = None
        self.selected_rect: Optional[QRect] = None
        
        self.init_ui()
    
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        default_color = QColor(self.config.get('default_color', '#FF0000'))
        default_line_width = self.config.get('default_line_width', 2)
        self.canvas = DrawingCanvas(self, default_color, default_line_width)
        self.canvas.setStyleSheet('background-color: #f0f0f0;')
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(self.canvas)
        scroll_area.setWidgetResizable(False)
        scroll_area.setAlignment(Qt.AlignCenter)
        scroll_area.setStyleSheet('QScrollArea { border: none; background-color: #e0e0e0; }')
        main_layout.addWidget(scroll_area, 1)
        
        self.toolbar = QFrame()
        self.toolbar.setStyleSheet('''
            QFrame {
                background-color: #ffffff;
                border-top: 1px solid #ddd;
                padding: 8px;
            }
            QPushButton {
                min-width: 32px;
                min-height: 32px;
                border: none;
                border-radius: 4px;
                background: transparent;
                font-size: 14px;
                font-weight: bold;
                padding: 4px 8px;
            }
            QPushButton:hover {
                background: #e0e0e0;
            }
            QPushButton:checked {
                background: #00a8ff;
                color: white;
            }
            QSlider::groove:horizontal {
                height: 6px;
                background: #e0e0e0;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                width: 14px;
                height: 14px;
                background: #00a8ff;
                border-radius: 7px;
                margin: -4px 0;
            }
        ''')
        
        toolbar_layout = QVBoxLayout(self.toolbar)
        toolbar_layout.setSpacing(6)
        toolbar_layout.setContentsMargins(10, 8, 10, 8)
        
        tools_row = QHBoxLayout()
        tools_row.setSpacing(2)
        
        self.tool_buttons = []
        tools = [
            (DrawingTool.RECT, 'Rect', 'Rectangle'),
            (DrawingTool.ELLIPSE, 'Oval', 'Ellipse'),
            (DrawingTool.ARROW, 'Arrow', 'Arrow'),
            (DrawingTool.LINE, 'Line', 'Line'),
            (DrawingTool.DASHED, 'Dash', 'Dashed Line'),
            (DrawingTool.PEN, 'Pen', 'Freehand'),
            (DrawingTool.TEXT, 'Text', 'Text'),
            (DrawingTool.MOSAIC, 'Mosaic', 'Mosaic'),
        ]
        
        for tool, icon, tooltip in tools:
            btn = QPushButton(icon, self.toolbar)
            btn.setToolTip(tooltip)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, t=tool: self.select_tool(t))
            tools_row.addWidget(btn)
            self.tool_buttons.append((tool, btn))
        
        tools_row.addSpacing(10)
        
        self.btn_ocr = QPushButton('OCR', self.toolbar)
        self.btn_ocr.setToolTip('Extract Text (OCR)')
        self.btn_ocr.setStyleSheet('''
            QPushButton {
                background: #9c27b0;
                color: white;
            }
            QPushButton:hover {
                background: #7b1fa2;
            }
        ''')
        self.btn_ocr.clicked.connect(self.do_ocr)
        tools_row.addWidget(self.btn_ocr)
        
        self.btn_smart_mosaic = QPushButton('Smart Mosaic', self.toolbar)
        self.btn_smart_mosaic.setToolTip('Auto-detect and mosaic sensitive data')
        self.btn_smart_mosaic.setStyleSheet('''
            QPushButton {
                background: #ff5722;
                color: white;
            }
            QPushButton:hover {
                background: #e64a19;
            }
        ''')
        self.btn_smart_mosaic.clicked.connect(self.do_smart_mosaic)
        tools_row.addWidget(self.btn_smart_mosaic)
        
        self.select_tool(DrawingTool.RECT)
        tools_row.addStretch()
        toolbar_layout.addLayout(tools_row)
        
        style_row = QHBoxLayout()
        style_row.setSpacing(10)
        
        style_row.addWidget(QLabel('Color:'))
        self.color_btn = QPushButton('●', self.toolbar)
        self.color_btn.setFixedSize(32, 32)
        self.color_btn.setStyleSheet(f'color: {self.config.get("default_color")}; font-size: 18px;')
        self.color_btn.clicked.connect(self.choose_color)
        style_row.addWidget(self.color_btn)
        
        style_row.addSpacing(8)
        
        style_row.addWidget(QLabel('Width:'))
        self.width_slider = QSlider(Qt.Horizontal, self.toolbar)
        self.width_slider.setMinimum(1)
        self.width_slider.setMaximum(10)
        self.width_slider.setValue(self.config.get('default_line_width', 2))
        self.width_slider.setFixedWidth(80)
        self.width_slider.valueChanged.connect(self.on_width_changed)
        style_row.addWidget(self.width_slider)
        
        self.width_label = QLabel(str(self.width_slider.value()))
        self.width_label.setFixedWidth(16)
        style_row.addWidget(self.width_label)
        
        style_row.addStretch()
        
        self.btn_undo = QPushButton('Undo', self.toolbar)
        self.btn_undo.setToolTip('Undo (Ctrl+Z)')
        self.btn_undo.clicked.connect(self.canvas.undo)
        style_row.addWidget(self.btn_undo)
        
        self.btn_redo = QPushButton('Redo', self.toolbar)
        self.btn_redo.setToolTip('Redo (Ctrl+Y)')
        self.btn_redo.clicked.connect(self.canvas.redo)
        style_row.addWidget(self.btn_redo)
        
        toolbar_layout.addLayout(style_row)
        
        action_row = QHBoxLayout()
        action_row.addStretch()
        
        self.btn_save = QPushButton('Save', self.toolbar)
        self.btn_save.setToolTip('Save to file (Ctrl+S)')
        self.btn_save.setStyleSheet('''
            QPushButton {
                background: #2196F3;
                color: white;
                min-width: 70px;
            }
            QPushButton:hover {
                background: #1976D2;
            }
        ''')
        self.btn_save.clicked.connect(self.save_to_file)
        action_row.addWidget(self.btn_save)
        
        self.btn_copy = QPushButton('Copy', self.toolbar)
        self.btn_copy.setToolTip('Copy to clipboard (Enter)')
        self.btn_copy.setStyleSheet('''
            QPushButton {
                background: #4CAF50;
                color: white;
                min-width: 70px;
            }
            QPushButton:hover {
                background: #388E3C;
            }
        ''')
        self.btn_copy.clicked.connect(self.copy_to_clipboard)
        action_row.addWidget(self.btn_copy)
        
        self.btn_close = QPushButton('Close', self.toolbar)
        self.btn_close.setToolTip('Close window (ESC)')
        self.btn_close.setStyleSheet('''
            QPushButton {
                background: #f44336;
                color: white;
                min-width: 70px;
            }
            QPushButton:hover {
                background: #d32f2f;
            }
        ''')
        self.btn_close.clicked.connect(self.close)
        action_row.addWidget(self.btn_close)
        
        toolbar_layout.addLayout(action_row)
        
        main_layout.addWidget(self.toolbar)
        
        shortcut_undo = QShortcut(QKeySequence('Ctrl+Z'), self)
        shortcut_undo.activated.connect(self.canvas.undo)
        
        shortcut_redo = QShortcut(QKeySequence('Ctrl+Y'), self)
        shortcut_redo.activated.connect(self.canvas.redo)
        
        shortcut_s = QShortcut(QKeySequence('Ctrl+S'), self)
        shortcut_s.activated.connect(self.save_to_file)
        
        shortcut_esc = QShortcut(QKeySequence('Escape'), self)
        shortcut_esc.activated.connect(self.close)
        
        shortcut_enter = QShortcut(QKeySequence('Return'), self)
        shortcut_enter.activated.connect(self.copy_to_clipboard)
    
    def select_tool(self, tool: str):
        self.canvas.current_tool = tool
        for t, btn in self.tool_buttons:
            btn.setChecked(t == tool)
    
    def choose_color(self):
        color = QColorDialog.getColor(
            QColor(self.config.get('default_color')),
            self,
            'Select Color'
        )
        if color.isValid():
            self.canvas.current_color = color
            self.color_btn.setStyleSheet(f'color: {color.name()}; font-size: 18px;')
            self.config.set('default_color', color.name())
    
    def on_width_changed(self, value):
        self.canvas.line_width = value
        self.width_label.setText(str(value))
    
    def set_screenshot(self, pixmap: QPixmap, rect: QRect):
        self.original_pixmap = pixmap
        self.selected_rect = rect
        
        cropped = pixmap.copy(rect)
        self.canvas.set_pixmap(cropped)
        
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        
        max_width = min(cropped.width() + 40, screen_geometry.width() - 100)
        max_height = min(cropped.height() + 150, screen_geometry.height() - 100)
        
        self.resize(max_width, max_height)
        
        center_x = screen_geometry.x() + (screen_geometry.width() - self.width()) // 2
        center_y = screen_geometry.y() + (screen_geometry.height() - self.height()) // 2
        self.move(center_x, center_y)
        
        self.show()
        self.setFocus()
        self.activateWindow()
        self.raise_()
    
    def save_to_file(self):
        final = self.canvas.get_final_pixmap()
        if not final:
            return
        
        default_dir = self.config.get('save_path')
        Path(default_dir).mkdir(parents=True, exist_ok=True)
        
        fmt = self.config.get('default_format', 'PNG').lower()
        filename = f"Screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt}"
        default_path = str(Path(default_dir) / filename)
        
        path, _ = QFileDialog.getSaveFileName(
            self, 'Save Screenshot', default_path,
            'PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)'
        )
        
        if path:
            if not path.lower().endswith(('.png', '.jpg', '.jpeg')):
                path += f'.{fmt}'
            save_fmt = 'PNG' if path.lower().endswith('.png') else 'JPEG'
            final.save(path, save_fmt)
            self.history_manager.add(path)
            print(f'Screenshot saved: {path}')
            self.statusBar().showMessage(f'Saved: {path}', 3000)
    
    def copy_to_clipboard(self):
        final = self.canvas.get_final_pixmap()
        if final:
            QApplication.clipboard().setPixmap(final)
            print('Screenshot copied to clipboard')
            self.statusBar().showMessage('Copied to clipboard!', 2000)
    
    def do_ocr(self):
        if not OCRManager.is_available():
            if not OCRManager.check_models_exist():
                reply = QMessageBox.question(
                    self, 'OCR Models Not Found',
                    'OCR models need to be downloaded (~80MB).\n'
                    'Would you like to download them now?\n\n'
                    'Alternatively, you can run:\n'
                    'pip install paddlepaddle paddleocr',
                    QMessageBox.Yes | QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            
            self.statusBar().showMessage('Loading OCR engine...')
            self.btn_ocr.setEnabled(False)
            
            def on_ocr_loaded(success, error_msg=None):
                self.btn_ocr.setEnabled(True)
                if success:
                    self.statusBar().showMessage('OCR engine loaded!', 2000)
                    self._perform_ocr()
                else:
                    self.statusBar().showMessage(f'OCR load failed: {error_msg}', 5000)
                    QMessageBox.warning(self, 'OCR Error', f'Failed to load OCR:\n{error_msg}')
            
            OCRManager.initialize(callback=on_ocr_loaded)
        else:
            self._perform_ocr()
    
    def _perform_ocr(self):
        if not OCRManager.is_available():
            return
        
        self.statusBar().showMessage('Performing OCR...')
        QApplication.processEvents()
        
        ocr_results = OCRManager.recognize(self.canvas.pixmap)
        
        if ocr_results:
            all_text = '\n'.join([r['text'] for r in ocr_results])
            
            dialog = OCRResultDialog(all_text, ocr_results, self)
            if dialog.exec_() == QDialog.Accepted:
                selected_text = dialog.get_selected_text()
                if selected_text:
                    QApplication.clipboard().setText(selected_text)
                    self.statusBar().showMessage(f'Copied {len(selected_text)} characters!', 2000)
        else:
            self.statusBar().showMessage('No text detected', 2000)
    
    def do_smart_mosaic(self):
        if not OCRManager.is_available():
            reply = QMessageBox.question(
                self, 'OCR Required',
                'Smart Mosaic requires OCR to detect text.\n'
                'Would you like to load OCR engine now?',
                QMessageBox.Yes | QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return
            
            self.statusBar().showMessage('Loading OCR engine...')
            self.btn_smart_mosaic.setEnabled(False)
            
            def on_ocr_loaded(success, error_msg=None):
                self.btn_smart_mosaic.setEnabled(True)
                if success:
                    self.statusBar().showMessage('OCR engine loaded!', 2000)
                    self._perform_smart_mosaic()
                else:
                    self.statusBar().showMessage(f'OCR load failed: {error_msg}', 5000)
            
            OCRManager.initialize(callback=on_ocr_loaded)
        else:
            self._perform_smart_mosaic()
    
    def _perform_smart_mosaic(self):
        if not OCRManager.is_available():
            return
        
        self.statusBar().showMessage('Detecting sensitive data...')
        QApplication.processEvents()
        
        ocr_results = OCRManager.recognize(self.canvas.pixmap)
        
        if not ocr_results:
            self.statusBar().showMessage('No text detected', 2000)
            return
        
        sensitive_areas = self.canvas.apply_smart_mosaic_to_text(ocr_results)
        
        if sensitive_areas:
            summary = '\n'.join([f"• {area['label']}: {area['value'][:3]}***" for area in sensitive_areas])
            self.statusBar().showMessage(f'Mosaiced {len(sensitive_areas)} sensitive items', 3000)
            QMessageBox.information(
                self, 'Smart Mosaic Applied',
                f'Applied mosaic to {len(sensitive_areas)} sensitive items:\n\n{summary}'
            )
        else:
            self.statusBar().showMessage('No sensitive data detected', 2000)
    
    def closeEvent(self, event):
        self.finished.emit()
        event.accept()


class OCRResultDialog(QDialog):
    def __init__(self, text: str, ocr_results: List[Dict], parent=None):
        super().__init__(parent)
        self.setWindowTitle('OCR Results')
        self.setMinimumSize(500, 400)
        self.ocr_results = ocr_results
        self.selected_text = text
        
        self.init_ui(text)
    
    def init_ui(self, text: str):
        layout = QVBoxLayout(self)
        
        label = QLabel('Detected Text (click to select):')
        layout.addWidget(label)
        
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(text)
        self.text_edit.setReadOnly(True)
        self.text_edit.selectAll()
        layout.addWidget(self.text_edit)
        
        info_label = QLabel(f'Detected {len(self.ocr_results)} text regions')
        info_label.setStyleSheet('color: #666; font-size: 12px;')
        layout.addWidget(info_label)
        
        btn_layout = QHBoxLayout()
        
        btn_copy_all = QPushButton('Copy All')
        btn_copy_all.clicked.connect(self.copy_all)
        btn_layout.addWidget(btn_copy_all)
        
        btn_copy_selected = QPushButton('Copy Selected')
        btn_copy_selected.clicked.connect(self.copy_selected)
        btn_layout.addWidget(btn_copy_selected)
        
        btn_layout.addStretch()
        
        btn_close = QPushButton('Close')
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        
        layout.addLayout(btn_layout)
    
    def copy_all(self):
        QApplication.clipboard().setText(self.text_edit.toPlainText())
        self.accept()
    
    def copy_selected(self):
        cursor = self.text_edit.textCursor()
        selected = cursor.selectedText()
        if selected:
            self.selected_text = selected
        self.accept()
    
    def get_selected_text(self) -> str:
        return self.selected_text


# Custom QLineEdit that allows user to bind shortcuts
class HotkeyLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setToolTip('Press your desired key combination here.\nPress Backspace to clear.')
    
    def keyPressEvent(self, event):
        key = event.key()
        modifiers = event.modifiers()
        
        # Ignore lonely modifier keys
        if key in (Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta):
            return
            
        if key in (Qt.Key_Backspace, Qt.Key_Delete):
            self.setText('')
            return
            
        parts =[]
        if modifiers & Qt.ControlModifier:
            parts.append('ctrl')
        if modifiers & Qt.ShiftModifier:
            parts.append('shift')
        if modifiers & Qt.AltModifier:
            parts.append('alt')
            
        if Qt.Key_A <= key <= Qt.Key_Z:
            parts.append(chr(key).lower())
        elif Qt.Key_0 <= key <= Qt.Key_9:
            parts.append(chr(key))
        elif Qt.Key_F1 <= key <= Qt.Key_F12:
            parts.append(f'f{key - Qt.Key_F1 + 1}')
        else:
            return
            
        self.setText('+'.join(parts))

class SettingsDialog(QDialog):
    def __init__(self, config: Config, auto_start_manager: AutoStartManager = None, parent=None):
        super().__init__(parent)
        self.config = config
        self.auto_start_manager = auto_start_manager
        self.setWindowTitle('Settings')
        self.setFixedSize(450, 400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        
        shortcut_group = QGroupBox('Hotkey Settings')
        shortcut_layout = QHBoxLayout(shortcut_group)
        
        shortcut_layout.addWidget(QLabel('Screenshot Hotkey:'))
        self.shortcut_edit = HotkeyLineEdit()
        self.shortcut_edit.setText(self.config.get('shortcut'))
        shortcut_layout.addWidget(self.shortcut_edit)
        
        layout.addWidget(shortcut_group)
        
        save_group = QGroupBox('Save Settings')
        save_layout = QGridLayout(save_group)
        
        save_layout.addWidget(QLabel('Default Save Path:'), 0, 0)
        self.path_edit = QLineEdit()
        self.path_edit.setText(self.config.get('save_path'))
        self.path_edit.setReadOnly(True)
        save_layout.addWidget(self.path_edit, 0, 1)
        
        self.browse_btn = QPushButton('Browse...')
        self.browse_btn.clicked.connect(self.browse_folder)
        save_layout.addWidget(self.browse_btn, 0, 2)
        
        save_layout.addWidget(QLabel('Default Format:'), 1, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(['PNG', 'JPG'])
        self.format_combo.setCurrentText(self.config.get('default_format'))
        save_layout.addWidget(self.format_combo, 1, 1)
        
        layout.addWidget(save_group)
        
        other_group = QGroupBox('Other Settings')
        other_layout = QVBoxLayout(other_group)
        
        self.magnifier_check = QCheckBox('Show Magnifier')
        self.magnifier_check.setChecked(self.config.get('show_magnifier'))
        other_layout.addWidget(self.magnifier_check)
        
        self.auto_start_check = QCheckBox('Launch at Startup')
        if self.auto_start_manager:
            self.auto_start_check.setChecked(self.auto_start_manager.is_enabled())
        else:
            self.auto_start_check.setChecked(False)
        other_layout.addWidget(self.auto_start_check)
        
        layout.addWidget(other_group)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        save_btn = QPushButton('Save')
        save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton('Cancel')
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, 'Select Save Folder')
        if folder:
            self.path_edit.setText(folder)
    
    def save_settings(self):
        self.config.set('shortcut', self.shortcut_edit.text())
        self.config.set('save_path', self.path_edit.text())
        self.config.set('default_format', self.format_combo.currentText())
        self.config.set('show_magnifier', self.magnifier_check.isChecked())
        self.config.set('auto_start', self.auto_start_check.isChecked())
        
        if self.auto_start_manager:
            if self.auto_start_check.isChecked():
                self.auto_start_manager.enable()
            else:
                self.auto_start_manager.disable()
        
        self.accept()


class HistoryWindow(QDialog):
    def __init__(self, history_manager: HistoryManager, parent=None):
        super().__init__(parent)
        self.history_manager = history_manager
        self.setWindowTitle('Screenshot History')
        self.setMinimumSize(800, 600)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        toolbar = QHBoxLayout()
        
        clear_btn = QPushButton('Clear All')
        clear_btn.clicked.connect(self.clear_history)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        
        self.list_widget = QListWidget()
        self.list_widget.setViewMode(QListWidget.IconMode)
        self.list_widget.setIconSize(QSize(200, 150))
        self.list_widget.setResizeMode(QListWidget.Adjust)
        self.list_widget.setSpacing(10)
        
        scroll.setWidget(self.list_widget)
        layout.addWidget(scroll)
        
        self.load_history()
    
    def load_history(self):
        self.list_widget.clear()
        
        for item in self.history_manager.history:
            list_item = QListWidgetItem()
            
            if item.get('path') and os.path.exists(item['path']):
                pixmap = QPixmap(item['path'])
                icon = QIcon(pixmap)
                list_item.setIcon(icon)
            
            timestamp = datetime.fromisoformat(item['timestamp'])
            list_item.setText(timestamp.strftime('%Y-%m-%d %H:%M:%S'))
            list_item.setData(Qt.UserRole, item['id'])
            list_item.setData(Qt.UserRole + 1, item.get('path'))
            
            self.list_widget.addItem(list_item)
        
        self.list_widget.itemDoubleClicked.connect(self.open_item)
    
    def open_item(self, item):
        path = item.data(Qt.UserRole + 1)
        if path and os.path.exists(path):
            os.startfile(path)
    
    def clear_history(self):
        reply = QMessageBox.question(
            self, 'Confirm',
            'Clear all history? This will delete all saved screenshots.',
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.history_manager.clear()
            self.load_history()


class HiddenWindow(QWidget):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setFixedSize(1, 1)
        self.move(-100, -100)
    
    def nativeEvent(self, eventType, message):
        if sys.platform == 'win32':
            if eventType == b'windows_generic_MSG':
                try:
                    msg = ctypes.wintypes.MSG.from_address(int(message))
                    if msg.message == WM_HOTKEY:
                        self.callback()
                        return True, 0
                except Exception:
                    pass
        return super().nativeEvent(eventType, message)


class ScreenshotApp:
    HOTKEY_ID = 1
    
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        
        self.config = Config()
        self.history_manager = HistoryManager(self.config)
        self.auto_start_manager = AutoStartManager()
        
        self.hidden_window = None
        self.overlay = ScreenshotOverlay(self.config)
        self.editor: Optional[EditorWindow] = None
        
        self.current_hotkey = None
        self.is_screenshot_in_progress = False
        
        self.setup_tray()
        self.setup_hotkey()
        self.setup_overlay_signals()
        self.sync_auto_start_state()
    
    def setup_tray(self):
        self.tray_icon = QSystemTrayIcon()
        
        icon_path = Path(__file__).parent / 'tray-icon.png'
        if icon_path.exists():
            self.tray_icon.setIcon(QIcon(str(icon_path)))
        else:
            self.tray_icon.setIcon(self.create_default_icon())
        
        menu = QMenu()
        
        screenshot_action = QAction('Screenshot', self.app)
        screenshot_action.triggered.connect(self.start_screenshot)
        menu.addAction(screenshot_action)
        
        history_action = QAction('History', self.app)
        history_action.triggered.connect(self.show_history)
        menu.addAction(history_action)
        
        menu.addSeparator()
        
        settings_action = QAction('Settings', self.app)
        settings_action.triggered.connect(self.show_settings)
        menu.addAction(settings_action)
        
        menu.addSeparator()
        
        quit_action = QAction('Quit', self.app)
        quit_action.triggered.connect(self.quit_app)
        menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.setToolTip('Screenshot Tool')
        self.tray_icon.show()
        
        shortcut_title = self.config.get('shortcut').title()
        self.tray_icon.showMessage(
            'Screenshot Tool',
            f'Press {shortcut_title} to take a screenshot',
            QSystemTrayIcon.Information,
            3000
        )
    
    def create_default_icon(self):
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
    
    def setup_hotkey(self):
        if sys.platform != 'win32':
            print('Hotkey only supported on Windows')
            return
        
        shortcut_str = self.config.get('shortcut')
        self.current_hotkey = shortcut_str
        
        try:
            mods, vk = self.parse_hotkey(shortcut_str)
            
            self.hidden_window = HiddenWindow(self.start_screenshot)
            self.hidden_window.show()
            
            hwnd = int(self.hidden_window.winId())
            
            if not user32.RegisterHotKey(hwnd, self.HOTKEY_ID, mods | MOD_NOREPEAT, vk):
                error = ctypes.get_last_error()
                print(f'Failed to register hotkey: {shortcut_str} (error: {error})')
                self.tray_icon.showMessage(
                    'Hotkey Error',
                    f'Failed to register hotkey: {shortcut_str}\nThe hotkey may be in use by another application.',
                    QSystemTrayIcon.Warning,
                    5000
                )
                return
            
            print(f'Hotkey registered: {shortcut_str}')
            
        except Exception as e:
            print(f'Failed to register hotkey: {e}')
    
    def parse_hotkey(self, shortcut: str):
        parts = shortcut.lower().replace(' ', '').split('+')
        
        mods = 0
        vk = 0
        
        key_map = {
            'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
            'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
            'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
            'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
            'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59,
            'z': 0x5A,
            '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
            '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
            'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
            'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
            'f11': 0x7A, 'f12': 0x7B,
        }
        
        for part in parts:
            if part == 'ctrl':
                mods |= MOD_CONTROL
            elif part == 'shift':
                mods |= MOD_SHIFT
            elif part == 'alt':
                mods |= MOD_ALT
            elif part in key_map:
                vk = key_map[part]
        
        return mods, vk
    
    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.start_screenshot()
    
    def setup_overlay_signals(self):
        self.overlay.screenshot_taken.connect(self.on_screenshot_taken)
        self.overlay.cancelled.connect(self.on_screenshot_cancelled)
    
    def start_screenshot(self):
        if self.is_screenshot_in_progress:
            print('Screenshot already in progress, ignoring hotkey...')
            return
        
        print('Starting screenshot...')
        self.is_screenshot_in_progress = True
        self.overlay.start_screenshot()
    
    def on_screenshot_taken(self, rect: QRect):
        self.overlay.hide()
        
        screen = QApplication.primaryScreen()
        pixmap = screen.grabWindow(0)
        
        self.editor = EditorWindow(self.config, self.history_manager)
        self.editor.finished.connect(self.on_editor_finished)
        self.editor.set_screenshot(pixmap, rect)
    
    def on_screenshot_cancelled(self):
        print('Screenshot cancelled by user')
        self.is_screenshot_in_progress = False
    
    def on_editor_finished(self):
        print('Screenshot process completed')
        self.is_screenshot_in_progress = False
    
    def sync_auto_start_state(self):
        config_auto_start = self.config.get('auto_start', False)
        actual_auto_start = self.auto_start_manager.is_enabled()
        
        if config_auto_start and not actual_auto_start:
            self.auto_start_manager.enable()
        elif not config_auto_start and actual_auto_start:
            self.auto_start_manager.disable()
    
    def show_settings(self):
        dialog = SettingsDialog(self.config, self.auto_start_manager)
        if dialog.exec_() == QDialog.Accepted:
            new_shortcut = self.config.get('shortcut')
            if new_shortcut != self.current_hotkey:
                if self.hidden_window:
                    hwnd = int(self.hidden_window.winId())
                    user32.UnregisterHotKey(hwnd, self.HOTKEY_ID)
                self.setup_hotkey()
    
    def show_history(self):
        window = HistoryWindow(self.history_manager)
        window.exec_()
    
    def quit_app(self):
        if sys.platform == 'win32' and self.hidden_window:
            hwnd = int(self.hidden_window.winId())
            user32.UnregisterHotKey(hwnd, self.HOTKEY_ID)
        self.app.quit()
    
    def run(self):
        return self.app.exec_()


def main():
    # Enable High DPI Scaling (Fixes cropped screenshots on high resolution monitors)
    if hasattr(Qt, 'AA_EnableHighDpiScaling'):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, 'AA_UseHighDpiPixmaps'):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
        
    app = ScreenshotApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()