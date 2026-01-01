# app/supplier/ui_search_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem, QHeaderView
from PySide6.QtCore import Qt
from .ui_supplier_window import SupplierWindow
from .supplier_repository import SupplierRepository

class SearchSupplierWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pesquisa de Fornecedores")
        self.setGeometry(100, 100, 800, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.supplier_repository = SupplierRepository()
        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_button = QPushButton("Pesquisar")
        self.search_button.clicked.connect(self.load_suppliers)
        search_layout.addWidget(QLabel("Pesquisar:"))
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_button)
        self.layout.addLayout(search_layout)

        # Supplier table
        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(6)
        self.supplier_table.setHorizontalHeaderLabels(["ID", "Nome/Razão Social", "CPF/CNPJ", "Telefone", "Cidade", "Estado"])
        self.supplier_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.supplier_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.supplier_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.supplier_table.doubleClicked.connect(self.edit_supplier)
        self.layout.addWidget(self.supplier_table)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.new_button = QPushButton("Novo")
        self.new_button.clicked.connect(self.new_supplier)
        self.edit_button = QPushButton("Editar")
        self.edit_button.clicked.connect(self.edit_supplier)
        self.delete_button = QPushButton("Excluir")
        self.delete_button.clicked.connect(self.delete_supplier)
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.edit_button)
        buttons_layout.addWidget(self.delete_button)
        self.layout.addLayout(buttons_layout)

    def load_suppliers(self):
        search_term = self.search_input.text()
        suppliers = self.supplier_repository.get_all() # Implement search logic in repository later
        self.supplier_table.setRowCount(len(suppliers))
        for row, supplier in enumerate(suppliers):
            self.supplier_table.setItem(row, 0, QTableWidgetItem(str(supplier['ID'])))
            self.supplier_table.setItem(row, 1, QTableWidgetItem(supplier['NOME_RAZAO_SOCIAL']))
            self.supplier_table.setItem(row, 2, QTableWidgetItem(supplier['CPF_CNPJ']))
            self.supplier_table.setItem(row, 3, QTableWidgetItem(supplier['TELEFONE']))
            self.supplier_table.setItem(row, 4, QTableWidgetItem(supplier['CIDADE']))
            self.supplier_table.setItem(row, 5, QTableWidgetItem(supplier['ESTADO']))

    def new_supplier(self):
        self.supplier_window = SupplierWindow()
        self.supplier_window.show()
        self.supplier_window.finished.connect(self.load_suppliers)

    def edit_supplier(self):
        selected_row = self.supplier_table.currentRow()
        if selected_row >= 0:
            supplier_id = int(self.supplier_table.item(selected_row, 0).text())
            self.supplier_window = SupplierWindow(supplier_id)
            self.supplier_window.show()
            self.supplier_window.finished.connect(self.load_suppliers)

    def delete_supplier(self):
        selected_row = self.supplier_table.currentRow()
        if selected_row >= 0:
            supplier_id = int(self.supplier_table.item(selected_row, 0).text())
            self.supplier_repository.delete(supplier_id)
            self.load_suppliers()
