import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QGraphicsView, 
                            QGraphicsScene, QGraphicsRectItem, QGraphicsTextItem,
                            QDockWidget, QDialog, QLineEdit, QPushButton, QFormLayout, 
                            QComboBox, QMessageBox, QTreeWidget, QTreeWidgetItem, 
                            QTextEdit, QMenu)
from PyQt5.QtCore import Qt, QPointF, QSettings, QPoint
from PyQt5.QtGui import QBrush, QColor, QKeyEvent, QContextMenuEvent
from PyQt5.QtSql import QSqlDatabase, QSqlQuery

class DatabaseConfigDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к базе данных")
        self.setFixedSize(400, 300)
        
        self.initUI()
        self.load_settings()

    def initUI(self):
        layout = QFormLayout()
        
        self.db_type = QComboBox()
        self.db_type.addItems(["QSQLITE", "QMYSQL", "QPSQL"])
        self.db_type.currentTextChanged.connect(self.update_fields)
        
        self.host = QLineEdit()
        self.port = QLineEdit()
        self.port.setInputMask("00000")
        self.user = QLineEdit()
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.db_name = QLineEdit()
        
        self.btn_connect = QPushButton("Подключиться")
        self.btn_connect.clicked.connect(self.accept)
        
        layout.addRow("Тип БД:", self.db_type)
        layout.addRow("Сервер:", self.host)
        layout.addRow("Порт:", self.port)
        layout.addRow("Пользователь:", self.user)
        layout.addRow("Пароль:", self.password)
        layout.addRow("Имя БД:", self.db_name)
        layout.addRow(self.btn_connect)
        
        self.setLayout(layout)
        self.update_fields()

    def update_fields(self):
        db_type = self.db_type.currentText()
        is_sqlite = db_type == "QSQLITE"
        self.host.setDisabled(is_sqlite)
        self.port.setDisabled(is_sqlite)
        self.user.setDisabled(is_sqlite)
        self.password.setDisabled(is_sqlite)

    def get_connection_params(self):
        return {
            'db_type': self.db_type.currentText(),
            'host': self.host.text(),
            'port': self.port.text(),
            'user': self.user.text(),
            'password': self.password.text(),
            'db_name': self.db_name.text()
        }

    def save_settings(self):
        settings = QSettings("MyCompany", "EstimateEditor")
        params = self.get_connection_params()
        for key, value in params.items():
            settings.setValue(key, value)

    def load_settings(self):
        settings = QSettings("MyCompany", "EstimateEditor")
        self.db_type.setCurrentText(settings.value("db_type", "QSQLITE"))
        self.host.setText(settings.value("host", ""))
        self.port.setText(settings.value("port", ""))
        self.user.setText(settings.value("user", ""))
        self.password.setText(settings.value("password", ""))
        self.db_name.setText(settings.value("db_name", "estimates.db"))


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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_()) 