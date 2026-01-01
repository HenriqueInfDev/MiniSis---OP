# app/production/ui_order_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QHeaderView, QTableWidget, QTableWidgetItem,
    QLabel, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import QDate, Qt
from app.production import order_operations
from app.item.ui_search_window import ItemSearchWindow
from app.production.ui_op_search_window import OPSearchWindow
from app.utils.ui_utils import NumericTableWidgetItem

class ProductionOrderWindow(QWidget):
    def __init__(self, op_id=None):
        super().__init__()
        self.current_op_id = op_id
        self.search_item_window = None
        self.search_op_window = None
        self.setWindowTitle("Ordem de Produção")
        self.setGeometry(250, 250, 800, 700)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setup_ui()
        if self.current_op_id:
            self.load_op_data()
        else:
            self.new_op()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        # Header Buttons
        layout = QHBoxLayout()
        self.new_button = QPushButton("Nova OP")
        self.new_button.clicked.connect(self.new_op)
        self.save_button = QPushButton("Salvar OP")
        self.save_button.clicked.connect(self.save_op)
        self.search_button = QPushButton("Pesquisar OP...")
        self.search_button.clicked.connect(self.open_op_search)
        layout.addWidget(self.new_button)
        layout.addWidget(self.save_button)
        layout.addStretch()
        layout.addWidget(self.search_button)
        self.main_layout.addLayout(layout)
        # Main Form
        form_group = QGroupBox("Dados da Ordem de Produção")
        layout = QFormLayout()
        self.op_id_display = QLabel("(Nova)")
        self.numero_input = QLineEdit()
        self.due_date_input = QDateEdit(calendarPopup=True)
        self.due_date_input.setDate(QDate.currentDate().addDays(7))
        self.status_display = QLabel("Planejada")
        layout.addRow("ID da OP:", self.op_id_display)
        layout.addRow("Número:", self.numero_input)
        layout.addRow("Data Prevista:", self.due_date_input)
        layout.addRow("Status:", self.status_display)
        form_group.setLayout(layout)
        self.main_layout.addWidget(form_group)
        # Items Group
        items_group = QGroupBox("Produtos a Produzir")
        layout = QVBoxLayout()
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(4)
        self.items_table.setHorizontalHeaderLabels(["ID Produto", "Descrição", "Qtd a Produzir", "Un."])
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setColumnHidden(0, True)
        self.items_table.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        layout.addWidget(self.items_table)
        buttons_layout = QHBoxLayout()
        add_item_button = QPushButton("Adicionar Produto...")
        add_item_button.clicked.connect(self.open_item_search)
        remove_item_button = QPushButton("Remover Produto")
        remove_item_button.clicked.connect(self.remove_item)
        buttons_layout.addStretch()
        buttons_layout.addWidget(add_item_button)
        buttons_layout.addWidget(remove_item_button)
        layout.addLayout(buttons_layout)
        items_group.setLayout(layout)
        self.main_layout.addWidget(items_group)

    def new_op(self):
        self.current_op_id = None
        self.setWindowTitle("Nova Ordem de Produção")
        self.op_id_display.setText("(Nova)")
        self.numero_input.clear()
        self.due_date_input.setDate(QDate.currentDate().addDays(7))
        self.status_display.setText("Planejada")
        self.items_table.setRowCount(0)

    def save_op(self):
        numero = self.numero_input.text()
        due_date = self.due_date_input.date().toString("yyyy-MM-dd")
        if self.items_table.rowCount() == 0:
            QMessageBox.warning(self, "Atenção", "Adicione pelo menos um produto.")
            return
        items = [{'id_produto': int(self.items_table.item(r, 0).text()),
                  'quantidade': float(self.items_table.item(r, 2).text())}
                 for r in range(self.items_table.rowCount())]
        if self.current_op_id:
            if order_operations.update_op(self.current_op_id, numero, due_date, items):
                QMessageBox.information(self, "Sucesso", "Ordem de Produção atualizada.")
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível atualizar a Ordem de Produção.")
        else:
            new_id = order_operations.create_op(numero, due_date, items)
            if new_id:
                self.current_op_id = new_id
                self.setWindowTitle(f"Editando Ordem de Produção #{new_id}")
                self.op_id_display.setText(str(new_id))
                QMessageBox.information(self, "Sucesso", f"Ordem de Produção #{new_id} criada.")
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível criar a Ordem de Produção.")

    def load_op_data(self):
        if not self.current_op_id: return
        details = order_operations.get_op_details(self.current_op_id)
        if details:
            master = details['master']
            self.setWindowTitle(f"Editando Ordem de Produção #{self.current_op_id}")
            self.op_id_display.setText(str(master['ID']))
            self.numero_input.setText(master.get('NUMERO', ''))
            self.status_display.setText(master.get('STATUS', ''))
            if master.get('DATA_PREVISTA'):
                self.due_date_input.setDate(QDate.fromString(master['DATA_PREVISTA'], "yyyy-MM-dd"))
            self.items_table.setRowCount(0)
            for item in details['items']:
                self.add_item_to_table(item)

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
        for row in range(self.items_table.rowCount()):
            if int(self.items_table.item(row, 0).text()) == item_data['ID']:
                QMessageBox.information(self, "Atenção", "Este produto já está na lista.")
                return
        item_data['ID_PRODUTO'] = item_data['ID']
        item_data['QUANTIDADE_PRODUZIR'] = 1.0
        item_data['UNIDADE'] = item_data['SIGLA']
        self.add_item_to_table(item_data)

    def add_item_to_table(self, item):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        id_item = NumericTableWidgetItem(str(item['ID_PRODUTO']))
        desc_item = QTableWidgetItem(item['DESCRICAO'])
        qty_item = NumericTableWidgetItem(str(item['QUANTIDADE_PRODUZIR']))
        unit_item = QTableWidgetItem(item['UNIDADE'].upper())

        # Apenas a célula de quantidade deve ser editável
        id_item.setFlags(id_item.flags() & ~Qt.ItemIsEditable)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)

        self.items_table.setItem(row, 0, id_item)
        self.items_table.setItem(row, 1, desc_item)
        self.items_table.setItem(row, 2, qty_item)
        self.items_table.setItem(row, 3, unit_item)

    def remove_item(self):
        rows = self.items_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Atenção", "Selecione um produto para remover.")
            return
        for index in sorted([idx.row() for idx in rows], reverse=True):
            self.items_table.removeRow(index)

    def open_op_search(self):
        if self.search_op_window is None:
            self.search_op_window = OPSearchWindow()
            self.search_op_window.op_selected.connect(self.load_op_by_id)
            self.search_op_window.destroyed.connect(lambda: setattr(self, 'search_op_window', None))
            self.search_op_window.show()
        else:
            self.search_op_window.activateWindow()
            self.search_op_window.raise_()

    def load_op_by_id(self, op_id):
        self.current_op_id = op_id
        self.load_op_data()
