# app/production_line/ui_line_edit_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem, QComboBox,
    QHeaderView, QAbstractItemView, QTextEdit
)
from PySide6.QtCore import Qt
from app.production_line import line_operations
from app.item.ui_search_window import ItemSearchWindow
from app.utils.ui_utils import NumericTableWidgetItem

class LineEditWindow(QWidget):
    def __init__(self, line_id=None, parent=None):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.parent = parent  # To refresh the list view
        self.current_line_id = line_id
        self.search_item_window = None

        self.setWindowTitle("Cadastro de Linha de Produção")
        self.setGeometry(300, 300, 600, 500)
        self.setup_ui()
        if self.current_line_id:
            self.load_line_data()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        # Form Group
        form_group = QGroupBox("Dados da Linha de Produção")
        form_layout = QFormLayout()
        self.name_input = QLineEdit()
        self.description_input = QTextEdit()
        self.status_combo = QComboBox()
        self.status_combo.addItems(["Ativa", "Inativa"])
        form_layout.addRow("Nome:", self.name_input)
        form_layout.addRow("Descrição:", self.description_input)
        form_layout.addRow("Status:", self.status_combo)
        form_group.setLayout(form_layout)
        self.main_layout.addWidget(form_group)

        # Items Group
        items_group = QGroupBox("Produtos da Linha")
        items_layout = QVBoxLayout()
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["ID Produto", "Descrição", "Quantidade", "Un."])
        self.items_table.setColumnHidden(0, True)
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        items_layout.addWidget(self.items_table)

        item_buttons_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Adicionar Produto")
        self.add_item_button.clicked.connect(self.open_item_search)
        self.remove_item_button = QPushButton("Remover Produto")
        self.remove_item_button.clicked.connect(self.remove_item)
        item_buttons_layout.addStretch()
        item_buttons_layout.addWidget(self.add_item_button)
        item_buttons_layout.addWidget(self.remove_item_button)
        items_layout.addLayout(item_buttons_layout)
        items_group.setLayout(items_layout)
        self.main_layout.addWidget(items_group)

        # Action Buttons
        action_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_line)
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.close)
        action_buttons_layout.addStretch()
        action_buttons_layout.addWidget(self.save_button)
        action_buttons_layout.addWidget(self.cancel_button)
        self.main_layout.addLayout(action_buttons_layout)

    def load_line_data(self):
        details = line_operations.get_production_line_details(self.current_line_id)
        if details:
            master = details['master']
            self.name_input.setText(master.get('NOME', ''))
            self.description_input.setPlainText(master.get('DESCRICAO', ''))
            self.status_combo.setCurrentText(master.get('STATUS', 'Ativa'))
            
            self.items_table.setRowCount(0)
            for item in details['items']:
                self.add_item_to_table(item)

    def save_line(self):
        name = self.name_input.text()
        description = self.description_input.toPlainText()
        status = self.status_combo.currentText()
        
        if not name:
            QMessageBox.warning(self, "Atenção", "O nome da linha de produção é obrigatório.")
            return

        items = []
        for row in range(self.items_table.rowCount()):
            items.append({
                'id_produto': int(self.items_table.item(row, 0).text()),
                'quantidade': float(self.items_table.item(row, 2).text())
            })

        if self.current_line_id:
            success = line_operations.update_production_line(self.current_line_id, name, description, status, items)
            message = "Linha de produção atualizada com sucesso." if success else "Falha ao atualizar a linha de produção."
        else:
            line_id = line_operations.create_production_line(name, description, status, items)
            success = line_id is not None
            message = "Linha de produção criada com sucesso." if success else "Falha ao criar a linha de produção."

        if success:
            QMessageBox.information(self, "Sucesso", message)
            if self.parent:
                self.parent.load_lines() # Refresh parent list
            self.close()
        else:
            QMessageBox.critical(self, "Erro", message)

    def open_item_search(self):
        if self.search_item_window is None:
            self.search_item_window = ItemSearchWindow(selection_mode=True, item_type_filter=['Produto', 'Ambos'])
            self.search_item_window.item_selected.connect(self.add_item_from_search)
            self.search_item_window.destroyed.connect(lambda: setattr(self, 'search_item_window', None))
            self.search_item_window.show()
        else:
            self.search_item_window.activateWindow()
            self.search_item_window.raise_()

    def add_item_from_search(self, item_data):
        item_to_add = {
            'ID_PRODUTO': item_data['ID'],
            'DESCRICAO': item_data['DESCRICAO'],
            'QUANTIDADE': 1.0, # Default quantity
            'UNIDADE': item_data['SIGLA']
        }
        self.add_item_to_table(item_to_add)

    def add_item_to_table(self, item):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        id_item = QTableWidgetItem(str(item['ID_PRODUTO']))
        desc_item = QTableWidgetItem(item['DESCRICAO'])
        qty_item = NumericTableWidgetItem(str(item['QUANTIDADE']))
        unit_item = QTableWidgetItem(item['UNIDADE'])

        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)

        self.items_table.setItem(row, 0, id_item)
        self.items_table.setItem(row, 1, desc_item)
        self.items_table.setItem(row, 2, qty_item)
        self.items_table.setItem(row, 3, unit_item)

    def remove_item(self):
        selected_rows = self.items_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Atenção", "Selecione um produto para remover.")
            return
        
        for index in sorted([idx.row() for idx in selected_rows], reverse=True):
            self.items_table.removeRow(index)
