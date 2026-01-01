# app/supplier/ui_search_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem

from .supplier_service import SupplierService
from ..ui_utils import show_error_message

class SearchSupplierWindow(QWidget):
    supplier_selected = Signal(dict)

    def __init__(self):
        super().__init__()
        self.supplier_service = SupplierService()
        self.setWindowTitle("Pesquisar Fornecedor")
        self.setGeometry(200, 200, 600, 400)
        self.setAttribute(Qt.WA_DeleteOnClose)

        # Layout Principal
        self.main_layout = QVBoxLayout(self)

        # --- Grupo de Pesquisa ---
        self.create_search_group()

        # --- Grupo de Resultados ---
        self.create_results_group()

        # Carrega os fornecedores na inicialização
        self.load_suppliers()

    def create_search_group(self):
        search_group = QGroupBox("Pesquisa")
        search_layout = QHBoxLayout()

        self.search_text = QLineEdit()
        self.search_text.setPlaceholderText("Digite o nome do fornecedor...")
        self.search_text.returnPressed.connect(self.load_suppliers)

        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.load_suppliers)

        search_layout.addWidget(self.search_text, 1)
        search_layout.addWidget(search_button)
        search_group.setLayout(search_layout)

        self.main_layout.addWidget(search_group)

    def create_results_group(self):
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout()

        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(["ID", "Nome", "Contato"])
        self.table_view.setModel(self.table_model)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSortingEnabled(True)
        self.table_view.doubleClicked.connect(self.handle_double_click)

        results_layout.addWidget(self.table_view)
        results_group.setLayout(results_layout)
        self.main_layout.addWidget(results_group)

    def load_suppliers(self):
        search_term = self.search_text.text()
        self.table_model.removeRows(0, self.table_model.rowCount())

        if search_term:
            response = self.supplier_service.search_suppliers(search_term)
        else:
            response = self.supplier_service.get_all_suppliers()

        if not response["success"]:
            show_error_message(self, response["message"])
            return

        for supplier in response["data"]:
            id_item = QStandardItem(str(supplier['ID']))
            id_item.setData(supplier, Qt.UserRole)
            row = [
                id_item,
                QStandardItem(supplier['NOME']),
                QStandardItem(supplier['CONTATO'] or '')
            ]
            self.table_model.appendRow(row)

    def handle_double_click(self, model_index):
        item = self.table_model.itemFromIndex(model_index)
        supplier_data = item.data(Qt.UserRole)
        self.supplier_selected.emit(supplier_data)
        self.close()
