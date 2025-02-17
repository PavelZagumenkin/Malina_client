import sys

from PyQt6 import QtWidgets, QtGui, QtCore
import textwrap
import pandas as pd
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QTableWidgetItem
from PyQt6.QtWidgets import QMessageBox
from data.signals import Signals
from data.active_session import Session
from data.server_requests import ServerRequests
from data.add_logs import add_log
from data.ui.autozakaz_table import Ui_autozakaz_table
import data.windows.windows_bakery
import sys


class WindowPrognozTablesSet(QtWidgets.QMainWindow):
    def __init__(self, wb_OLAP_prodagi, periodDay, points):
        super().__init__()
        self.ui = Ui_autozakaz_table()
        self.ui.setupUi(self)
        self.signals = Signals()
        self.server_requests = ServerRequests()
        self.session = Session.get_instance()  # Получение экземпляра класса Session
        self.kod = ''
        self.name = ''
        self.points = points
        self.periodDay = periodDay
        self.column_title = ['', '', 'Кф. товара', 'Выкладка', 'Квант поставки', 'Замес', 'Код блюда', 'Блюдо',
                             'Категория блюда']
        self.column_title = self.column_title + points
        self.column_title_for_excel = ['Код блюда', 'Блюдо', 'Категория блюда'] + points
        wb_OLAP_prodagi = wb_OLAP_prodagi[self.column_title_for_excel]
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/images/icon.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        self.setWindowIcon(icon)
        self.ui.tableWidget.setRowCount(wb_OLAP_prodagi.shape[0] + 1)
        self.ui.tableWidget.setColumnCount(len(self.column_title))
        self.wrap = []
        for header in self.column_title:
            wrap = textwrap.fill(header, width=10)
            self.wrap.append(wrap)
        self.ui.tableWidget.setHorizontalHeaderLabels(self.wrap)
        self.font = QtGui.QFont("Times", 10, QFont.Weight.Bold)
        self.ui.tableWidget.horizontalHeader().setFont(self.font)
        for col in range(0, wb_OLAP_prodagi.shape[1]):
            for row in range(0, wb_OLAP_prodagi.shape[0]):
                if pd.isna(wb_OLAP_prodagi.iloc[row, col]):
                    item = QTableWidgetItem('0')
                else:
                    item = QTableWidgetItem(str(wb_OLAP_prodagi.iloc[row, col]))
                self.ui.tableWidget.setItem(row + 1, col + 6, item)
        global saveZnach
        saveZnach = {}
        for col in range(9, self.ui.tableWidget.columnCount()):
            saveZnach[col] = {}
            for row in range(1, self.ui.tableWidget.rowCount()):
                saveZnach[col][row] = float(self.ui.tableWidget.item(row, col).text())
        self.ui.tableWidget.setItem(0, 8, QTableWidgetItem("Кф. кондитерской"))
        self.ui.tableWidget.item(0, 8).setFont(self.font)
        for col_spin in range(9, self.ui.tableWidget.columnCount()):
            self.KFStoreSpin = QtWidgets.QDoubleSpinBox()
            self.KFStoreSpin.wheelEvent = lambda event: None
            self.ui.tableWidget.setCellWidget(0, col_spin, self.KFStoreSpin)
            self.ui.tableWidget.cellWidget(0, col_spin).setValue(1.00)
            self.ui.tableWidget.cellWidget(0, col_spin).setSingleStep(0.01)
            self.ui.tableWidget.cellWidget(0, col_spin).valueChanged.connect(self.raschetPrognoz)

        # Сбор всех кодов и имен
        kod_name_pairs = []
        for row_spin in range(1, self.ui.tableWidget.rowCount()):
            kod = self.ui.tableWidget.item(row_spin, 6).text()
            name = self.ui.tableWidget.item(row_spin, 7).text()
            kod_name_pairs.append((kod, name))
        kod_data = self.poisk_display_kvant_batch(kod_name_pairs)

        for row_spin in range(1, self.ui.tableWidget.rowCount()):
            kod = self.ui.tableWidget.item(row_spin, 6).text()
            if kod not in kod_data:
                self.ui.tableWidget.removeRow(row_spin)
                for c in range(9, self.ui.tableWidget.columnCount()):
                    del saveZnach[c][row_spin]
                for c in range(9, self.ui.tableWidget.columnCount()):
                    counter = row_spin + 1
                    for r in range(row_spin, self.ui.tableWidget.rowCount()):
                        saveZnach[c][r] = saveZnach[c].pop(counter)
                        counter += 1
                continue
            # if self.poisk_display_kvant_batch(self.ui.tableWidget.item(row_spin, 6).text(),
            #                                   self.ui.tableWidget.item(row_spin, 7).text()) == 'Отмена':
            #     self.ui.tableWidget.removeRow(row_spin)
            #     for c in range(9, self.ui.tableWidget.columnCount()):
            #         del saveZnach[c][row_spin]
            #     for c in range(9, self.ui.tableWidget.columnCount()):
            #         counter = row_spin + 1
            #         for r in range(row_spin, self.ui.tableWidget.rowCount()):
            #             saveZnach[c][r] = saveZnach[c].pop(counter)
            #             counter += 1
            #     continue
            data = kod_data[kod]
            self.ui.tableWidget.item(row_spin, 6).setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            self.KFTovarDSpin = QtWidgets.QDoubleSpinBox()
            self.DisplaySpin = QtWidgets.QSpinBox()
            self.KvantSpin = QtWidgets.QSpinBox()
            self.BatchSpin = QtWidgets.QSpinBox()
            self.KFTovarDSpin.wheelEvent = lambda event: None
            self.DisplaySpin.wheelEvent = lambda event: None
            self.KvantSpin.wheelEvent = lambda event: None
            self.BatchSpin.wheelEvent = lambda event: None
            self.ui.tableWidget.setCellWidget(row_spin, 2, self.KFTovarDSpin)
            self.ui.tableWidget.cellWidget(row_spin, 2).setValue(1.00)
            self.ui.tableWidget.cellWidget(row_spin, 2).setSingleStep(0.01)
            self.ui.tableWidget.cellWidget(row_spin, 2).valueChanged.connect(self.raschetPrognoz)
            self.ui.tableWidget.setCellWidget(row_spin, 3, self.DisplaySpin)
            self.ui.tableWidget.cellWidget(row_spin, 3).setMaximum(1000)
            # self.ui.tableWidget.cellWidget(row_spin, 3).setValue(
            #     self.poisk_display_kvant_batch(self.ui.tableWidget.item(row_spin, 6).text(),
            #                                    self.ui.tableWidget.item(row_spin, 7).text())[4])
            self.ui.tableWidget.cellWidget(row_spin, 3).setValue(data[4])
            self.ui.tableWidget.cellWidget(row_spin, 3).setSingleStep(1)
            self.ui.tableWidget.setCellWidget(row_spin, 4, self.KvantSpin)
            self.ui.tableWidget.cellWidget(row_spin, 4).setMaximum(1000)
            # self.ui.tableWidget.cellWidget(row_spin, 4).setValue(
            #     self.poisk_display_kvant_batch(self.ui.tableWidget.item(row_spin, 6).text(),
            #                                    self.ui.tableWidget.item(row_spin, 7).text())[5])
            self.ui.tableWidget.cellWidget(row_spin, 4).setValue(data[5])
            self.ui.tableWidget.cellWidget(row_spin, 4).setSingleStep(1)
            self.ui.tableWidget.setCellWidget(row_spin, 5, self.BatchSpin)
            self.ui.tableWidget.cellWidget(row_spin, 5).setMaximum(1000)
            # self.ui.tableWidget.cellWidget(row_spin, 5).setValue(
            #     self.poisk_display_kvant_batch(self.ui.tableWidget.item(row_spin, 6).text(),
            #                                    self.ui.tableWidget.item(row_spin, 7).text())[6])
            self.ui.tableWidget.cellWidget(row_spin, 5).setValue(data[6])
            self.ui.tableWidget.cellWidget(row_spin, 5).setSingleStep(1)
            # self.ui.tableWidget.setItem(row_spin, 8, QTableWidgetItem(self.poisk_display_kvant_batch(self.ui.tableWidget.item(row_spin, 6).text(), self.ui.tableWidget.item(row_spin, 7).text())[3]))
            self.ui.tableWidget.setItem(row_spin, 8, QTableWidgetItem(data[3]))
            self.ui.tableWidget.item(row_spin, 8).setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
            # self.ui.tableWidget.setItem(row_spin, 7, QTableWidgetItem(self.sravnenie_name(self.ui.tableWidget.item(row_spin, 6).text(), self.ui.tableWidget.item(row_spin, 7).text())))
            self.ui.tableWidget.setItem(row_spin, 7, QTableWidgetItem(self.sravnenie_name(kod, self.ui.tableWidget.item(row_spin, 7).text(), data[2])))
            self.ui.tableWidget.item(row_spin, 7).setFlags(QtCore.Qt.ItemFlag.ItemIsEnabled)
        for row_button in range(1, self.ui.tableWidget.rowCount()):
            self.copyRowButton = QtWidgets.QPushButton()
            self.ui.tableWidget.setCellWidget(row_button, 0, self.copyRowButton)
            self.ui.tableWidget.cellWidget(row_button, 0).setText('')
            iconCopy = QtGui.QIcon()
            iconCopy.addPixmap(QtGui.QPixmap("data/images/copy.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.ui.tableWidget.cellWidget(row_button, 0).setIcon(iconCopy)
            self.ui.tableWidget.cellWidget(row_button, 0).clicked.connect(self.copyRow)
            self.deleteRowButton = QtWidgets.QPushButton()
            self.ui.tableWidget.setCellWidget(row_button, 1, self.deleteRowButton)
            self.ui.tableWidget.cellWidget(row_button, 1).setText('')
            iconCross = QtGui.QIcon()
            iconCross.addPixmap(QtGui.QPixmap("data/images/cross.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.ui.tableWidget.cellWidget(row_button, 1).setIcon(iconCross)
            self.ui.tableWidget.cellWidget(row_button, 1).clicked.connect(self.deleteRow)
        self.SaveAndClose = QtWidgets.QPushButton()
        self.ui.tableWidget.setCellWidget(0, 7, self.SaveAndClose)
        self.ui.tableWidget.cellWidget(0, 7).setText('Сохранить и закрыть')
        font = QtGui.QFont()
        font.setFamily("Trebuchet MS")
        font.setPointSize(12)
        font.bold()
        font.setWeight(50)
        self.ui.tableWidget.cellWidget(0, 7).setFont(font)
        self.ui.tableWidget.cellWidget(0, 7).setStyleSheet(open('data/css/QPushButton.qss').read())
        self.ui.tableWidget.cellWidget(0, 7).clicked.connect(self.saveAndCloseDef)
        self.ui.tableWidget.resizeColumnsToContents()
        self.ui.tableWidget.cellChanged.connect(lambda row, col: self.on_cell_changed(row, col))

        # Подключаем слоты к сигналам
        self.signals.success_signal.connect(self.show_success_message)
        self.signals.failed_signal.connect(self.show_error_message)
        self.signals.crit_failed_signal.connect(self.show_crit_error_message)


    def on_cell_changed(self, row, col):
        if row >= 1 and col >= 9:
            # Получаем содержимое ячейки и проверяем, является ли оно числом
            try:
                value = float(self.ui.tableWidget.item(row, col).text())
            except ValueError:
                value = None
            # Если содержимое не является числом, то заменяем его на 0.0
            if value is None:
                self.signals.failed_signal.emit('Вы ввели не число!')
                self.ui.tableWidget.setItem(row, col, QTableWidgetItem(str(0.0)))
        else:
            return


    def raschetPrognoz(self):
        buttonClicked = self.sender()
        index = self.ui.tableWidget.indexAt(buttonClicked.pos())
        if index.row() == 0:
            for i in range(1, self.ui.tableWidget.rowCount()):
                result = round(float(saveZnach[index.column()][i]) * float(
                    self.ui.tableWidget.cellWidget(0, index.column()).value()) * float(
                    self.ui.tableWidget.cellWidget(i, 2).value()), 2)
                self.ui.tableWidget.setItem(i, index.column(), QTableWidgetItem(str(result)))
        else:
            for i in range(9, self.ui.tableWidget.columnCount()):
                result = round(float(saveZnach[i][index.row()]) * float(
                    self.ui.tableWidget.cellWidget(index.row(), 2).value()) * float(
                    self.ui.tableWidget.cellWidget(0, i).value()), 2)
                self.ui.tableWidget.setItem(index.row(), i, QTableWidgetItem(str(result)))


    def saveAndCloseDef(self):
        start_date = self.periodDay[0].toString('yyyy-MM-dd')
        end_date = self.periodDay[1].toString('yyyy-MM-dd')
        matrix_table_prognoz = []
        points_index = 0
        # Проход по каждому столбцу начиная с начала названия ТТ
        for column_index in range(9, self.ui.tableWidget.columnCount()):
            column_name = self.points[points_index]
            # Проход по каждой строке для текущего столбца
            for row_index in range(1, self.ui.tableWidget.rowCount()):
                row_data = [start_date, end_date, column_name]
                kod_dishe = self.ui.tableWidget.item(row_index, 6)
                if kod_dishe is not None:
                    row_data.append(kod_dishe.text())
                else:
                    return
                category_dishe = self.ui.tableWidget.item(row_index, 8)
                if category_dishe is not None:
                    row_data.append(category_dishe.text())
                else:
                    return
                koeff_dishe = float(self.ui.tableWidget.cellWidget(row_index, 2).value())
                if koeff_dishe is not None:
                    row_data.append(koeff_dishe)
                else:
                    return
                display = self.ui.tableWidget.cellWidget(row_index, 3).value()
                if display is not None:
                    row_data.append(display)
                else:
                    return
                kvant = self.ui.tableWidget.cellWidget(row_index, 4).value()
                if kvant is not None:
                    row_data.append(kvant)
                else:
                    return
                batch = self.ui.tableWidget.cellWidget(row_index, 5).value()
                if batch is not None:
                    row_data.append(batch)
                else:
                    return
                koeff_points = float(self.ui.tableWidget.cellWidget(0, column_index).value())
                if koeff_points is not None:
                    row_data.append(koeff_points)
                else:
                    return
                data_null = float(saveZnach[column_index][row_index])
                if data_null is not None:
                    row_data.append(data_null)
                else:
                    row_data.append(0)  # или любое значение по умолчанию для пустых ячеек
                data_prognoz = float(self.ui.tableWidget.item(row_index, column_index).text())
                if data_prognoz is not None:
                    row_data.append(data_prognoz)
                else:
                    row_data.append(0)  # или любое значение по умолчанию для пустых ячеек
                author = self.session.get_username()  # Получение имени пользователя из экземпляра класса Session
                row_data.append(author)
                # Добавление строки в матрицу
                matrix_table_prognoz.append(row_data)
            points_index += 1
        data_server = self.server_requests.post('save_prognoz', {matrix_table_prognoz})
        if 'Критическая ошибка' in data_server['result']:
            self.signals.crit_failed_signal.emit(data_server['result'])
        self.close()


    def copyRow(self):
        otvet_dialog_copy_row = self.dialog_copy_row()
        if otvet_dialog_copy_row == 0:
            return
        else:
            kod = self.kod
            name = self.name
            kod_name_pairs = [(kod, name)]
            data_dishe = self.poisk_display_kvant_batch(kod_name_pairs)
            buttonClicked = self.sender()
            index = self.ui.tableWidget.indexAt(buttonClicked.pos())
            rowPosition = self.ui.tableWidget.rowCount()
            self.ui.tableWidget.insertRow(rowPosition)
            self.copyRowButton = QtWidgets.QPushButton()
            self.ui.tableWidget.setCellWidget(rowPosition, 0, self.copyRowButton)
            self.ui.tableWidget.cellWidget(rowPosition, 0).setText('')
            iconCopy = QtGui.QIcon()
            iconCopy.addPixmap(QtGui.QPixmap("data/images/copy.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.ui.tableWidget.cellWidget(rowPosition, 0).setIcon(iconCopy)
            self.ui.tableWidget.cellWidget(rowPosition, 0).clicked.connect(self.copyRow)
            self.deleteRowButton = QtWidgets.QPushButton()
            self.ui.tableWidget.setCellWidget(rowPosition, 1, self.deleteRowButton)
            self.ui.tableWidget.cellWidget(rowPosition, 1).setText('')
            iconCross = QtGui.QIcon()
            iconCross.addPixmap(QtGui.QPixmap("data/images/cross.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            self.ui.tableWidget.cellWidget(rowPosition, 1).setIcon(iconCross)
            self.ui.tableWidget.cellWidget(rowPosition, 1).clicked.connect(self.deleteRow)
            self.KFTovarDSpin = QtWidgets.QDoubleSpinBox()
            self.DisplaySpin = QtWidgets.QSpinBox()
            self.KvantSpin = QtWidgets.QSpinBox()
            self.BatchSpin = QtWidgets.QSpinBox()
            self.KFTovarDSpin.wheelEvent = lambda event: None
            self.DisplaySpin.wheelEvent = lambda event: None
            self.KvantSpin.wheelEvent = lambda event: None
            self.BatchSpin.wheelEvent = lambda event: None
            self.ui.tableWidget.setCellWidget(rowPosition, 2, self.KFTovarDSpin)
            self.ui.tableWidget.cellWidget(rowPosition, 2).setValue(1.00)
            self.ui.tableWidget.cellWidget(rowPosition, 2).setSingleStep(0.01)
            self.ui.tableWidget.cellWidget(rowPosition, 2).valueChanged.connect(self.raschetPrognoz)
            self.ui.tableWidget.setCellWidget(rowPosition, 3, self.DisplaySpin)
            self.ui.tableWidget.cellWidget(rowPosition, 3).setValue(list(data_dishe.values())[0][4])
            self.ui.tableWidget.cellWidget(rowPosition, 3).setMaximum(1000)
            self.ui.tableWidget.cellWidget(rowPosition, 3).setSingleStep(1)
            self.ui.tableWidget.setCellWidget(rowPosition, 4, self.KvantSpin)
            self.ui.tableWidget.cellWidget(rowPosition, 4).setValue(list(data_dishe.values())[0][5])
            self.ui.tableWidget.cellWidget(rowPosition, 4).setMaximum(1000)
            self.ui.tableWidget.cellWidget(rowPosition, 4).setSingleStep(1)
            self.ui.tableWidget.setCellWidget(rowPosition, 5, self.BatchSpin)
            self.ui.tableWidget.cellWidget(rowPosition, 5).setValue(list(data_dishe.values())[0][6])
            self.ui.tableWidget.cellWidget(rowPosition, 5).setMaximum(1000)
            self.ui.tableWidget.cellWidget(rowPosition, 5).setSingleStep(1)
            for c in range(6, 9):
                if c == 6:
                    self.ui.tableWidget.setItem(rowPosition, c, QTableWidgetItem(list(data_dishe.values())[0][1]))
                elif c == 7:
                    self.ui.tableWidget.setItem(rowPosition, c, QTableWidgetItem(list(data_dishe.values())[0][2]))
                elif c == 8:
                    self.ui.tableWidget.setItem(rowPosition, c, QTableWidgetItem(list(data_dishe.values())[0][3]))
            for c in range(9, self.ui.tableWidget.columnCount()):
                self.ui.tableWidget.setItem(rowPosition, c, QTableWidgetItem(str(round(saveZnach[c][index.row()] * float(self.ui.tableWidget.cellWidget(0, c).value()), 2))))
            for c in range(9, self.ui.tableWidget.columnCount()):
                saveZnach[c][rowPosition] = round(float(self.ui.tableWidget.item(rowPosition, c).text()) / float(self.ui.tableWidget.cellWidget(0, c).value()), 2)


    def deleteRow(self):
        buttonClicked = self.sender()
        index = self.ui.tableWidget.indexAt(buttonClicked.pos())
        self.ui.tableWidget.removeRow(index.row())
        for c in range(9, self.ui.tableWidget.columnCount()):
            del saveZnach[c][index.row()]
        for c in range(9, self.ui.tableWidget.columnCount()):
            counter = index.row() + 1
            for r in range(index.row(), self.ui.tableWidget.rowCount()):
                saveZnach[c][r] = saveZnach[c].pop(counter)
                counter += 1


    def dialog_copy_row(self):
        dialog_copy = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        button_select_new_batch = QtWidgets.QPushButton('Зарегистрировать новое блюдо', dialog_copy)
        button_select_new_batch.clicked.connect(lambda: self.handle_button_click('Новое блюдо', dialog_copy))
        button_select_from_existing = QtWidgets.QPushButton('Выбрать из существующих', dialog_copy)
        button_select_from_existing.clicked.connect(lambda: self.handle_button_click('Существующее блюдо', dialog_copy))
        button_cancel = QtWidgets.QPushButton('Отменить операцию копирования', dialog_copy)
        button_cancel.clicked.connect(dialog_copy.reject)
        layout.addWidget(QtWidgets.QLabel(
            f'Вы хотите применить продажи к новому блюду или уже существующему?'))
        layout.addWidget(button_select_new_batch)
        layout.addWidget(button_select_from_existing)
        layout.addWidget(button_cancel)
        dialog_copy.setLayout(layout)
        dialog_copy.setWindowTitle('Примите решение по копированию строки')
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/images/icon.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        dialog_copy.setWindowIcon(icon)
        # Открываем диалоговое окно и ждем его завершения
        request = dialog_copy.exec()
        return request


    def handle_button_click(self, button_text, dialog_copy):
        if button_text == 'Новое блюдо':
            result = self.dialog_add_display_kvant_batch(kod='Введите код блюда', name='Введите наименование блюда', edit=True)
            if result == 'Товар успешно зарегистрирован':
                return dialog_copy.accept()
            elif result == 'Отмена':
                return
            else:
                self.signals.failed_signal.emit(result)
        else:
            result = self.dialog_select_from_existing()
            if result == 'Успешно':
                return dialog_copy.accept()
            elif result == 'Отмена':
                return


    def dialog_select_from_existing(self):
        dialog = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        button_yes = QtWidgets.QPushButton('Выбрать', dialog)
        button_yes.clicked.connect(dialog.accept)
        button_cancel = QtWidgets.QPushButton('Отмена', dialog)
        button_cancel.clicked.connect(dialog.reject)
        spisok_kods_dishes_in_table = []
        for row in range (1, self.ui.tableWidget.rowCount()):
            spisok_kods_dishes_in_table.append(self.ui.tableWidget.item(row, 6).text())
        spisok_names_dishes_in_DB = self.spisok_dishes(spisok_kods_dishes_in_table)
        if 'Ошибка' in spisok_names_dishes_in_DB:
            self.signals.failed_signal.emit(spisok_names_dishes_in_DB)
        else:
            spisok_names_dishe_combobox = QtWidgets.QComboBox(dialog)
            spisok_names_dishe_combobox.addItems(spisok_names_dishes_in_DB)
            layout.addWidget(QtWidgets.QLabel(
                f'Выберите из выпадающего списка блюдо,\nдля которого хотите применить продажи из выбранной строки'))
            layout.addWidget(spisok_names_dishe_combobox)
            layout.addWidget(button_yes)
            layout.addWidget(button_cancel)
            dialog.setLayout(layout)
            dialog.setWindowTitle('Конфликт наименований товара')
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap("data/images/icon.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
            dialog.setWindowIcon(icon)
            # Открываем диалоговое окно и ждем его завершения
            request = dialog.exec()
            # Проверям результат обращения к БД
            if request == 0:
                return 'Отмена'
            else:
                self.kod = self.poisk_kod_dishe_in_DB_po_name(spisok_names_dishe_combobox.currentText())
                self.name = spisok_names_dishe_combobox.currentText()
                return 'Успешно'


    def poisk_kod_dishe_in_DB_po_name(self, name):
        data_server = self.server_requests.post('poisk_kod_dishe_in_DB', {'name': name})
        if 'Критическая ошибка' in data_server['result']:
            self.signals.crit_failed_signal.emit(data_server['result'])
        return data_server['result']


    def spisok_dishes(self, spisok_kods_dishes_in_table):
        data_server = self.server_requests.post('spisok_kods_dishes_in_table', {'spisok_kods_dishes_in_table': spisok_kods_dishes_in_table})
        if 'Критическая ошибка' in data_server['result']:
            self.signals.crit_failed_signal.emit(data_server['result'])
        return data_server['result']


    # def sravnenie_name(self, kod, name):
    #     data_server = self.server_requests.post('poisk_data_tovar', {'kod': kod})
    #     if 'Критическая ошибка' in data_server['result']:
    #         self.signals.crit_failed_signal.emit(data_server['result'])
    #     if data_server['result'][0][2] != name:
    #         return self.dialog_select_name(kod, name, data_server['result'][0][2])
    #     return name

    def sravnenie_name(self, kod, name, server_name):
        if server_name != name:
            return self.dialog_select_name(kod, name, server_name)
        return name


    def dialog_select_name(self, kod, name_excel, name_DB):
        dialog = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        button_yes = QtWidgets.QPushButton('Изменить', dialog)
        button_yes.clicked.connect(dialog.accept)
        button_no = QtWidgets.QPushButton('Нет', dialog)
        button_no.clicked.connect(dialog.reject)
        layout.addWidget(QtWidgets.QLabel(
            f'В OLAP-отчете для блюда под кодом: {kod}, наименование\nтовара отличается от того,что хранится в Базе данных.'))
        olap_name_line_edit = QtWidgets.QLineEdit(dialog)
        DB_name_line_edit = QtWidgets.QLineEdit(dialog)
        layout.addWidget(QtWidgets.QLabel('Наименование в OLAP-отчете:'))
        layout.addWidget(olap_name_line_edit)
        olap_name_line_edit.setText(name_excel)
        olap_name_line_edit.setReadOnly(True)
        layout.addWidget(QtWidgets.QLabel('Наименование в Базе данных:'))
        layout.addWidget(DB_name_line_edit)
        DB_name_line_edit.setText(name_DB)
        DB_name_line_edit.setReadOnly(True)
        layout.addWidget(QtWidgets.QLabel(
            f'Изменить наименование в Базе данных?'))
        layout.addWidget(button_yes)
        layout.addWidget(button_no)
        dialog.setLayout(layout)
        dialog.setWindowTitle('Конфликт наименований товара')
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/images/icon.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        dialog.setWindowIcon(icon)
        # Открываем диалоговое окно и ждем его завершения
        request = dialog.exec()
        # Проверям результат обращения к БД
        if request == 0:
            return name_DB
        else:
            data_server = self.server_requests.post('update_name_dishe', {'kod': kod, 'name_excel': name_excel})
            if 'Критическая ошибка' in data_server['result']:
                self.signals.crit_failed_signal.emit(data_server['result'])
            if "успешно изменено" in data_server['result']:
                return name_excel
            else:
                self.signals.failed_signal.emit(data_server['result'])
                return name_DB


    # Поиск кода в базе данных
    def poisk_display_kvant_batch(self, kod_name_pairs):
        # data_server = self.server_requests.post('poisk_data_tovar', {'kod': kod})
        # if 'Критическая ошибка' in data_server['result']:
        #     self.signals.crit_failed_signal.emit(data_server['result'])
        # if not data_server['result']:
        #     result_request = self.dialog_add_display_kvant_batch(kod, name, edit=False)
        #     if result_request == 'Отмена':
        #         return 'Отмена'
        #     elif result_request == 'Товар успешно зарегистрирован':
        #         data_server = self.server_requests.post('poisk_data_tovar', {'kod': kod})
        #         if 'Критическая ошибка' in data_server['result']:
        #             self.signals.crit_failed_signal.emit(data_server['result'])
        #         return data_server['result'][0]
        #     elif 'Ошибка' in result_request:
        #         self.signals.failed_signal.emit(result_request)
        #         return 'Отмена'
        # else:
        #     return data_server['result'][0]
        kods = [pair[0] for pair in kod_name_pairs]
        data_server = self.server_requests.post('poisk_data_tovar', {'kods': kods})
        if 'Критическая ошибка' in data_server['results']:
            self.signals.crit_failed_signal.emit(data_server['results'])
            return 'Отмена'
        if data_server['results'] == 'Отсутствует':
            missing_kod = data_server['kod']
            missing_name = next(name for kod, name in kod_name_pairs if kod == missing_kod)
            result_request = self.dialog_add_display_kvant_batch(missing_kod, missing_name, edit=False)
            if result_request == 'Отмена':
                return 'Отмена'
            elif result_request == 'Товар успешно зарегистрирован':
                data_server = self.server_requests.post('poisk_data_tovar', {'kods': kods})
                if 'Критическая ошибка' in data_server['result']:
                    self.signals.crit_failed_signal.emit(data_server['result'])
                kod_data = {item[1]: item for sublist in data_server['results'] for item in sublist}  # Создаем словарь для быстрого доступа
                return kod_data
            elif 'Ошибка' in result_request:
                self.signals.failed_signal.emit(result_request)
                return 'Отмена'
        else:
            kod_data = {item[1]: item for sublist in data_server['results'] for item in sublist}  # Создаем словарь для быстрого доступа
            return kod_data


    def dialog_add_display_kvant_batch(self, kod, name, edit):
        # Создаем диалоговое окно
        dialog = QtWidgets.QDialog()
        layout = QtWidgets.QVBoxLayout()
        kod_line_edit = QtWidgets.QLineEdit(dialog)
        name_line_edit = QtWidgets.QLineEdit(dialog)
        category_combobox = QtWidgets.QComboBox(dialog)
        display_line_edit = QtWidgets.QLineEdit(dialog)
        display_line_edit.setValidator(QtGui.QIntValidator())
        kvant_line_edit = QtWidgets.QLineEdit(dialog)
        kvant_line_edit.setValidator(QtGui.QIntValidator())
        batch_line_edit = QtWidgets.QLineEdit(dialog)
        batch_line_edit.setValidator(QtGui.QIntValidator())
        koeff_ice_sklad_line_edit = QtWidgets.QLineEdit(dialog)
        koeff_ice_sklad_line_edit.setValidator(QtGui.QDoubleValidator())
        button_ok = QtWidgets.QPushButton('Добавить', dialog)
        button_ok.clicked.connect(dialog.accept)
        layout.addWidget(QtWidgets.QLabel(
            f'Установите необходимые значения\nдля товара отсутствующего в БД'))
        layout.addWidget(QtWidgets.QLabel('Код:'))
        layout.addWidget(kod_line_edit)
        kod_line_edit.setText(kod)
        if edit == False:
            kod_line_edit.setReadOnly(True)
        layout.addWidget(QtWidgets.QLabel('Наименование:'))
        layout.addWidget(name_line_edit)
        name_line_edit.setText(name)
        if edit == False:
            name_line_edit.setReadOnly(True)
        layout.addWidget(QtWidgets.QLabel('Выберите категорию:'))
        layout.addWidget(category_combobox)
        data_server = self.server_requests.post('get_spisok_category_in_DB')
        if 'Критическая ошибка' in data_server['result']:
            self.signals.crit_failed_signal.emit(data_server['result'])
        category_combobox.addItems(data_server['result'])
        category_combobox.wheelEvent = lambda event: None
        category_combobox.setCurrentText('Выпечка пекарни')
        layout.addWidget(QtWidgets.QLabel('Выкладка:'))
        layout.addWidget(display_line_edit)
        display_line_edit.setText('1')
        layout.addWidget(QtWidgets.QLabel('Квант поставки:'))
        layout.addWidget(kvant_line_edit)
        kvant_line_edit.setText('1')
        layout.addWidget(QtWidgets.QLabel('Минимальный замес:'))
        layout.addWidget(batch_line_edit)
        batch_line_edit.setText('1')
        layout.addWidget(QtWidgets.QLabel('Коэффициент для пекарни:'))
        layout.addWidget(koeff_ice_sklad_line_edit)
        koeff_ice_sklad_line_edit.setText('1')
        layout.addWidget(button_ok)
        dialog.setLayout(layout)
        dialog.setWindowTitle('Добавление нового товара в БД')
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("data/images/icon.png"), QtGui.QIcon.Mode.Normal, QtGui.QIcon.State.Off)
        dialog.setWindowIcon(icon)
        # Открываем диалоговое окно и ждем его завершения
        request = dialog.exec()
        # Проверям результат обращения к БД
        otvet_DB = "Отмена"
        if request == 1:
            kod = kod_line_edit.text()
            name = name_line_edit.text()
            category = category_combobox.currentText()
            display = display_line_edit.text()
            kvant = kvant_line_edit.text()
            batch = batch_line_edit.text()
            koeff_ice_sklad = koeff_ice_sklad_line_edit.text()
            data_server = self.server_requests.post('insert_data_tovar', {'kod': kod, 'name': name, 'category': category, 'display': display, 'kvant': kvant, 'batch': batch, 'koeff_ice_sklad': koeff_ice_sklad})
            if 'Критическая ошибка' in data_server['result']:
                self.signals.crit_failed_signal.emit(data_server['result'])
            otvet_DB = data_server['result']
            self.kod = kod
            self.name = name
        return otvet_DB


    def show_success_message(self, message):
        pass


    def show_error_message(self, message):
        # Отображаем сообщение об ошибке
        QtWidgets.QMessageBox.information(self, "Ошибка", message)


    def show_crit_error_message(self, message):
        QtWidgets.QMessageBox.information(self, "Критическая ошибка", message)
        sys.exit()


    def closeEvent(self, event):
        self.session.set_work_date(
            self.periodDay[0].toString('yyyy-MM-dd'))  # Сохраняем время периода, скоторым работаем
        global WindowBakery
        if event.spontaneous():
            reply = QMessageBox()
            reply.setWindowTitle("Завершение работы с таблицой")
            reply.setWindowIcon(QtGui.QIcon("data/images/icon.png"))
            reply.setText("Вы хотите завершить работу с таблицей?")
            reply.setIcon(QMessageBox.Icon.Question)
            reply.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            reply.setDefaultButton(QMessageBox.StandardButton.Cancel)
            otvet = reply.exec()
            if otvet == QMessageBox.StandardButton.Yes:
                event.accept()
                WindowBakery = data.windows.windows_bakery.WindowBakery()
                WindowBakery.show()
            else:
                event.ignore()
        else:
            event.accept()
            WindowBakery = data.windows.windows_bakery.WindowBakery()
            WindowBakery.show()