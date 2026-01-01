# app/stock/ui_entry_edit_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QPushButton, QMessageBox, QHeaderView, QTableWidget, QTableWidgetItem,
    QLabel, QDateEdit, QAbstractItemView, QDateTimeEdit
)
from PySide6.QtCore import QDate, Qt, QDateTime
from app.stock.service import StockService
from app.supplier.service import SupplierService
from app.item.ui_search_window import ItemSearchWindow
from app.supplier.ui_search_window import SupplierSearchWindow
from app.utils.ui_utils import NumericTableWidgetItem, show_error_message

class EntryEditWindow(QWidget):
    def __init__(self, entry_id=None):
        super().__init__()
        self.stock_service = StockService()
        self.supplier_service = SupplierService()
        self.current_entry_id = entry_id
        self.selected_supplier_id = None
        self.search_item_window = None
        self.search_supplier_window = None

        title = f"Editando Entrada #{entry_id}" if entry_id else "Nova Entrada de Insumo"
        self.setWindowTitle(title)
        self.setGeometry(250, 250, 800, 700)
        self.setup_ui()

        if self.current_entry_id:
            self.load_entry_data()
        else:
            self.new_entry()

    def setup_ui(self):
        self.main_layout = QVBoxLayout(self)

        header_layout = QHBoxLayout()
        self.save_button = QPushButton("Salvar")
        self.save_button.clicked.connect(self.save_entry)
        self.finalize_button = QPushButton("Finalizar Entrada")
        self.finalize_button.clicked.connect(self.finalize_entry)
        header_layout.addStretch()
        header_layout.addWidget(self.save_button)
        header_layout.addWidget(self.finalize_button)
        self.main_layout.addLayout(header_layout)

        form_group = QGroupBox("Dados da Nota de Entrada")
        form = QFormLayout()
        self.entry_id_display = QLabel("(Nova)")
        self.date_input = QDateEdit(calendarPopup=True)
        self.date_input.setDate(QDate.currentDate())
        self.typing_date_input = QDateTimeEdit()
        self.typing_date_input.setDateTime(QDateTime.currentDateTime())
        self.typing_date_input.setCalendarPopup(True)

        supplier_layout = QHBoxLayout()
        self.supplier_display = QLineEdit()
        self.supplier_display.setReadOnly(True)
        self.supplier_display.setPlaceholderText("Selecione um fornecedor...")
        search_supplier_button = QPushButton("Buscar...")
        search_supplier_button.clicked.connect(self.open_supplier_search)
        supplier_layout.addWidget(self.supplier_display)
        supplier_layout.addWidget(search_supplier_button)

        self.note_number_input = QLineEdit()
        self.observacao_input = QLineEdit()
        self.status_display = QLabel("Em Aberto")

        self.data_input = QDateEdit(calendarPopup=True)
        self.data_input.setDate(QDate.currentDate())

        form.addRow("ID da Entrada:", self.entry_id_display)
        form.addRow("Data:", self.data_input)
        form.addRow("Data da Entrada:", self.date_input)
        form.addRow("Data de Digitação:", self.typing_date_input)
        form.addRow("Fornecedor:", supplier_layout)
        form.addRow("Número da Nota:", self.note_number_input)
        form.addRow("Observação:", self.observacao_input)
        form.addRow("Status:", self.status_display)
        form_group.setLayout(form)
        self.main_layout.addWidget(form_group)

        items_group = QGroupBox("Insumos da Nota")
        items_layout = QVBoxLayout()
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels(["ID Insumo", "Descrição", "Un.", "Quantidade", "Valor Unit.", "Valor Total"])
        self.items_table.verticalHeader().setVisible(False)
        self.items_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.items_table.setColumnHidden(0, True)
        self.items_table.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        header = self.items_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.items_table.cellChanged.connect(self.on_cell_changed)
        items_layout.addWidget(self.items_table)

        buttons_layout = QHBoxLayout()
        self.add_item_button = QPushButton("Adicionar Insumo...")
        self.add_item_button.setObjectName("add_item_button")
        self.add_item_button.clicked.connect(self.open_item_search)
        self.remove_item_button = QPushButton("Remover Insumo")
        self.remove_item_button.setObjectName("remove_item_button")
        self.remove_item_button.clicked.connect(self.remove_item)
        buttons_layout.addStretch()
        buttons_layout.addWidget(self.add_item_button)
        buttons_layout.addWidget(self.remove_item_button)
        items_layout.addLayout(buttons_layout)

        items_group.setLayout(items_layout)
        self.main_layout.addWidget(items_group)

    def new_entry(self):
        self.current_entry_id = None
        self.selected_supplier_id = None
        self.setWindowTitle("Nova Entrada de Insumo")
        self.entry_id_display.setText("(Nova)")
        self.data_input.setDate(QDate.currentDate())
        self.date_input.setDate(QDate.currentDate())
        self.typing_date_input.setDateTime(QDateTime.currentDateTime())
        self.supplier_display.clear()
        self.note_number_input.clear()
        self.observacao_input.clear()
        self.status_display.setText("Em Aberto")
        self.items_table.setRowCount(0)
        self.set_read_only(False)

    def save_entry(self):
        data = self.data_input.date().toString("yyyy-MM-dd")
        entry_date = self.date_input.date().toString("yyyy-MM-dd")
        typing_date = self.typing_date_input.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        note_number = self.note_number_input.text()
        observacao = self.observacao_input.text()

        if not self.selected_supplier_id:
            show_error_message(self, "Error", "Por favor, selecione um fornecedor.")
            return

        items = []
        for row in range(self.items_table.rowCount()):
            items.append({
                'id_insumo': int(self.items_table.item(row, 0).text()),
                'quantidade': float(self.items_table.item(row, 3).text().replace(',', '.')),
                'valor_unitario': float(self.items_table.item(row, 4).text().replace(',', '.'))
            })

        if self.current_entry_id:
            response = self.stock_service.update_entry(self.current_entry_id, data, entry_date, typing_date, self.selected_supplier_id, note_number, observacao, items)
            if response["success"]:
                QMessageBox.information(self, "Sucesso", response["message"])
            else:
                show_error_message(self, "Error", response["message"])
        else:
            response = self.stock_service.create_entry(data, entry_date, typing_date, self.selected_supplier_id, note_number, observacao)
            if response["success"]:
                self.current_entry_id = response["data"]
                self.stock_service.update_entry_items(self.current_entry_id, items)
                self.setWindowTitle(f"Editando Entrada #{self.current_entry_id}")
                self.entry_id_display.setText(str(self.current_entry_id))
                QMessageBox.information(self, "Sucesso", response["message"])
            else:
                show_error_message(self, "Error", response["message"])

    def load_entry_data(self):
        response = self.stock_service.get_entry_details(self.current_entry_id)
        if not response["success"]:
            show_error_message(self, "Error", response["message"])
            self.close()
            return

        details = response["data"]
        master = details['master']
        self.entry_id_display.setText(str(master['ID']))
        self.data_input.setDate(QDate.fromString(master['DATA'], "yyyy-MM-dd"))
        self.date_input.setDate(QDate.fromString(master['DATA_ENTRADA'], "yyyy-MM-dd"))
        self.typing_date_input.setDateTime(QDateTime.fromString(master['DATA_DIGITACAO'], "yyyy-MM-dd HH:mm:ss"))

        self.selected_supplier_id = master.get('ID_FORNECEDOR')
        if self.selected_supplier_id:
            supplier_resp = self.supplier_service.get_supplier_by_id(self.selected_supplier_id)
            if supplier_resp["success"]:
                supplier_data = supplier_resp["data"]
                self.supplier_display.setText(supplier_data['NOME_FANTASIA'] or supplier_data['RAZAO_SOCIAL'])

        self.note_number_input.setText(master.get('NUMERO_NOTA', ''))
        self.observacao_input.setText(master.get('OBSERVACAO', ''))
        self.status_display.setText(master.get('STATUS', ''))

        self.items_table.setRowCount(0)
        for item in details['items']:
            self.add_item_to_table(item, is_loading=True)

        if master.get('STATUS') == 'Finalizada':
            self.set_read_only(True)

    def open_supplier_search(self):
        if self.search_supplier_window is None:
            self.search_supplier_window = SupplierSearchWindow(selection_mode=True)
            self.search_supplier_window.supplier_selected.connect(self.set_selected_supplier)
            self.search_supplier_window.destroyed.connect(lambda: setattr(self, 'search_supplier_window', None))
            self.search_supplier_window.show()
        else:
            self.search_supplier_window.activateWindow()
            self.search_supplier_window.raise_()

    def set_selected_supplier(self, supplier_data):
        self.selected_supplier_id = supplier_data['ID']
        self.supplier_display.setText(supplier_data['NOME_FANTASIA'] or supplier_data['RAZAO_SOCIAL'])

    def open_item_search(self):
        if self.search_item_window is None:
            self.search_item_window = ItemSearchWindow(selection_mode=True, item_type_filter=['Insumo', 'Ambos'])
            self.search_item_window.item_selected.connect(self.add_item_from_search)
            self.search_item_window.destroyed.connect(lambda: setattr(self, 'search_item_window', None))
            self.search_item_window.show()
        else:
            self.search_item_window.activateWindow()
            self.search_item_window.raise_()

    def add_item_from_search(self, item_data):
        for row in range(self.items_table.rowCount()):
            if int(self.items_table.item(row, 0).text()) == item_data['ID']:
                QMessageBox.warning(self, "Atenção", "Este insumo já está na lista.")
                return

        item = { 'ID_INSUMO': item_data['ID'], 'DESCRICAO': item_data['DESCRICAO'], 'SIGLA': item_data['SIGLA'], 'QUANTIDADE': 1.0, 'VALOR_UNITARIO': 0.0 }
        self.add_item_to_table(item)

    def add_item_to_table(self, item, is_loading=False):
        self.items_table.blockSignals(True)
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)

        self.items_table.setItem(row, 0, QTableWidgetItem(str(item['ID_INSUMO'])))
        self.items_table.setItem(row, 1, QTableWidgetItem(item['DESCRICAO']))
        self.items_table.setItem(row, 2, QTableWidgetItem(item['SIGLA'].upper()))
        self.items_table.setItem(row, 3, NumericTableWidgetItem(str(item['QUANTIDADE'])))
        self.items_table.setItem(row, 4, NumericTableWidgetItem(f"{item['VALOR_UNITARIO']:.2f}"))
        total = item['QUANTIDADE'] * item['VALOR_UNITARIO']
        self.items_table.setItem(row, 5, NumericTableWidgetItem(f"{total:.2f}"))

        for col in [1, 2]:
             self.items_table.item(row, col).setFlags(self.items_table.item(row, col).flags() & ~Qt.ItemIsEditable)

        self.items_table.blockSignals(False)

    def remove_item(self):
        rows = self.items_table.selectionModel().selectedRows()
        if not rows:
            QMessageBox.warning(self, "Atenção", "Selecione um insumo para remover.")
            return
        for index in sorted([r.row() for r in rows], reverse=True):
            self.items_table.removeRow(index)

    def on_cell_changed(self, row, column):
        self.items_table.blockSignals(True)
        try:
            qty_item = self.items_table.item(row, 3)
            unit_price_item = self.items_table.item(row, 4)
            total_price_item = self.items_table.item(row, 5)

            qty = float(qty_item.text().replace(',', '.')) if qty_item and qty_item.text() else 0
            unit_price = float(unit_price_item.text().replace(',', '.')) if unit_price_item and unit_price_item.text() else 0
            total_price = float(total_price_item.text().replace(',', '.')) if total_price_item and total_price_item.text() else 0

            if column == 3:  # Quantidade
                new_total = qty * unit_price
                total_price_item.setText(f"{new_total:.2f}")
            elif column == 4:  # Valor Unitário
                new_total = qty * unit_price
                total_price_item.setText(f"{new_total:.2f}")
            elif column == 5:  # Valor Total
                if qty > 0:
                    new_unit_price = total_price / qty
                    unit_price_item.setText(f"{new_unit_price:.2f}")
                else:
                    unit_price_item.setText("0.00")
        except (ValueError, TypeError, ZeroDivisionError) as e:
            print(f"Error in calculation: {e}")
        finally:
            self.items_table.blockSignals(False)

    def set_read_only(self, read_only):
        self.date_input.setReadOnly(read_only)
        self.typing_date_input.setReadOnly(read_only)
        self.supplier_display.setReadOnly(True) # Always read-only

        supplier_layout = self.main_layout.itemAt(1).widget().layout().itemAt(3, QFormLayout.FieldRole).layout()
        search_button = supplier_layout.itemAt(1).widget()
        search_button.setDisabled(read_only)

        self.note_number_input.setReadOnly(read_only)
        self.items_table.setEditTriggers(QAbstractItemView.NoEditTriggers if read_only else QAbstractItemView.AllEditTriggers)
        self.save_button.setDisabled(read_only)
        self.finalize_button.setDisabled(read_only)
        self.add_item_button.setDisabled(read_only)
        self.remove_item_button.setDisabled(read_only)

    def finalize_entry(self):
        if not self.current_entry_id:
            show_error_message(self, "Error", "Salve a nota de entrada antes de finalizá-la.")
            return

        reply = QMessageBox.question(
            self, "Confirmar Finalização", "Você tem certeza que deseja finalizar esta entrada?\nEsta ação atualizará o estoque e o custo dos insumos e não poderá ser desfeita.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.save_entry()
            response = self.stock_service.finalize_entry(self.current_entry_id)
            if response["success"]:
                QMessageBox.information(self, "Sucesso", response["message"])
                self.load_entry_data()
            else:
                show_error_message(self, "Error", response["message"])
