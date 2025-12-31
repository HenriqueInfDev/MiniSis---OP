# app/supplier/ui_supplier_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTableView, QHeaderView, QAbstractItemView, QMessageBox
)
from PySide6.QtGui import QStandardItemModel, QStandardItem
from ..services.supplier_service import SupplierService
from ..ui_utils import show_error_message

class SupplierWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.supplier_service = SupplierService()
        self.current_supplier_id = None
        self.setWindowTitle("Cadastro de Fornecedores")
        self.setGeometry(200, 200, 800, 600)
        self.setup_ui()
        self.load_suppliers()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        form_group = QGroupBox("Dados do Fornecedor")
        form_layout = QVBoxLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome")
        self.cnpj_input = QLineEdit()
        self.cnpj_input.setPlaceholderText("CNPJ")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Telefone")
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")

        form_layout.addWidget(self.name_input)
        form_layout.addWidget(self.cnpj_input)
        form_layout.addWidget(self.phone_input)
        form_layout.addWidget(self.email_input)

        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_supplier)
        self.new_button = QPushButton("Novo")
        self.new_button.clicked.connect(self.clear_form)
        self.delete_button = QPushButton("Excluir")
        self.delete_button.clicked.connect(self.delete_supplier)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.new_button)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.delete_button)
        form_layout.addLayout(buttons_layout)

        form_group.setLayout(form_layout)
        main_layout.addWidget(form_group)

        results_group = QGroupBox("Fornecedores Cadastrados")
        results_layout = QVBoxLayout()
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(["ID", "Nome", "CNPJ", "Telefone", "Email"])
        self.table_view.setModel(self.table_model)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setColumnHidden(0, True)
        self.table_view.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table_view.doubleClicked.connect(self.load_supplier_for_edit)
        results_layout.addWidget(self.table_view)
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)

    def load_suppliers(self):
        self.table_model.removeRows(0, self.table_model.rowCount())
        response = self.supplier_service.get_all_suppliers()
        if response["success"]:
            for supplier in response["data"]:
                row = [
                    QStandardItem(str(supplier['ID'])),
                    QStandardItem(supplier['NOME']),
                    QStandardItem(supplier['CNPJ']),
                    QStandardItem(supplier['TELEFONE']),
                    QStandardItem(supplier['EMAIL'])
                ]
                self.table_model.appendRow(row)
        else:
            show_error_message(self, response["message"])

    def save_supplier(self):
        name = self.name_input.text()
        cnpj = self.cnpj_input.text()
        phone = self.phone_input.text()
        email = self.email_input.text()

        if self.current_supplier_id:
            response = self.supplier_service.update_supplier(self.current_supplier_id, name, cnpj, phone, email)
        else:
            response = self.supplier_service.add_supplier(name, cnpj, phone, email)

        if response["success"]:
            QMessageBox.information(self, "Sucesso", response["message"])
            self.load_suppliers()
            self.clear_form()
        else:
            show_error_message(self, response["message"])

    def delete_supplier(self):
        if not self.current_supplier_id:
            show_error_message(self, "Nenhum fornecedor selecionado para excluir.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Exclusão",
            "Você tem certeza que deseja excluir este fornecedor?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            response = self.supplier_service.delete_supplier(self.current_supplier_id)
            if response["success"]:
                QMessageBox.information(self, "Sucesso", response["message"])
                self.load_suppliers()
                self.clear_form()
            else:
                show_error_message(self, response["message"])

    def load_supplier_for_edit(self, model_index):
        row = model_index.row()
        self.current_supplier_id = int(self.table_model.item(row, 0).text())
        self.name_input.setText(self.table_model.item(row, 1).text())
        self.cnpj_input.setText(self.table_model.item(row, 2).text())
        self.phone_input.setText(self.table_model.item(row, 3).text())
        self.email_input.setText(self.table_model.item(row, 4).text())

    def clear_form(self):
        self.current_supplier_id = None
        self.name_input.clear()
        self.cnpj_input.clear()
        self.phone_input.clear()
        self.email_input.clear()
