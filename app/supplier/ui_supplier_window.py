# app/supplier/ui_supplier_window.py
from PySide6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox, QMessageBox
from PySide6.QtCore import Qt, Signal
from .supplier_repository import SupplierRepository

class SupplierWindow(QMainWindow):
    finished = Signal()

    def __init__(self, supplier_id=None):
        super().__init__()
        self.supplier_id = supplier_id
        self.supplier_repository = SupplierRepository()
        self.setWindowTitle("Cadastro de Fornecedor")
        self.setGeometry(100, 100, 800, 600)
        self.setAttribute(Qt.WA_DeleteOnClose)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.setup_ui()
        if self.supplier_id:
            self.load_supplier_data()

    def setup_ui(self):
        # Tipo de Pessoa (Física/Jurídica)
        self.tipo_pessoa_combo = QComboBox()
        self.tipo_pessoa_combo.addItems(["Física", "Jurídica"])
        self.tipo_pessoa_combo.currentIndexChanged.connect(self.update_document_mask)
        self.layout.addWidget(QLabel("Tipo de Pessoa:"))
        self.layout.addWidget(self.tipo_pessoa_combo)

        # CPF/CNPJ
        self.cpf_cnpj_edit = QLineEdit()
        self.layout.addWidget(QLabel("CPF/CNPJ:"))
        self.layout.addWidget(self.cpf_cnpj_edit)

        # Nome/Razão Social
        self.nome_razao_social_edit = QLineEdit()
        self.layout.addWidget(QLabel("Nome/Razão Social:"))
        self.layout.addWidget(self.nome_razao_social_edit)

        # Telefone
        self.telefone_edit = QLineEdit()
        self.telefone_edit.setInputMask("(99) 99999-9999")
        self.layout.addWidget(QLabel("Telefone:"))
        self.layout.addWidget(self.telefone_edit)

        # Email
        self.email_edit = QLineEdit()
        self.layout.addWidget(QLabel("Email:"))
        self.layout.addWidget(self.email_edit)

        # Endereço
        self.cep_edit = QLineEdit()
        self.cep_edit.setInputMask("99999-999")
        self.endereco_edit = QLineEdit()
        self.numero_edit = QLineEdit()
        self.complemento_edit = QLineEdit()
        self.bairro_edit = QLineEdit()
        self.cidade_edit = QLineEdit()
        self.estado_edit = QLineEdit()

        self.layout.addWidget(QLabel("CEP:"))
        self.layout.addWidget(self.cep_edit)
        self.layout.addWidget(QLabel("Endereço:"))
        self.layout.addWidget(self.endereco_edit)
        self.layout.addWidget(QLabel("Número:"))
        self.layout.addWidget(self.numero_edit)
        self.layout.addWidget(QLabel("Complemento:"))
        self.layout.addWidget(self.complemento_edit)
        self.layout.addWidget(QLabel("Bairro:"))
        self.layout.addWidget(self.bairro_edit)
        self.layout.addWidget(QLabel("Cidade:"))
        self.layout.addWidget(self.cidade_edit)
        self.layout.addWidget(QLabel("Estado:"))
        self.layout.addWidget(self.estado_edit)

        # Botões
        buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_supplier)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.close)
        buttons_layout.addWidget(self.save_button)
        buttons_layout.addWidget(self.cancel_button)
        self.layout.addLayout(buttons_layout)

        self.update_document_mask()

    def update_document_mask(self):
        if self.tipo_pessoa_combo.currentText() == "Física":
            self.cpf_cnpj_edit.setInputMask("999.999.999-99")
        else:
            self.cpf_cnpj_edit.setInputMask("99.999.999/9999-99")

    def load_supplier_data(self):
        supplier = self.supplier_repository.get_by_id(self.supplier_id)
        if supplier:
            self.tipo_pessoa_combo.setCurrentText(supplier['TIPO_PESSOA'])
            self.cpf_cnpj_edit.setText(supplier['CPF_CNPJ'])
            self.nome_razao_social_edit.setText(supplier['NOME_RAZAO_SOCIAL'])
            self.telefone_edit.setText(supplier['TELEFONE'])
            self.email_edit.setText(supplier['EMAIL'])
            self.cep_edit.setText(supplier['CEP'])
            self.endereco_edit.setText(supplier['ENDERECO'])
            self.numero_edit.setText(supplier['NUMERO'])
            self.complemento_edit.setText(supplier['COMPLEMENTO'])
            self.bairro_edit.setText(supplier['BAIRRO'])
            self.cidade_edit.setText(supplier['CIDADE'])
            self.estado_edit.setText(supplier['ESTADO'])

    def save_supplier(self):
        supplier_data = {
            'tipo_pessoa': self.tipo_pessoa_combo.currentText(),
            'cpf_cnpj': self.cpf_cnpj_edit.text(),
            'nome_razao_social': self.nome_razao_social_edit.text(),
            'telefone': self.telefone_edit.text(),
            'email': self.email_edit.text(),
            'cep': self.cep_edit.text(),
            'endereco': self.endereco_edit.text(),
            'numero': self.numero_edit.text(),
            'complemento': self.complemento_edit.text(),
            'bairro': self.bairro_edit.text(),
            'cidade': self.cidade_edit.text(),
            'estado': self.estado_edit.text()
        }

        if self.supplier_id:
            self.supplier_repository.update(self.supplier_id, supplier_data)
        else:
            self.supplier_repository.add(supplier_data)

        QMessageBox.information(self, "Sucesso", "Fornecedor salvo com sucesso!")
        self.finished.emit()
        self.close()
