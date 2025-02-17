from PyQt6 import QtWidgets, QtGui
from data.ui.sections import Ui_WindowSections
from data.active_session import Session
from data.signals import Signals
from data.server_requests import ServerRequests
from data.add_logs import add_log
import data.windows.windows_authorization
import data.windows.windows_control
import data.windows.windows_logistics
import data.windows.windows_production
import sys


class WindowSections(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_WindowSections()
        self.ui.setupUi(self)
        self.signals = Signals()
        self.server_requests = ServerRequests()
        self.session = Session.get_instance()  # Получение экземпляра класса Session
        self.role = self.session.get_role()  # Получение роли пользователя из экземпляра класса Session
        if self.role == 'operator':
            self.ui.btn_logistics.setEnabled(True)
        elif self.role == 'logist':
            self.ui.btn_logistics.setEnabled(True)
        elif self.role == 'supervisor':
            self.ui.btn_trade.setEnabled(True)
        elif self.role == 'manager':
            self.ui.btn_office.setEnabled(True)
        elif self.role == 'superadmin':
            self.ui.btn_logistics.setEnabled(True)
            self.ui.btn_trade.setEnabled(True)
            self.ui.btn_production.setEnabled(True)
            self.ui.btn_office.setEnabled(True)
            self.ui.btn_control.setEnabled(True)
        self.ui.btn_exit.clicked.connect(self.logout)
        self.ui.btn_logistics.clicked.connect(self.show_logistics)
        self.ui.btn_control.clicked.connect(self.show_control)
        self.ui.btn_production.clicked.connect(self.show_production)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/images/icon.ico"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.setWindowIcon(icon)
        # Подключаем слоты к сигналам
        self.signals.success_signal.connect(self.show_success_message)
        self.signals.failed_signal.connect(self.show_error_message)
        self.signals.crit_failed_signal.connect(self.show_crit_error_message)

    # Обработка выхода пользователя
    def logout(self):
        logs_result = add_log(f"Пользователь {self.session.get_username()} выполнил вход в систему.")
        if "Лог записан" in logs_result['result']:
            self.signals.success_signal.emit(logs_result['result'])
            self.close()
            global windowLogin
            windowLogin = data.windows.windows_authorization.WindowAuthorization()
            windowLogin.show()
            windowLogin.ui.label_login_password.setFocus()  # Фокус по умолчанию на тексте
            windowLogin.ui.label_login_password.setStyleSheet("color: rgb(0, 0, 0)")
            windowLogin.ui.label_login_password.setText('Введите логин и пароль')
            windowLogin.ui.line_login.clear()
            windowLogin.ui.line_password.clear()
        elif 'Критическая ошибка' in logs_result['result']:
            self.signals.crit_failed_signal.emit(logs_result['result'])
        else:
            self.signals.failed_signal.emit(logs_result['result'])

    # Закрываем выбор раздела, открываем выпечку
    def show_logistics(self):
        self.close()
        global WindowLogistics
        WindowLogistics = data.windows.windows_logistics.WindowLogistics()
        WindowLogistics.show()

    # Закрываем выбор раздела, открываем выпечку
    def show_production(self):
        self.close()
        global WindowProduction
        WindowProduction = data.windows.windows_production.WindowProduction()
        WindowProduction.show()

    # Закрываем выбор раздела, открываем выпечку
    def show_control(self):
        self.close()
        global WindowControl
        WindowControl = data.windows.windows_control.WindowControl()
        WindowControl.show()

    def show_success_message(self, message):
        pass

    def show_error_message(self, message):
        QtWidgets.QMessageBox.information(self, "Ошибка", message)

    def show_crit_error_message(self, message):
        QtWidgets.QMessageBox.information(self, "Критическая ошибка", message)
        sys.exit()

    def closeEvent(self, event):
        if event.spontaneous():
            logs_result = add_log(f"Пользователь {self.session.get_username()} вышел из системы.")
            if "Лог записан" in logs_result['result']:
                self.signals.success_signal.emit(logs_result['result'])
                self.close()
            elif 'Критическая ошибка' in logs_result['result']:
                self.signals.crit_failed_signal.emit(logs_result['result'])
            else:
                self.signals.failed_signal.emit(logs_result['result'])
        event.accept()
