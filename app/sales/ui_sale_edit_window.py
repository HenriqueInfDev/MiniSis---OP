# app/sales/ui_sale_edit_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QHeaderView, QTableWidget, QTableWidgetItem,
    QLabel, QDateEdit, QAbstractItemView
)
from PySide6.QtCore import QDate, Qt
from app.sales.sale_service import SaleService
from app.item.ui_search_window import ItemSearchWindow
from app.utils.ui_utils import NumericTableWidgetItem, show_error_message

class SaleEditWindow(QWidget):
    def __init__(self, sale_id=None):
        super().__init__()
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.sale_service = SaleService()
        self.current_sale_id = sale_id
        self.search_item_window = None

        title = f"Editando Saída #{sale_id}" if sale_id else "Nova Saída de Produto"
        self.setWindowTitle(title)
        self.setGeometry(250, 250, 800, 600)
        self.setup_ui()

        if self.current_sale_id:
            self.load_sale_data()
        else:
            self.new_sale()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_sale)
        self.finalize_button = QPushButton("Finalizar Saída")
        self.finalize_button.clicked.connect(self.finalize_sale)
        header_layout.addStretch()
        header_layout.addWidget(self.save_button)
        header_layout.addWidget(self.finalize_button)
        self.main_layout.addLayout(header_layout)

        form_group = QGroupBox("Dados da Saída")
        form = QFormLayout()
        self.sale_id_display = QLabel("(Nova)")
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        self.observacao_input = QLineEdit()
        self.status_display = QLabel("Em Aberto")

        form.addRow("ID da Saída:", self.sale_id_display)
        form.addRow("Data da Saída:", self.date_input)
        form.addRow("Observação:", self.observacao_input)
        form.addRow("Status:", self.status_display)
        form_group.setLayout(form)
        self.main_layout.addWidget(form_group)

        items_group = QGroupBox("Produtos da Saída")
        items_layout = QVBoxLayout()
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["ID Produto", "Descrição", "Un.", "Quantidade", "Valor Venda", "Valor Total"])
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setColumnHidden(0, True)
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)

        self.items_table.cellChanged.connect(self.on_cell_changed)
        items_layout.addWidget(self.items_table)

        buttons_layout = QHBoxLayout()
        self.total_label = QLabel("Valor Total da Saída: R$ 0.00")
        buttons_layout.addWidget(self.total_label)
        buttons_layout.addStretch()
        self.add_item_button = QPushButton("Adicionar Produto")
        self.add_item_button.clicked.connect(self.open_item_search)
        self.remove_item_button = QPushButton("Remover Produto")
        self.remove_item_button.clicked.connect(self.remove_item)
        buttons_layout.addWidget(self.add_item_button)
        buttons_layout.addWidget(self.remove_item_button)
        items_layout.addLayout(buttons_layout)

        items_group.setLayout(items_layout)
        self.main_layout.addWidget(items_group)

    def new_sale(self):
        self.current_sale_id = None
        self.setWindowTitle("Nova Saída de Produto")
        self.sale_id_display.setText("(Nova)")
        self.date_input.setDate(QDate.currentDate())
        self.observacao_input.clear()
        self.status_display.setText("Em Aberto")
        self.items_table.setRowCount(0)
        self.update_total_value()
        self.set_read_only(False)

    def save_sale(self):
        sale_date = self.date_input.date().toString("yyyy-MM-dd")
        observacao = self.observacao_input.text()

        items = []
        for row in range(self.items_table.rowCount()):
            items.append({
                'id_produto': int(self.items_table.item(row, 0).text()),
                'quantidade': float(self.items_table.item(row, 3).text().replace(',', '.')),
                'valor_unitario': float(self.items_table.item(row, 4).text().replace(',', '.'))
            })

        if self.current_sale_id:
            response = self.sale_service.update_sale(self.current_sale_id, sale_date, observacao, items)
        else:
            response = self.sale_service.create_sale(sale_date, observacao, items)
            if response["success"]:
                self.current_sale_id = response["data"]
                self.setWindowTitle(f"Editando Saída #{self.current_sale_id}")
                self.sale_id_display.setText(str(self.current_sale_id))

        if response["success"]:
            QMessageBox.information(self, "Sucesso", response["message"])
        else:
            show_error_message(self, "Erro", response["message"])

    def load_sale_data(self):
        response = self.sale_service.get_sale_details(self.current_sale_id)
        if not response["success"]:
            show_error_message(self, "Erro", response["message"])
            self.close()
            return

        details = response["data"]
        master = details['master']
        self.sale_id_display.setText(str(master['ID']))
        self.date_input.setDate(QDate.fromString(master['DATA_SAIDA'], "yyyy-MM-dd"))
        self.observacao_input.setText(master.get('OBSERVACAO', ''))
        self.status_display.setText(master.get('STATUS', ''))

        self.items_table.setRowCount(0)
        for item in details['items']:
            self.add_item_to_table(item)

        self.update_total_value()
        if master.get('STATUS') == 'Finalizada':
            self.set_read_only(True)

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
                QMessageBox.warning(self, "Atenção", "Este produto já está na lista.")
                return

        item_to_add = {
            'ID_PRODUTO': item_data['ID'],
            'DESCRICAO': item_data['DESCRICAO'],
            'SIGLA': item_data['SIGLA'],
            'QUANTIDADE': 1.0,
            'VALOR_UNITARIO': 0.0
        }
        self.add_item_to_table(item_to_add)

    def add_item_to_table(self, item):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        self.items_table.setItem(row, 0, QTableWidgetItem(str(item['ID_PRODUTO'])))
        self.items_table.setItem(row, 1, QTableWidgetItem(item['DESCRICAO']))
        self.items_table.setItem(row, 2, QTableWidgetItem(item['SIGLA'].upper()))
        self.items_table.setItem(row, 3, NumericTableWidgetItem(str(item['QUANTIDADE'])))
        self.items_table.setItem(row, 4, NumericTableWidgetItem(f"{item['VALOR_UNITARIO']:.2f}"))
        total = item['QUANTIDADE'] * item['VALOR_UNITARIO']
        self.items_table.setItem(row, 5, NumericTableWidgetItem(f"{total:.2f}"))

        for col in [0, 1, 2]:
            self.items_table.item(row, col).setFlags(self.items_table.item(row, col).flags() & ~Qt.ItemIsEditable)

    def remove_item(self):
        rows = self.items_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Atenção", "Selecione um produto para remover.")
            return
        for index in sorted([r.row() for r in rows], reverse=True):
            self.items_table.removeRow(index)
        self.update_total_value()

    def on_cell_changed(self, row, column):
        if column not in [3, 4, 5]:  # Quantidade, Valor Venda, Valor Total
            return

        self.items_table.blockSignals(True)
        try:
            qty_item = self.items_table.item(row, 3)
            unit_price_item = self.items_table.item(row, 4)
            total_price_item = self.items_table.item(row, 5)

            qty = float(qty_item.text().replace(',', '.'))

            if column == 3 or column == 4:
                unit_price = float(unit_price_item.text().replace(',', '.'))
                total_price_item.setText(f"{qty * unit_price:.2f}")
            elif column == 5:
                total_price = float(total_price_item.text().replace(',', '.'))
                if qty > 0:
                    unit_price_item.setText(f"{total_price / qty:.2f}")
                else:
                    unit_price_item.setText("0.00")
        except (ValueError, ZeroDivisionError) as e:
             print(f"Error in on_cell_changed: {e}")
        finally:
            self.items_table.blockSignals(False)
        self.update_total_value()

    def update_total_value(self):
        total = 0.0
        for row in range(self.items_table.rowCount()):
            total_item = self.items_table.item(row, 5)
            if total_item and total_item.text():
                total += float(total_item.text().replace(',', '.'))
        self.total_label.setText(f"Valor Total da Saída: R$ {total:.2f}")

    def set_read_only(self, read_only):
        self.date_input.setReadOnly(read_only)
        self.observacao_input.setReadOnly(read_only)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers if read_only else QAbstractItemView.AllEditTriggers)
        self.save_button.setDisabled(read_only)
        self.finalize_button.setDisabled(read_only)
        self.add_item_button.setDisabled(read_only)
        self.remove_item_button.setDisabled(read_only)

    def finalize_sale(self):
        if not self.current_sale_id:
            show_error_message(self, "Erro", "Salve a saída antes de finalizá-la.")
            return

        reply = QMessageBox.question(self, "Confirmar Finalização",
                                     "Você tem certeza que deseja finalizar esta saída?\nEsta ação atualizará o estoque e não poderá ser desfeita.",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if reply == QMessageBox.Yes:
            self.save_sale()
            response = self.sale_service.finalize_sale(self.current_sale_id)
            if response["success"]:
                QMessageBox.information(self, "Sucesso", response["message"])
                self.load_sale_data()
            else:
                show_error_message(self, "Erro", response["message"])
