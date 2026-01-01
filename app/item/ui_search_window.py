# app/item/ui_search_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLineEdit,
    QComboBox, QPushButton, QTableView, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Signal
from PySide6.QtGui import QStandardItemModel, QStandardItem

from app.item.service import ItemService
from app.utils.ui_utils import show_error_message


class ItemSearchWindow(QWidget):
    # Sinal que emitirá os dados do item selecionado
    item_selected = Signal(dict)

    def __init__(self, selection_mode=False, item_type_filter=None):
        super().__init__()
        self.item_service = ItemService()
        self.edit_window = None # Para manter referência da janela de edição
        self.selection_mode = selection_mode
        self.item_type_filter = item_type_filter # Lista de tipos de item a exibir

        title = "Selecionar Insumo" if selection_mode else "Pesquisa de Produto"
        self.setWindowTitle(title)
        self.setGeometry(150, 150, 800, 600)

        # Layout Principal
        self.main_layout = QVBoxLayout(self)

        # --- Grupo de Pesquisa ---
        self.create_search_group()

        # --- Grupo de Resultados ---
        self.create_results_group()

        # Carrega os itens na inicialização
        self.load_items()

    def create_search_group(self):
        search_group = QGroupBox("Pesquisa")
        search_layout = QHBoxLayout()

        self.search_field_combo = QComboBox()
        self.search_field_combo.addItems(["Descrição", "ID", "Unidade", "Quantidade"])

        self.search_text = QLineEdit()
        self.search_text.returnPressed.connect(self.load_items) # Busca ao pressionar Enter

        search_button = QPushButton("Buscar")
        search_button.clicked.connect(self.load_items)

        new_button = QPushButton("Novo Item")
        new_button.clicked.connect(self.open_new_item_window)

        search_layout.addWidget(self.search_field_combo)
        search_layout.addWidget(self.search_text, 1) # O campo de texto se expande
        search_layout.addWidget(search_button)
        search_layout.addWidget(new_button)
        search_group.setLayout(search_layout)

        self.main_layout.addWidget(search_group)

    def create_results_group(self):
        results_group = QGroupBox("Resultados")
        results_layout = QVBoxLayout()

        self.table_view = QTableView()
        self.table_model = QStandardItemModel()
        self.table_model.setHorizontalHeaderLabels(["ID", "Código Interno", "Descrição", "Tipo", "Un.", "Quantidade", "Custo Unit."])
        self.table_view.setModel(self.table_model)
        header = self.table_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch) # Coluna "Descrição"
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table_view.verticalHeader().setVisible(False)
        self.table_view.setSortingEnabled(True)
        self.table_view.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        self.table_view.doubleClicked.connect(self.handle_double_click)

        results_layout.addWidget(self.table_view)
        results_group.setLayout(results_layout)
        self.main_layout.addWidget(results_group)

    def load_items(self):
        """Carrega os itens na tabela, usando o ItemService."""
        search_type_text = self.search_field_combo.currentText()
        search_content = self.search_text.text()
        self.table_model.removeRows(0, self.table_model.rowCount())

        if search_content:
            search_type_map = {
                "Descrição": "description",
                "ID": "id"
            }
            search_type = search_type_map.get(search_type_text, "description")
            response = self.item_service.search_items(search_type, search_content)
        else:
            response = self.item_service.get_all_items()

        if not response["success"]:
            show_error_message(self, "Error", response["message"])
            return

        # Aplica o filtro de tipo de item, se existir
        items = response["data"]
        if self.item_type_filter:
            items = [item for item in items if item['TIPO_ITEM'] in self.item_type_filter]

        for item in items:
            id_item = QStandardItem()
            id_item.setData(item['ID'], 0)

            qty_item = QStandardItem()
            qty_item.setData(item['SALDO_ESTOQUE'], 0)

            cost_item = QStandardItem()
            cost_item.setData(item['CUSTO_MEDIO'], 0)

            row = [
                id_item,
                QStandardItem(item['CODIGO_INTERNO']),
                QStandardItem(item['DESCRICAO']),
                QStandardItem(item['TIPO_ITEM']),
                QStandardItem(item['SIGLA'].upper()),
                qty_item,
                cost_item
            ]
            # Adiciona a linha à tabela primeiro
            self.table_model.appendRow(row)
            # Agora que a linha existe, podemos adicionar o dado extra
            row_index = self.table_model.rowCount() - 1
            full_item_data = {
                'ID': item['ID'],
                'DESCRICAO': item['DESCRICAO'],
                'TIPO_ITEM': item['TIPO_ITEM'],
                'SIGLA': item['SIGLA'],
                'SALDO_ESTOQUE': item['SALDO_ESTOQUE'],
                'CUSTO_MEDIO': item['CUSTO_MEDIO']
            }
            self.table_model.item(row_index, 0).setData(full_item_data)

    def handle_double_click(self, model_index):
        if self.selection_mode:
            item_data = self.table_model.item(model_index.row(), 0).data()
            self.item_selected.emit(item_data)
            self.close()
        else:
            self.open_edit_item_window(model_index)

    def open_new_item_window(self):
        # Passa None para indicar que é um novo item
        self.show_edit_window(item_id=None)

    def open_edit_item_window(self, model_index):
        # Pega o ID do item da tabela e passa para a janela de edição
        item_data = self.table_model.item(model_index.row(), 0).data()
        self.show_edit_window(item_id=item_data['ID'])

    def show_edit_window(self, item_id):
        """Abre a janela de edição, garantindo que apenas uma instância exista e limpando a referência quando fechada."""
        from .ui_form_window import ItemFormWindow
        if self.edit_window is None:
            self.edit_window = ItemFormWindow(item_id=item_id)
            self.edit_window.destroyed.connect(self.on_edit_window_closed)
            self.edit_window.show()
        else:
            self.edit_window.activateWindow()
            self.edit_window.raise_()

    def on_edit_window_closed(self):
        """Slot para limpar a referência da janela de edição e recarregar os itens."""
        self.edit_window = None
        self.load_items()
