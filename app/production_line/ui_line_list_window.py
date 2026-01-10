# app/production_line/ui_line_list_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt
from app.production_line import line_operations
from app.production_line.ui_line_edit_window import LineEditWindow
from app.production.ui_order_window import ProductionOrderWindow
from app.production import order_operations

class LineListWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.edit_window = None
        self.order_window = None
        self.setWindowTitle("Linhas de Produção")
        self.setGeometry(200, 200, 700, 500)
        self.setup_ui()
        self.load_lines()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)
        
        # Action Buttons
        action_layout = QHBoxLayout()
        self.new_button = QPushButton("Nova Linha")
        self.new_button.clicked.connect(self.open_edit_window)
        self.edit_button = QPushButton("Editar Linha")
        self.edit_button.clicked.connect(self.open_edit_window_for_selected)
        self.delete_button = QPushButton("Excluir Linha")
        self.delete_button.clicked.connect(self.delete_selected_line)
        self.produce_button = QPushButton("Produzir")
        self.produce_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.produce_button.clicked.connect(self.produce_from_selected_line)
        
        action_layout.addWidget(self.new_button)
        action_layout.addWidget(self.edit_button)
        action_layout.addWidget(self.delete_button)
        action_layout.addStretch()
        action_layout.addWidget(self.produce_button)
        self.main_layout.addLayout(action_layout)

        # Production Lines Table
        self.lines_table = QTableWidget()
        self.lines_table.setColumnCount(4)
        self.lines_table.setHorizontalHeaderLabels(["ID", "Nome", "Qtd. Produtos", "Status"])
        self.lines_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.lines_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.lines_table.verticalHeader().setVisible(False)
        self.lines_table.setColumnHidden(0, True)
        header = self.lines_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.main_layout.addWidget(self.lines_table)

    def load_lines(self):
        self.lines_table.setRowCount(0)
        lines = line_operations.get_all_production_lines()
        for line in lines:
            row = self.lines_table.rowCount()
            self.lines_table.insertRow(row)
            self.lines_table.setItem(row, 0, QTableWidgetItem(str(line['ID'])))
            self.lines_table.setItem(row, 1, QTableWidgetItem(line['NOME']))
            self.lines_table.setItem(row, 2, QTableWidgetItem(str(line['QTD_PRODUTOS'])))
            self.lines_table.setItem(row, 3, QTableWidgetItem(line['STATUS']))
            # Style inactive lines
            if line['STATUS'] == 'Inativa':
                for col in range(self.lines_table.columnCount()):
                    self.lines_table.item(row, col).setForeground(Qt.gray)

    def open_edit_window(self):
        if self.edit_window is None:
            self.edit_window = LineEditWindow(parent=self)
            self.edit_window.destroyed.connect(lambda: setattr(self, 'edit_window', None))
            self.edit_window.show()
        else:
            self.edit_window.activateWindow()

    def open_edit_window_for_selected(self):
        selected_row = self.lines_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma linha de produção para editar.")
            return
        line_id = int(self.lines_table.item(selected_row, 0).text())
        if self.edit_window is None:
            self.edit_window = LineEditWindow(line_id=line_id, parent=self)
            self.edit_window.destroyed.connect(lambda: setattr(self, 'edit_window', None))
            self.edit_window.show()
        else:
            self.edit_window.activateWindow()

    def delete_selected_line(self):
        selected_row = self.lines_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma linha de produção para excluir.")
            return
        line_id = int(self.lines_table.item(selected_row, 0).text())
        line_name = self.lines_table.item(selected_row, 1).text()

        reply = QMessageBox.question(
            self, 'Confirmar Exclusão',
            f"Tem certeza que deseja excluir a linha de produção '{line_name}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if line_operations.delete_production_line(line_id):
                QMessageBox.information(self, "Sucesso", "Linha de produção excluída.")
                self.load_lines()
            else:
                QMessageBox.critical(self, "Erro", "Não foi possível excluir a linha de produção.")

    def produce_from_selected_line(self):
        selected_row = self.lines_table.currentRow()
        if selected_row < 0:
            QMessageBox.warning(self, "Atenção", "Selecione uma linha de produção para iniciar a produção.")
            return

        line_id = int(self.lines_table.item(selected_row, 0).text())
        status = self.lines_table.item(selected_row, 3).text()

        if status == 'Inativa':
            QMessageBox.warning(self, "Atenção", "Não é possível iniciar a produção a partir de uma linha inativa.")
            return

        line_details = line_operations.get_production_line_details(line_id)
        if not line_details or not line_details['items']:
            QMessageBox.warning(self, "Atenção", "Esta linha de produção não tem produtos para produzir.")
            return

        items_to_produce = [
            {'id_produto': item['ID_PRODUTO'], 'quantidade': item['QUANTIDADE']}
            for item in line_details['items']
        ]
        
        numero_op = f"LP-{line_id}-{self.lines_table.item(selected_row, 1).text()}"

        new_op_id = order_operations.create_op(numero_op, None, items_to_produce, id_linha_producao=line_id)
        
        if new_op_id:
            QMessageBox.information(self, "Ordem de Produção Criada", f"Ordem de Produção #{new_op_id} foi criada. Por favor, revise e finalize.")
            if self.order_window is None:
                self.order_window = ProductionOrderWindow(op_id=new_op_id)
                self.order_window.destroyed.connect(lambda: setattr(self, 'order_window', None))
                self.order_window.show()
            else:
                self.order_window.load_op_by_id(new_op_id)
                self.order_window.activateWindow()
        else:
            QMessageBox.critical(self, "Erro", "Falha ao criar a Ordem de Produção a partir da linha selecionada.")
