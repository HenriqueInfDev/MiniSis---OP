# app/supplier/ui_edit_window.py
import requests
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QPushButton, QTabWidget, QFormLayout, QMessageBox
)
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from app.supplier.service import SupplierService
from app.utils.ui_utils import show_error_message

class SupplierEditWindow(QWidget):
    def __init__(self, supplier_id=None):
        super().__init__()
        self.supplier_service = SupplierService()
        self.current_supplier_id = supplier_id

        title = f"Editando Fornecedor #{supplier_id}" if supplier_id else "Novo Fornecedor"
        self.setWindowTitle(title)
        self.setGeometry(250, 250, 600, 400)
        self.setup_ui()

        if self.current_supplier_id:
            self.load_supplier_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.new_button = QPushButton("Novo")
        self.new_button.clicked.connect(self.clear_form)
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_supplier)
        self.delete_button = QPushButton("Excluir")
        self.delete_button.clicked.connect(self.delete_supplier)
        header_layout.addStretch()
        header_layout.addWidget(self.new_button)
        header_layout.addWidget(self.save_button)
        header_layout.addWidget(self.delete_button)
        main_layout.addLayout(header_layout)

        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        self.setup_identification_tab()
        self.setup_address_tab()

    def setup_identification_tab(self):
        ident_widget = QWidget()
        layout = QFormLayout(ident_widget)
        self.razao_social_input = QLineEdit()
        self.nome_fantasia_input = QLineEdit()

        self.cnpj_input = QLineEdit()
        self.cnpj_input.setValidator(QRegularExpressionValidator(QRegularExpression("[0-9./-]+")))
        self.cnpj_input.textChanged.connect(self.format_cnpj_cpf)

        self.phone_input = QLineEdit()
        self.phone_input.textChanged.connect(self.format_phone_number)

        self.email_input = QLineEdit()

        self.status_combo = QComboBox()
        self.status_combo.addItems(["Ativo", "Inativo"])

        layout.addRow("Razão Social:", self.razao_social_input)
        layout.addRow("Nome Fantasia:", self.nome_fantasia_input)
        layout.addRow("Status:", self.status_combo)
        layout.addRow("CPF/CNPJ:", self.cnpj_input)
        layout.addRow("Telefone:", self.phone_input)
        layout.addRow("Email:", self.email_input)
        self.tab_widget.addTab(ident_widget, "Identificação")

    def setup_address_tab(self):
        address_widget = QWidget()
        layout = QFormLayout(address_widget)
        self.cep_input = QLineEdit()
        self.cep_input.setInputMask("00000-000")
        self.cep_input.editingFinished.connect(self.fetch_address_from_cep)

        self.logradouro_input = QLineEdit()
        self.numero_input = QLineEdit()
        self.complemento_input = QLineEdit()
        self.bairro_input = QLineEdit()
        self.cidade_input = QLineEdit()

        self.uf_input = QLineEdit()
        self.uf_input.setInputMask("AA")

        layout.addRow("CEP:", self.cep_input)
        layout.addRow("Logradouro:", self.logradouro_input)
        layout.addRow("Número:", self.numero_input)
        layout.addRow("Complemento:", self.complemento_input)
        layout.addRow("Bairro:", self.bairro_input)
        layout.addRow("Cidade:", self.cidade_input)
        layout.addRow("UF:", self.uf_input)
        self.tab_widget.addTab(address_widget, "Endereço")

    def format_cnpj_cpf(self, text):
        cleaned_text = ''.join(filter(str.isdigit, text))

        self.cnpj_input.blockSignals(True)

        if len(cleaned_text) <= 11:
            if len(cleaned_text) > 9:
                formatted_text = f"{cleaned_text[:3]}.{cleaned_text[3:6]}.{cleaned_text[6:9]}-{cleaned_text[9:]}"
            elif len(cleaned_text) > 6:
                formatted_text = f"{cleaned_text[:3]}.{cleaned_text[3:6]}.{cleaned_text[6:]}"
            elif len(cleaned_text) > 3:
                formatted_text = f"{cleaned_text[:3]}.{cleaned_text[3:]}"
            else:
                formatted_text = cleaned_text
        else:
            if len(cleaned_text) > 12:
                formatted_text = f"{cleaned_text[:2]}.{cleaned_text[2:5]}.{cleaned_text[5:8]}/{cleaned_text[8:12]}-{cleaned_text[12:]}"
            elif len(cleaned_text) > 8:
                formatted_text = f"{cleaned_text[:2]}.{cleaned_text[2:5]}.{cleaned_text[5:8]}/{cleaned_text[8:]}"
            elif len(cleaned_text) > 5:
                formatted_text = f"{cleaned_text[:2]}.{cleaned_text[2:5]}.{cleaned_text[5:]}"
            elif len(cleaned_text) > 2:
                formatted_text = f"{cleaned_text[:2]}.{cleaned_text[2:]}"
            else:
                formatted_text = cleaned_text

        self.cnpj_input.setText(formatted_text)
        self.cnpj_input.setCursorPosition(len(formatted_text))
        self.cnpj_input.blockSignals(False)

    def format_phone_number(self, text):
        cleaned_text = ''.join(filter(str.isdigit, text))

        self.phone_input.blockSignals(True)

        if len(cleaned_text) <= 10:
            if len(cleaned_text) > 6:
                formatted_text = f"({cleaned_text[:2]}) {cleaned_text[2:6]}-{cleaned_text[6:]}"
            elif len(cleaned_text) > 2:
                formatted_text = f"({cleaned_text[:2]}) {cleaned_text[2:]}"
            else:
                formatted_text = cleaned_text
        else:
            if len(cleaned_text) > 7:
                formatted_text = f"({cleaned_text[:2]}) {cleaned_text[2:7]}-{cleaned_text[7:]}"
            elif len(cleaned_text) > 2:
                formatted_text = f"({cleaned_text[:2]}) {cleaned_text[2:]}"
            else:
                formatted_text = cleaned_text

        self.phone_input.setText(formatted_text)
        self.phone_input.setCursorPosition(len(formatted_text))
        self.phone_input.blockSignals(False)

    def fetch_address_from_cep(self):
        cep = self.cep_input.text().replace("-", "").strip()
        if len(cep) == 8:
            try:
                response = requests.get(f"https://viacep.com.br/ws/{cep}/json/")
                if response.status_code == 200:
                    data = response.json()
                    if not data.get("erro"):
                        self.logradouro_input.setText(data.get("logradouro", ""))
                        self.bairro_input.setText(data.get("bairro", ""))
                        self.cidade_input.setText(data.get("localidade", ""))
                        self.uf_input.setText(data.get("uf", ""))
                        self.numero_input.setFocus()
            except requests.RequestException:
                show_error_message(self, "Error", "Não foi possível buscar o CEP. Verifique sua conexão com a internet.")

    def load_supplier_data(self):
        response = self.supplier_service.get_supplier_by_id(self.current_supplier_id)
        if response["success"]:
            supplier = response["data"]
            self.razao_social_input.setText(supplier['RAZAO_SOCIAL'])
            self.nome_fantasia_input.setText(supplier['NOME_FANTASIA'])
            self.status_combo.setCurrentText(supplier['STATUS'])
            self.cnpj_input.setText(supplier['CNPJ'])
            self.phone_input.setText(supplier['TELEFONE'])
            self.email_input.setText(supplier['EMAIL'])
            self.logradouro_input.setText(supplier['LOGRADOURO'])
            self.numero_input.setText(supplier['NUMERO'])
            self.complemento_input.setText(supplier['COMPLEMENTO'])
            self.bairro_input.setText(supplier['BAIRRO'])
            self.cidade_input.setText(supplier['CIDADE'])
            self.uf_input.setText(supplier['UF'])
            self.cep_input.setText(supplier['CEP'])
        else:
            show_error_message(self, "Error", response["message"])

    def save_supplier(self):
        razao_social = self.razao_social_input.text()
        nome_fantasia = self.nome_fantasia_input.text()
        status = self.status_combo.currentText()
        cnpj = self.cnpj_input.text()
        phone = self.phone_input.text()
        email = self.email_input.text()
        address = {
            'logradouro': self.logradouro_input.text(),
            'numero': self.numero_input.text(),
            'complemento': self.complemento_input.text(),
            'bairro': self.bairro_input.text(),
            'cidade': self.cidade_input.text(),
            'uf': self.uf_input.text(),
            'cep': self.cep_input.text()
        }

        if self.current_supplier_id:
            response = self.supplier_service.update_supplier(self.current_supplier_id, razao_social, nome_fantasia, cnpj, phone, email, address, status)
        else:
            response = self.supplier_service.add_supplier(razao_social, nome_fantasia, cnpj, phone, email, address, status)

        if response["success"]:
            QMessageBox.information(self, "Sucesso", response["message"])
            if not self.current_supplier_id and response.get("data"):
                self.current_supplier_id = response["data"]
                self.setWindowTitle(f"Editando Fornecedor #{self.current_supplier_id}")
        else:
            show_error_message(self, "Error", response["message"])

    def delete_supplier(self):
        if not self.current_supplier_id:
            show_error_message(self, "Error", "Nenhum fornecedor carregado para excluir.")
            return

        reply = QMessageBox.question(self, "Confirmar Exclusão", "Tem certeza que deseja excluir este fornecedor?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            response = self.supplier_service.delete_supplier(self.current_supplier_id)
            if response["success"]:
                QMessageBox.information(self, "Sucesso", response["message"])
                self.close()
            else:
                show_error_message(self, "Error", response["message"])

    def clear_form(self):
        self.current_supplier_id = None
        self.setWindowTitle("Novo Fornecedor")
        for widget in self.findChildren(QLineEdit):
            widget.clear()
        self.tab_widget.setCurrentIndex(0)
