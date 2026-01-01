# app/stock/ui_entry_search_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QComboBox, QPushButton, QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from app.stock.service import StockService
from app.utils.ui_utils import show_error_message
from app.stock.ui_entry_edit_window import EntryEditWindow

class EntrySearchWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.stock_service = StockService()
        self.edit_window = None
        self.setWindowTitle("Pesquisa de Entradas de Insumo")
        self.setGeometry(200, 200, 900, 700)
        self.setup_ui()
        self.load_entries()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        search_group = QGroupBox("Pesquisa")
        search_layout = QHBoxLayout()
        self.search_field = QComboBox()
        self.search_field.addItems(["ID", "Fornecedor", "Nº Nota", "Status"])
        self.search_term = QLineEdit()
        self.search_term.returnPressed.connect(self.load_entries)
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.load_entries)
        new_button = QPushButton("Nova Entrada")
        new_button.clicked.connect(self.open_new_entry_window)

        search_layout.addWidget(self.search_field)
        search_layout.addWidget(self.search_term, 1)
        search_layout.addWidget(search_button)
        search_layout.addWidget(new_button)
        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout()
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(["ID", "Data Entrada", "Data Digitação", "Fornecedor", "Nº Nota", "Valor Total", "Status"])
        self.table_view.setModel(self.table_model)

        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.Stretch)

        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSortingEnabled(True)
        self.table_view.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        self.table_view.doubleClicked.connect(self.open_edit_entry_window)

        results_layout.addWidget(self.table_view)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

    def load_entries(self):
        self.table_model.removeRows(0, self.table_model.rowCount())
        search_term = self.search_term.text()
        search_field = self.search_field.currentText()
        response = self.stock_service.list_entries(search_term, search_field)

        if response["success"]:
            for entry in response["data"]:
                row = [
                    QStandardItem(str(entry['ID'])),
                    QStandardItem(entry.get('DATA_ENTRADA', '')),
                    QStandardItem(entry.get('DATA_DIGITACAO', '')),
                    QStandardItem(entry.get('FORNECEDOR', '')),
                    QStandardItem(entry.get('NUMERO_NOTA', '')),
                    QStandardItem(f"{entry.get('VALOR_TOTAL', 0):.2f}" if entry.get('VALOR_TOTAL') is not None else "N/A"),
                    QStandardItem(entry.get('STATUS', ''))
                ]
                self.table_model.appendRow(row)
        else:
            show_error_message(self, "Error", response["message"])

    def open_new_entry_window(self):
        self.show_edit_window(entry_id=None)

    def open_edit_entry_window(self, model_index):
        entry_id = int(self.table_model.item(model_index.row(), 0).text())
        self.show_edit_window(entry_id=entry_id)

    def show_edit_window(self, entry_id):
        if self.edit_window is None:
            self.edit_window = EntryEditWindow(entry_id=entry_id)
            self.edit_window.destroyed.connect(self.on_edit_window_closed)
            self.edit_window.show()
        else:
            self.edit_window.activateWindow()
            self.edit_window.raise_()

    def on_edit_window_closed(self):
        self.edit_window = None
        self.load_entries()
