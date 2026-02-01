import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import (Qt, QTimer, QPoint, QPointF, pyqtProperty, 
                          QEasingCurve, QPropertyAnimation, QRectF,
                          QParallelAnimationGroup, QEvent) # [新增] QEvent
from PyQt6.QtGui import QPainter, QColor, QPainterPath, QPen, QPolygonF, QMouseEvent

class FloatingBall(QWidget):
    def __init__(self):
        super().__init__()
        
        # --- 視窗設定 ---
        self.ball_radius = 30
        self.container_size = 500 
        
        # --- 物理參數 ---
        self.spring = 0.10   
        self.friction = 0.75    
        self.max_stretch = 0.40
        
        # --- 狀態變數 ---
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        
        self.last_global_pos = QPoint()
        self.is_dragging = False
        self.drag_start_pos = QPoint()
        self.window_start_pos = QPoint()
        self.edge_side = 'right'
        
        # [新增] 防止邏輯衝突的鎖 (點擊外部關閉時，避免 Icon 再次觸發打開)
        self.block_toggle = False
        
        # 自動收納
        self.is_collapsed = False
        self.collapse_timer = QTimer(self)
        self.collapse_timer.setSingleShot(True)
        self.collapse_timer.timeout.connect(self.collapse_to_edge)
        
        self.panel = None 
        
        # 物理引擎
        self.physics_timer = QTimer(self)
        self.physics_timer.timeout.connect(self.update_physics)
        self.physics_timer.start(16) 
        
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(self.container_size, self.container_size)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | 
            Qt.WindowType.WindowStaysOnTopHint | 
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.move(screen.width() - 350, screen.height() // 2)
        self.last_global_pos = self.pos()

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(300, self.snap_to_edge)
        self.collapse_timer.start(5000)

    # --- [新增] 事件過濾器：監聽聊天室是否失去焦點 ---
    def eventFilter(self, source, event):
        # 如果事件來源是聊天室面板
        if source == self.panel:
            # 如果事件類型是 "視窗失去焦點 (WindowDeactivate)"
            # 代表使用者點了聊天室以外的地方
            if event.type() == QEvent.Type.WindowDeactivate:
                if self.panel.isVisible():
                    self.panel.hide_panel()      # 關閉面板
                    self.collapse_timer.start(5000) # 重新開始倒數收納球
                    
                    # [關鍵邏輯] 上鎖 200ms
                    # 如果你是點擊 JellyBall 來關閉的，這個 Deactivate 會先觸發，
                    # 導致 JellyBall 的 mouseRelease 以為你要「打開」。
                    # 所以這裡我們先鎖住 toggle 功能 0.2 秒。
                    self.block_toggle = True
                    QTimer.singleShot(200, lambda: setattr(self, 'block_toggle', False))
                    
        return super().eventFilter(source, event)

    def update_physics(self):
        if self.is_collapsed: return

        force_x = -self.spring * self.offset_x
        force_y = -self.spring * self.offset_y
        
        self.velocity_x += force_x
        self.velocity_y += force_y
        
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction
        
        self.offset_x += self.velocity_x
        self.offset_y += self.velocity_y
        
        if abs(self.offset_x) < 0.05 and abs(self.offset_y) < 0.05 and \
           abs(self.velocity_x) < 0.05 and abs(self.velocity_y) < 0.05:
            self.offset_x = 0
            self.offset_y = 0
            self.velocity_x = 0
            self.velocity_y = 0
            
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        cx = self.width() / 2
        cy = self.height() / 2
        
        if self.is_collapsed:
            self.draw_arrow(painter, cx, cy)
        else:
            self.draw_jelly_ball(painter, cx, cy)

    def draw_jelly_ball(self, painter, cx, cy):
        ball_x = cx + self.offset_x
        ball_y = cy + self.offset_y
        
        dist = math.sqrt(self.offset_x**2 + self.offset_y**2)
        stretch_factor = 1.0 + min(dist * 0.02, self.max_stretch) 
        squash_factor = 1.0 / stretch_factor
        
        angle_rad = math.atan2(self.offset_y, self.offset_x)
        angle_deg = math.degrees(angle_rad)
        
        painter.save()
        painter.translate(ball_x, ball_y)
        painter.rotate(angle_deg)
        painter.scale(stretch_factor, squash_factor)
        
        path = QPainterPath()
        path.addEllipse(QPointF(0, 0), self.ball_radius, self.ball_radius)
        
        painter.fillPath(path, QColor(60, 120, 240, 240))
        
        pen = QPen(QColor(255, 255, 255, 180))
        avg_scale = (stretch_factor + squash_factor) / 2
        pen.setWidthF(2.0 / avg_scale)
        painter.setPen(pen)
        painter.drawEllipse(QPointF(0, 0), self.ball_radius, self.ball_radius)
        
        painter.setPen(QColor(255, 255, 255))
        font = painter.font()
        font.setPixelSize(20)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(QRectF(-self.ball_radius, -self.ball_radius, 
                                self.ball_radius*2, self.ball_radius*2),
                        Qt.AlignmentFlag.AlignCenter, "福")
        painter.restore()

    def draw_arrow(self, painter, cx, cy):
        painter.save()
        tab_width = 20
        tab_height = 50
        
        if self.edge_side == 'right':
            rect = QRectF(cx + 10, cy - tab_height/2, tab_width, tab_height)
            path = QPainterPath()
            path.addRoundedRect(rect, 10, 10)
            arrow_points = [QPointF(cx + 18, cy - 5), QPointF(cx + 13, cy), QPointF(cx + 18, cy + 5)]
        else:
            rect = QRectF(cx - 10 - tab_width, cy - tab_height/2, tab_width, tab_height)
            path = QPainterPath()
            path.addRoundedRect(rect, 10, 10)
            arrow_points = [QPointF(cx - 18, cy - 5), QPointF(cx - 13, cy), QPointF(cx - 18, cy + 5)]

        painter.fillPath(path, QColor(60, 120, 240, 200))
        pen = QPen(QColor(255, 255, 255, 200))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.drawPolyline(arrow_points)
        painter.restore()

    def collapse_to_edge(self):
        if self.panel and self.panel.isVisible():
            self.collapse_timer.stop()
            return

        self.is_collapsed = True
        self.update()
        if self.panel:
            self.panel.hide()

    def expand_from_edge(self):
        self.is_collapsed = False
        self.update()
        self.collapse_timer.start(5000)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_collapsed:
                self.expand_from_edge()
                return

            self.is_dragging = False
            self.drag_start_pos = event.globalPosition().toPoint()
            self.window_start_pos = self.pos()
            self.last_global_pos = self.pos()
            self.velocity_x = 0
            self.velocity_y = 0
            self.collapse_timer.stop()

    def mouseMoveEvent(self, event):
        if self.is_collapsed: return

        if event.buttons() == Qt.MouseButton.LeftButton:
            global_pos = event.globalPosition().toPoint()
            diff = global_pos - self.drag_start_pos
            
            if diff.manhattanLength() > 5:
                self.is_dragging = True
                new_pos = self.window_start_pos + diff
                self.move(new_pos)
                
                delta_x = new_pos.x() - self.last_global_pos.x()
                delta_y = new_pos.y() - self.last_global_pos.y()
                self.offset_x -= delta_x 
                self.offset_y -= delta_y 
                self.last_global_pos = new_pos
                
                if self.panel and self.panel.isVisible():
                    self.panel.hide_panel()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.is_dragging:
                self.is_dragging = False
                self.snap_to_edge()
                self.collapse_timer.start(5000)
            elif not self.is_collapsed:
                self.velocity_y = 8 
                self.toggle_panel()
            
            self.last_global_pos = self.pos()
            
            if not self.is_collapsed:
                if self.panel and self.panel.isVisible():
                    self.collapse_timer.stop()
                else:
                    self.collapse_timer.start(5000)

    def snap_to_edge(self):
        center_point = self.geometry().center()
        current_screen = QApplication.screenAt(center_point)
        if not current_screen:
            current_screen = QApplication.primaryScreen()
            
        screen_geo = current_screen.geometry()
        current_pos = self.pos()
        padding = (self.container_size - self.ball_radius*2) / 2
        
        dist_to_left = abs(current_pos.x() - screen_geo.left())
        dist_to_right = abs(current_pos.x() + self.width() - screen_geo.right())
        
        if dist_to_left < dist_to_right:
            target_x = screen_geo.left() - padding + 10
            self.edge_side = 'left'
        else:
            target_x = screen_geo.right() - self.width() + padding - 10
            self.edge_side = 'right'
            
        self.anim_move = QPropertyAnimation(self, b"pos")
        self.anim_move.setDuration(500) 
        self.anim_move.setStartValue(current_pos)
        self.anim_move.setEndValue(QPoint(int(target_x), current_pos.y()))
        self.anim_move.valueChanged.connect(self.on_animation_move)
        self.anim_move.setEasingCurve(QEasingCurve.Type.OutBack)
        self.anim_move.start()

    def on_animation_move(self, new_pos):
        if isinstance(new_pos, QPoint):
            delta_x = new_pos.x() - self.last_global_pos.x()
            delta_y = new_pos.y() - self.last_global_pos.y()
            self.offset_x -= delta_x 
            self.offset_y -= delta_y 
            self.last_global_pos = new_pos
            if self.panel and self.panel.isVisible():
                self.panel.hide_panel()

    # def toggle_panel(self):
    #     """ [功能修正] 點擊外部關閉 + 防止誤觸 """
        
    #     # [檢查] 是否因為點擊外部剛剛才關閉？如果是，這次點擊無效
    #     if self.block_toggle:
    #         return

    #     if not self.panel:
    #         try:
    #             from floating_panel import FloatingPanel
    #             self.panel = FloatingPanel(self)
    #             self.panel.setWindowFlags(
    #                 Qt.WindowType.Window | 
    #                 Qt.WindowType.FramelessWindowHint | 
    #                 Qt.WindowType.WindowStaysOnTopHint
    #             )
                
    #             # [新增] 安裝事件過濾器，讓 JellyBall 監聽 Panel 的狀態
    #             self.panel.installEventFilter(self)
                
    #         except ImportError:
    #             print("找不到 floating_panel.py")
    #             return
        
    #     # 關閉面板
    #     if self.panel.isVisible():
    #         self.panel.hide_panel()
    #         self.collapse_timer.start(5000)
    #         return

    #     # 開啟面板
    #     self.collapse_timer.stop()

    #     panel_width = self.panel.width() if self.panel.width() > 50 else 400
    #     panel_height = self.panel.height() if self.panel.height() > 50 else 600

    #     center_point = self.geometry().center()
    #     current_screen = QApplication.screenAt(center_point)
    #     if not current_screen:
    #         current_screen = QApplication.primaryScreen()
    #     screen_geo = current_screen.geometry()
        
    #     ball_center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        
    #     spacing = -20      
    #     vertical_shift = 150 
        
    #     screen_center_x = screen_geo.left() + screen_geo.width() / 2
        
    #     if ball_center.x() > screen_center_x:
    #         target_x = ball_center.x() - self.ball_radius - panel_width - spacing
    #     else:
    #         target_x = ball_center.x() + self.ball_radius + spacing
            
    #     target_y = ball_center.y() - (panel_height // 2) + vertical_shift
        
    #     end_rect = QRectF(target_x, target_y, panel_width, panel_height).toRect()
    #     start_rect = QRectF(ball_center.x(), ball_center.y(), 1, 1).toRect()

    #     self.panel.setWindowOpacity(0)
    #     self.panel.setGeometry(start_rect)
    #     self.panel.show() 
    #     self.panel.raise_() 

    #     self.anim_group = QParallelAnimationGroup()
        
    #     anim_geo = QPropertyAnimation(self.panel, b"geometry")
    #     anim_geo.setDuration(400)
    #     anim_geo.setStartValue(start_rect)
    #     anim_geo.setEndValue(end_rect)
    #     anim_geo.setEasingCurve(QEasingCurve.Type.OutBack)
        
    #     anim_fade = QPropertyAnimation(self.panel, b"windowOpacity")
    #     anim_fade.setDuration(300)
    #     anim_fade.setStartValue(0)
    #     anim_fade.setEndValue(1)
        
    #     self.anim_group.addAnimation(anim_geo)
    #     self.anim_group.addAnimation(anim_fade)
    #     self.anim_group.start()

    def toggle_panel(self):
        """ [智慧定位版] 自動判斷上下邊界，保證視窗完整顯示 """
        
        if self.block_toggle: return

        if not self.panel:
            try:
                from floating_panel import FloatingPanel
                self.panel = FloatingPanel(self)
                self.panel.setWindowFlags(
                    Qt.WindowType.Window | 
                    Qt.WindowType.FramelessWindowHint | 
                    Qt.WindowType.WindowStaysOnTopHint
                )
                self.panel.installEventFilter(self)
            except ImportError:
                print("找不到 floating_panel.py")
                return
        
        if self.panel.isVisible():
            self.panel.hide_panel()
            self.collapse_timer.start(5000)
            return

        self.collapse_timer.stop()

        # 1. 準備尺寸
        panel_width = self.panel.width() if self.panel.width() > 50 else 400
        panel_height = self.panel.height() if self.panel.height() > 50 else 600

        # 2. 獲取當前螢幕的「可用區域」 (Available Geometry 會扣除工作列 Taskbar)
        center_point = self.geometry().center()
        current_screen = QApplication.screenAt(center_point)
        if not current_screen:
            current_screen = QApplication.primaryScreen()
            
        screen_geo = current_screen.availableGeometry() # [重點] 改用 availableGeometry
        ball_center = self.mapToGlobal(QPoint(self.width() // 2, self.height() // 2))
        
        # --- [X 軸計算] 左右貼邊 ---
        spacing = -20 
        screen_center_x = screen_geo.left() + screen_geo.width() / 2
        
        if ball_center.x() > screen_center_x:
            # 球在右半邊 -> 面板顯示在左側
            target_x = ball_center.x() - self.ball_radius - panel_width - spacing
        else:
            # 球在左半邊 -> 面板顯示在右側
            target_x = ball_center.x() + self.ball_radius + spacing

        # --- [Y 軸計算] 智慧上下定位 ---
        
        # 預設偏好：球在面板上方約 120px 的位置 (讓使用者不用抬頭看訊息)
        preferred_offset_from_top = 120 
        ideal_y = ball_center.y() - preferred_offset_from_top
        
        # [智慧修正]
        # 1. 檢查底部：如果底部超出螢幕，就往上推
        if ideal_y + panel_height > screen_geo.bottom() - 10:
            # 讓面板底部剛好貼齊螢幕底部 (留 10px 邊距)
            target_y = screen_geo.bottom() - panel_height - 10
        # 2. 檢查頂部：如果頂部超出螢幕，就往下推 (優先級較低，所以寫在後面)
        elif ideal_y < screen_geo.top() + 10:
            # 讓面板頂部剛好貼齊螢幕頂部
            target_y = screen_geo.top() + 10
        else:
            # 如果都在範圍內，就用預設的理想位置
            target_y = ideal_y

        # --- 動畫設定 ---
        end_rect = QRectF(target_x, target_y, panel_width, panel_height).toRect()
        # 起點：球的中心，從一個點長出來
        start_rect = QRectF(ball_center.x(), ball_center.y(), 1, 1).toRect()

        # 設定透明度與初始位置 (防殘影)
        self.panel.setWindowOpacity(0)
        self.panel.setGeometry(start_rect)
        self.panel.show() 
        self.panel.raise_() 

        # 執行並行動畫
        self.anim_group = QParallelAnimationGroup()
        
        anim_geo = QPropertyAnimation(self.panel, b"geometry")
        anim_geo.setDuration(400)
        anim_geo.setStartValue(start_rect)
        anim_geo.setEndValue(end_rect)
        anim_geo.setEasingCurve(QEasingCurve.Type.OutBack)
        
        anim_fade = QPropertyAnimation(self.panel, b"windowOpacity")
        anim_fade.setDuration(250)
        anim_fade.setStartValue(0)
        anim_fade.setEndValue(1)
        
        self.anim_group.addAnimation(anim_geo)
        self.anim_group.addAnimation(anim_fade)
        self.anim_group.start()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = FloatingBall()
    window.show()
    sys.exit(app.exec())