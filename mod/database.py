from PyQt5.QtWidgets import (QDialog, QLineEdit, QPushButton, QFormLayout, 
                            QComboBox)
from PyQt5.QtCore import QSettings

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
