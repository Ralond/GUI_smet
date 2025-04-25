from PyQt5.QtWidgets import (QGraphicsRectItem, QGraphicsTextItem, QMenu)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QBrush, QColor

class DraggableItem(QGraphicsRectItem):
    def __init__(self, title, item_type, parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.setRect(0, 0, 200, 50)
        self.update_style()
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                     QGraphicsRectItem.ItemIsSelectable |
                     QGraphicsRectItem.ItemSendsGeometryChanges)
        
        self.text_item = QGraphicsTextItem(title, self)
        self.text_item.setTextWidth(180)
        self.text_item.setPos(10, 10)
        self.text_item.setDefaultTextColor(Qt.black)
        self.text_item.document().setDefaultStyleSheet("font-size: 10pt;")

    def get_title(self):
        return self.text_item.toPlainText()

    def update_style(self):
        colors = {
            'chapter': QColor(200, 220, 255),
            'work': QColor(220, 255, 200),
            'resource': QColor(255, 240, 200)
        }
        self.setBrush(QBrush(colors[self.item_type]))

    def contextMenuEvent(self, event):
        menu = QMenu()
        types = ['chapter', 'work', 'resource']
        for t in types:
            action = menu.addAction(f"Сменить на {t}")
            action.triggered.connect(lambda _, t=t: self.change_type(t))
        menu.exec_(event.screenPos())

    def change_type(self, new_type):
        self.item_type = new_type
        self.update_style()
        # Здесь добавить обновление в БД

class ContainerItem(QGraphicsRectItem):
    def __init__(self, title, item_type='chapter', parent=None):
        super().__init__(parent)
        self.item_type = item_type
        self.child_items = []
        self.setRect(0, 0, 300, 400)
        self.update_style()
        self.setFlags(QGraphicsRectItem.ItemIsMovable | 
                     QGraphicsRectItem.ItemIsSelectable)
        
        self.text_item = QGraphicsTextItem(title, self)
        self.text_item.setTextWidth(280)
        self.text_item.setPos(10, 10)
        self.text_item.setDefaultTextColor(Qt.black)
        self.text_item.document().setDefaultStyleSheet("font-size: 12pt;")

    def get_title(self):
        return self.text_item.toPlainText()

    def update_style(self):
        self.setBrush(QBrush(QColor(240, 240, 240)))

    def add_child(self, item):
        if item.scene() is None:
            self.scene().addItem(item)
        item.setParentItem(self)
        self.child_items.append(item)
        self.update_layout()

    def update_layout(self):
        y = 50
        max_width = 0
        for child in self.child_items:
            child.setPos(20, y)
            max_width = max(max_width, child.rect().width())
            y += child.rect().height() + 10
        self.setRect(0, 0, max_width + 40, y)
