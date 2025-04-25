import sys
from PyQt5.QtWidgets import (QMainWindow, QGraphicsView, 
                            QGraphicsScene, QDockWidget, QDialog, QMessageBox, QTreeWidget, QTreeWidgetItem, 
                            QTextEdit)
from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from PyQt5.QtGui import QBrush, QColor

from .logic import ContainerItem, DraggableItem
from .database import DatabaseConfigDialog

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = None
        self.last_x = 50
        self.init_db_connection()
        self.initUI()

        self.properties_dock = QDockWidget("Свойства", self)
        self.properties_text = QTextEdit()
        self.properties_dock.setWidget(self.properties_text)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_dock)
        
        self.tree_widget.itemClicked.connect(self.show_properties)
        self.scene.selectionChanged.connect(self.handle_selection)

    def initUI(self):
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        self.dock = QDockWidget("Elements", self)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Структура сметы")
        self.dock.setWidget(self.tree_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        self.setWindowTitle('Смета - графический редактор')
        self.setGeometry(100, 100, 1200, 800)
        self.load_data()

    def init_db_connection(self):
        dlg = DatabaseConfigDialog(self)
        if dlg.exec_() == QDialog.Accepted:
            params = dlg.get_connection_params()
            dlg.save_settings()
            
            self.db = QSqlDatabase.addDatabase(params['db_type'])
            if params['db_type'] != "QSQLITE":
                self.db.setHostName(params['host'])
                self.db.setPort(int(params['port']))
                self.db.setUserName(params['user'])
                self.db.setPassword(params['password'])
            self.db.setDatabaseName(params['db_name'])
            
            if not self.db.open():
                QMessageBox.critical(self, "Ошибка", 
                    f"Не удалось подключиться к БД:\n{self.db.lastError().text()}")
                sys.exit(1)
        else:
            sys.exit(0)

    def load_data_from_db(self):
        chapters = []
        query = QSqlQuery()
        if not query.exec("SELECT id, name, excel_row FROM chapters"):
            raise Exception(query.lastError().text())
        while query.next():
            chapters.append({
                'id': query.value(0),
                'name': query.value(1),
                'excel_row': query.value(2)
            })
        
        works = []
        if not query.exec("SELECT id, chapter_id, code, description, quantity FROM works"):
            raise Exception(query.lastError().text())
        while query.next():
            works.append({
                'id': query.value(0),
                'chapter_id': query.value(1),
                'code': query.value(2),
                'description': query.value(3),
                'quantity': query.value(4)
            })
        
        resources = []
        if not query.exec("SELECT id, work_id, type, code, description, quantity FROM resources"):
            raise Exception(query.lastError().text())
        while query.next():
            resources.append({
                'id': query.value(0),
                'work_id': query.value(1),
                'type': query.value(2),
                'code': query.value(3),
                'description': query.value(4),
                'quantity': query.value(5)
            })
        
        return chapters, works, resources

    def initUI(self):
        self.scene = QGraphicsScene()
        self.view = CustomGraphicsView(self.scene)
        self.setCentralWidget(self.view)
        
        self.dock = QDockWidget("Elements", self)
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabel("Структура сметы")
        self.dock.setWidget(self.tree_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock)
        
        self.setWindowTitle('Смета - графический редактор')
        self.setGeometry(100, 100, 1200, 800)
        self.load_data()

    def load_data(self):
        try:
            chapters, works, resources = self.load_data_from_db()
            self.tree_widget.clear()
            self.scene.clear()
            x_pos = 50

            for chapter in chapters:
                container = ContainerItem(chapter['name'], 'chapter')
                container.setPos(x_pos, 50)
                self.scene.addItem(container)
                x_pos += 400

                chapter_item = QTreeWidgetItem(self.tree_widget, [f"Раздел: {chapter['name']}"])

                for work in works:
                    if work['chapter_id'] == chapter['id']:
                        work_item = ContainerItem(work['description'], 'work')
                        work_item.setBrush(QBrush(QColor(220, 255, 200)))
                        container.add_child(work_item)

                        work_tree_item = QTreeWidgetItem(chapter_item, [f"Работа: {work['description']}"])

                        for resource in resources:
                            if resource['work_id'] == work['id']:
                                res_item = DraggableItem(resource['description'], 'resource')
                                work_item.add_child(res_item)
                                QTreeWidgetItem(work_tree_item, [f"Ресурс: {resource['description']}"])

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки данных:\n{str(e)}")
            sys.exit(1)

    def show_properties(self, item):
        text = []
        if isinstance(item, QTreeWidgetItem):
            if "Раздел:" in item.text(0):
                text.append("Тип: Раздел")
            elif "Работа:" in item.text(0):
                text.append("Тип: Работа")
            elif "Ресурс:" in item.text(0):
                text.append("Тип: Ресурс")
        elif isinstance(item, (ContainerItem, DraggableItem)):
            text.append(f"Тип: {item.item_type}")
            text.append(f"Название: {item.get_title()}")
        
        self.properties_text.setPlainText("\n".join(text))

    def handle_selection(self):
        items = self.scene.selectedItems()
        if items:
            self.show_properties(items[0])

    def show_properties(self, item):
        text = []
        if isinstance(item, QTreeWidgetItem):
            # Обработка элементов дерева
            if "Раздел:" in item.text(0):
                text.append("Тип: Раздел")
            elif "Работа:" in item.text(0):
                text.append("Тип: Работа")
            elif "Ресурс:" in item.text(0):
                text.append("Тип: Ресурс")
        elif isinstance(item, (ContainerItem, DraggableItem)):
            # Обработка графических элементов
            text.append(f"Тип: {item.item_type}")
            text.append(f"Название: {item.get_title()}")
        
        self.properties_text.setPlainText("\n".join(text))

    def handle_selection(self):
        items = self.scene.selectedItems()
        if items:
            self.show_properties(items[0])

class CustomGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self._pan = False
        self._pan_start = QPoint()

    def mousePressEvent(self, event):
        if event.button() == Qt.RightButton:
            self._pan = True
            self._pan_start = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        else:
            super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.RightButton:
            self._pan = False
            self.setCursor(Qt.ArrowCursor)
        else:
            super().mouseReleaseEvent(event)

    def mouseMoveEvent(self, event):
        if self._pan:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() - delta.y())
            self._pan_start = event.pos()
        super().mouseMoveEvent(event)
