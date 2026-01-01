# app/supplier/ui_search_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from PySide6.QtCore import Signal, Qt
from app.supplier.service import SupplierService
from app.utils.ui_utils import show_error_message
from app.supplier.ui_edit_window import SupplierEditWindow

def _safe_str(value):
    """Converte o valor para string, tratando None como uma string vazia."""
    return str(value) if value is not None else ""

class SupplierSearchWindow(QWidget):
    supplier_selected = Signal(dict)

    def __init__(self, selection_mode=False):
        super().__init__()
        self.supplier_service = SupplierService()
        self.edit_window = None
        self.selection_mode = selection_mode

        title = "Selecionar Fornecedor" if self.selection_mode else "Pesquisa de Fornecedores"
        self.setWindowTitle(title)
        self.setGeometry(200, 200, 800, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        search_group = QGroupBox("Pesquisa")
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Pesquisar por nome...")
        self.search_input.returnPressed.connect(self.load_suppliers)
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.load_suppliers)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(search_button)

        if not self.selection_mode:
            new_button = QPushButton("Novo")
            new_button.clicked.connect(self.open_new_supplier_window)
            search_layout.addWidget(new_button)

        search_group.setLayout(search_layout)
        main_layout.addWidget(search_group)

        results_group = QGroupBox("Fornecedores Cadastrados")
        results_layout = QVBoxLayout()
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(["ID", "Razão Social", "Nome Fantasia", "CNPJ", "Telefone", "Email", "Status"])
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setColumnHidden(0, True)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        self.table_view.doubleClicked.connect(self.handle_double_click)
        results_layout.addWidget(self.table_view)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

    def load_suppliers(self):
        self.table_model.removeRows(0, self.table_model.rowCount())
        search_text = self.search_input.text()

        if search_text:
            response = self.supplier_service.search_suppliers("Nome Fantasia", search_text)
        else:
            response = self.supplier_service.get_all_suppliers()

        if response["success"]:
            for supplier in response["data"]:
                supplier_data = {
                    'ID': supplier['ID'],
                    'RAZAO_SOCIAL': _safe_str(supplier['RAZAO_SOCIAL']),
                    'NOME_FANTASIA': _safe_str(supplier['NOME_FANTASIA']),
                    'CNPJ': _safe_str(supplier['CNPJ']),
                    'TELEFONE': _safe_str(supplier['TELEFONE']),
                    'EMAIL': _safe_str(supplier['EMAIL'])
                }

                id_item = QStandardItem(str(supplier['ID']))
                id_item.setData(supplier_data, Qt.UserRole)

                row = [
                    id_item,
                    QStandardItem(supplier_data['RAZAO_SOCIAL']),
                    QStandardItem(supplier_data['NOME_FANTASIA']),
                    QStandardItem(supplier_data['CNPJ']),
                    QStandardItem(supplier_data['TELEFONE']),
                    QStandardItem(supplier_data['EMAIL']),
                    QStandardItem(supplier['STATUS'])
                ]
                self.table_model.appendRow(row)
        else:
            show_error_message(self, "Error", response["message"])

    def handle_double_click(self, model_index):
        item_data = self.table_model.item(model_index.row(), 0).data(Qt.UserRole)
        if self.selection_mode:
            self.supplier_selected.emit(item_data)
            self.close()
        else:
            self.open_edit_supplier_window(item_data['ID'])

    def open_new_supplier_window(self):
        self.show_edit_window(supplier_id=None)

    def open_edit_supplier_window(self, supplier_id):
        self.show_edit_window(supplier_id=supplier_id)

    def show_edit_window(self, supplier_id):
        if self.edit_window is None:
            self.edit_window = SupplierEditWindow(supplier_id=supplier_id)
            self.edit_window.destroyed.connect(self.on_edit_window_closed)
            self.edit_window.show()
        else:
            self.edit_window.activateWindow()
            self.edit_window.raise_()

    def on_edit_window_closed(self):
        self.edit_window = None
        self.load_suppliers()

    def search_suppliers(self, search_field, search_text):
        response = self.supplier_service.search_suppliers(search_field, search_text)
        if response["success"]:
            self.table_model.removeRows(0, self.table_model.rowCount())
            for supplier in response["data"]:
                row = [
                    QStandardItem(str(supplier['ID'])),
                    QStandardItem(supplier['RAZAO_SOCIAL']),
                    QStandardItem(supplier['NOME_FANTASIA']),
                    QStandardItem(supplier['CNPJ']),
                    QStandardItem(supplier['TELEFONE']),
                    QStandardItem(supplier['EMAIL'])
                ]
                self.table_model.appendRow(row)
        else:
            show_error_message(self, "Error", response["message"])
