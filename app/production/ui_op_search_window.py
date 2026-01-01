# app/production/ui_op_search_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QComboBox, QPushButton, QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QStandardItemModel, QStandardItem
from . import order_operations

class OPSearchWindow(QWidget):
    op_selected = Signal(int)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pesquisa de Ordens de Produção")
        self.setGeometry(200, 200, 800, 600)
        self.setup_ui()
        self.load_ops()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        # Search Group
        search_group = QGroupBox("Pesquisa")
        layout = QHBoxLayout()
        self.search_field = QComboBox()
        self.search_field.addItems(["ID", "Status"])
        self.search_term = QLineEdit()
        self.search_term.returnPressed.connect(self.load_ops)
        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.load_ops)
        layout.addWidget(self.search_field)
        layout.addWidget(self.search_term, 1)
        layout.addWidget(search_button)
        search_group.setLayout(layout)
        self.main_layout.addWidget(search_group)
        # Results Group
        results_group = QGroupBox("Resultados")
        layout = QVBoxLayout()
        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(["ID", "Data Criação", "Data Prevista", "Status"])
        self.table_view.setModel(self.table_model)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSortingEnabled(True)
        self.table_view.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        self.table_view.doubleClicked.connect(self.handle_double_click)
        layout.addWidget(self.table_view)
        results_group.setLayout(layout)
        self.main_layout.addWidget(results_group)

    def load_ops(self):
        self.table_model.removeRows(0, self.table_model.rowCount())
        search_term = self.search_term.text()
        search_field = self.search_field.currentText().upper()
        ops = order_operations.list_ops(search_term, search_field)
        for op in ops:
            row = [
                QStandardItem(str(op['ID'])),
                QStandardItem(op.get('DATA_CRIACAO', '')),
                QStandardItem(op.get('DATA_PREVISTA', '')),
                QStandardItem(op.get('STATUS', ''))
            ]
            self.table_model.appendRow(row)

    def handle_double_click(self, model_index):
        op_id = int(self.table_model.item(model_index.row(), 0).text())
        self.op_selected.emit(op_id)
        self.close()
