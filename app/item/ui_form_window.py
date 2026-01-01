# app/item/ui_form_window.py
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QFormLayout, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QHeaderView, QTabWidget,
    QTableWidget, QTableWidgetItem, QLabel, QDoubleSpinBox, QAbstractItemView
)
from PySide6.QtCore import Qt
from app.item.service import ItemService
from app.production import composition_operations
from app.utils.ui_utils import NumericTableWidgetItem, show_error_message

class ItemFormWindow(QWidget):
    def __init__(self, item_id=None):
        super().__init__()
        self.item_service = ItemService()
        self.current_item_id = item_id
        self.has_unsaved_changes = False

        self.setWindowTitle(f"Editando Item #{item_id}" if item_id else "Novo Item")
        self.setGeometry(200, 200, 700, 600)

        # Layout Principal
        self.main_layout = QVBoxLayout(self)

        # --- Cabeçalho com Botões ---
        self.create_header_buttons()

        # --- Sistema de Abas ---
        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        # --- Aba Principal ---
        self.create_main_tab()

        # --- Aba Composição ---
        self.create_composition_tab()

        # Carregar dados
        self.populate_units_combobox()
        self.populate_suppliers_combobox()
        self.load_item_data()

        # Conectar sinal da ComboBox de tipo
        self.type_combo.currentTextChanged.connect(self.toggle_composition_tab)

        self.search_window = None # Para manter a referência da janela de busca

        # Conectar sinais para detectar alterações
        self.description_input.textChanged.connect(self._set_unsaved_changes)
        self.type_combo.currentIndexChanged.connect(self._set_unsaved_changes)
        self.unit_combo.currentIndexChanged.connect(self._set_unsaved_changes)
        # A alteração da composição será tratada nos métodos add/remove

    def _set_unsaved_changes(self):
        """Marca o estado como 'não salvo' e atualiza o título da janela."""
        if not self.has_unsaved_changes:
            self.has_unsaved_changes = True
            self.setWindowTitle(self.windowTitle() + "*")

    def closeEvent(self, event):
        """Sobrescreve o evento de fechar a janela para verificar alterações."""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                'Alterações Não Salvas',
                'Você tem alterações não salvas. Deseja salvá-las antes de sair?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.save_item()
                # Se o save_item falhar (por exemplo, validação), não devemos fechar
                if self.has_unsaved_changes: # O save_item reseta o flag se for bem sucedido
                    event.ignore()
                else:
                    event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else: # Cancel
                event.ignore()
        else:
            event.accept()

    def create_header_buttons(self):
        header_layout = QHBoxLayout()

        new_button = QPushButton("Novo")
        new_button.clicked.connect(self.new_item)

        save_button = QPushButton("Salvar")
        save_button.clicked.connect(self.save_item)

        delete_button = QPushButton("Excluir")
        delete_button.clicked.connect(self.delete_item)

        close_button = QPushButton("Fechar")
        close_button.clicked.connect(self.close)

        header_layout.addStretch()
        header_layout.addWidget(new_button)
        header_layout.addWidget(save_button)
        header_layout.addWidget(delete_button)
        header_layout.addWidget(close_button)

        self.main_layout.addLayout(header_layout)

    def create_main_tab(self):
        main_widget = QWidget()
        layout = QFormLayout(main_widget)

        self.codigo_interno_input = QLineEdit()
        self.description_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Insumo", "Produto", "Ambos"])
        self.unit_combo = QComboBox()
        self.supplier_combo = QComboBox()

        layout.addRow("Código Interno:", self.codigo_interno_input)
        layout.addRow("Descrição:", self.description_input)
        layout.addRow("Tipo de Item:", self.type_combo)
        layout.addRow("Unidade:", self.unit_combo)
        layout.addRow("Fornecedor Padrão:", self.supplier_combo)

        self.tab_widget.addTab(main_widget, "Principal")

    def create_composition_tab(self):
        self.composition_widget = QWidget()
        layout = QVBoxLayout(self.composition_widget)
        self.selected_material = None # Para armazenar os dados do insumo selecionado

        # --- Formulário de Edição/Adição ---
        edit_group = QGroupBox("Insumo")
        edit_group_layout = QVBoxLayout(edit_group) # Layout principal do grupo

        # Layout horizontal para os campos de entrada
        input_layout = QHBoxLayout()

        # Campo de Descrição (Insumo)
        self.material_display = QLineEdit()
        self.material_display.setPlaceholderText("Selecione um insumo...")
        self.material_display.setReadOnly(True)
        input_layout.addWidget(self.material_display, 6) # Proporção 6

        # Campo de Quantidade
        self.quantity_spinbox = QDoubleSpinBox()
        self.quantity_spinbox.setRange(0.0, 99999.99)
        self.quantity_spinbox.setDecimals(4)
        input_layout.addWidget(self.quantity_spinbox, 2) # Proporção 2

        # Label da Unidade
        self.unit_label = QLabel("Un.")
        self.unit_label.setFixedWidth(40) # Largura fixa para alinhar
        input_layout.addWidget(self.unit_label)

        # Botão de Busca
        search_button = QPushButton("Buscar...")
        search_button.clicked.connect(self.open_material_search)
        input_layout.addWidget(search_button)

        edit_group_layout.addLayout(input_layout)

        # Botão de Adicionar/Atualizar em uma linha separada
        self.add_update_button = QPushButton("Adicionar Insumo")
        self.add_update_button.clicked.connect(self.add_update_composition_item)

        # O botão agora ocupa toda a largura
        edit_group_layout.addWidget(self.add_update_button)

        layout.addWidget(edit_group)

        # --- Grid de Composição e Botões de Ação ---
        self.composition_table = QTableWidget()
        self.composition_table.setColumnCount(6)
        self.composition_table.setHorizontalHeaderLabels(["ID Insumo", "Descrição", "Qtd", "Un.", "Custo Unit.", "Custo Total"])
        self.composition_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        header = self.composition_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        self.composition_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.composition_table.setColumnHidden(0, True)
        self.composition_table.verticalHeader().setVisible(False)
        self.composition_table.setSortingEnabled(True)
        self.composition_table.setStyleSheet("QTableView::item:selected { background-color: #D3D3D3; color: black; }")
        layout.addWidget(self.composition_table)

        # --- Barra de Ações da Composição ---
        action_bar_layout = QHBoxLayout()
        self.edit_selected_button = QPushButton("Editar Selecionado")
        self.edit_selected_button.clicked.connect(self.load_selected_for_edit)
        self.remove_selected_button = QPushButton("Remover Selecionado")
        self.remove_selected_button.clicked.connect(self.remove_selected_composition_item)

        action_bar_layout.addStretch()
        action_bar_layout.addWidget(self.edit_selected_button)
        action_bar_layout.addWidget(self.remove_selected_button)
        layout.addLayout(action_bar_layout)

        # --- Custo Total ---
        self.total_cost_label = QLabel("Custo Total da Composição: R$ 0.00")
        layout.addWidget(self.total_cost_label, 0, Qt.AlignRight)

        self.tab_widget.addTab(self.composition_widget, "Composição")

    def populate_units_combobox(self):
        response = self.item_service.list_units()
        if response["success"]:
            for unit in response["data"]:
                self.unit_combo.addItem(f"{unit['NOME']} ({unit['SIGLA']})", userData=unit['ID'])
        else:
            show_error_message(self, "Error", response["message"])

    def populate_suppliers_combobox(self):
        from app.supplier.service import SupplierService
        supplier_service = SupplierService()
        response = supplier_service.get_all_suppliers()
        if response["success"]:
            self.supplier_combo.addItem("Nenhum", userData=None)
            for supplier in response["data"]:
                self.supplier_combo.addItem(supplier['NOME_FANTASIA'] or supplier['RAZAO_SOCIAL'], userData=supplier['ID'])
        else:
            show_error_message(self, "Error", response["message"])

    def load_item_data(self):
        if self.current_item_id:
            response = self.item_service.get_item_by_id(self.current_item_id)
            if response["success"]:
                item = response["data"]
                self.codigo_interno_input.setText(item['CODIGO_INTERNO'])
                self.description_input.setText(item['DESCRICAO'])
                self.type_combo.setCurrentText(item['TIPO_ITEM'])

                unit_index = self.unit_combo.findData(item['ID_UNIDADE'])
                if unit_index != -1:
                    self.unit_combo.setCurrentIndex(unit_index)

                supplier_index = self.supplier_combo.findData(item['ID_FORNECEDOR_PADRAO'])
                if supplier_index != -1:
                    self.supplier_combo.setCurrentIndex(supplier_index)

                self.load_composition_data()

        self.toggle_composition_tab()

    def load_composition_data(self):
        self.composition_table.setRowCount(0)
        if self.current_item_id:
            composition = composition_operations.get_bom(self.current_item_id)
            for comp_item in composition:
                self.add_row_to_composition_grid(
                    comp_item['ID_INSUMO'],
                    comp_item['DESCRICAO'],
                    comp_item['QUANTIDADE'],
                    comp_item['CUSTO_MEDIO'],
                    comp_item['SIGLA']
                )
            self.update_total_cost()

    def toggle_composition_tab(self):
        item_type = self.type_combo.currentText()
        composition_tab_index = self.tab_widget.indexOf(self.composition_widget)
        is_visible = item_type in ("Produto", "Ambos")
        self.tab_widget.setTabVisible(composition_tab_index, is_visible)

    def open_material_search(self):
        """Abre a janela de busca de itens em modo de seleção."""
        from .ui_search_window import SearchWindow
        if self.search_window is None:
            self.search_window = SearchWindow(selection_mode=True, item_type_filter=['Insumo', 'Ambos'])
            self.search_window.item_selected.connect(self.set_selected_material)
            self.search_window.destroyed.connect(lambda: setattr(self, 'search_window', None))
            self.search_window.show()
        else:
            self.search_window.activateWindow()
            self.search_window.raise_()

    def set_selected_material(self, item_data):
        """Recebe o item selecionado da janela de busca e preenche o formulário."""
        self.selected_material = item_data
        self.material_display.setText(item_data['DESCRICAO'])
        self.unit_label.setText(item_data['SIGLA'].upper())
        self.quantity_spinbox.setFocus() # Move o foco para a quantidade

    def add_update_composition_item(self):
        """Adiciona ou atualiza um item na tabela de composição."""
        if not self.selected_material:
            QMessageBox.warning(self, "Atenção", "Nenhum insumo selecionado.")
            return

        quantity = self.quantity_spinbox.value()
        if quantity <= 0:
            QMessageBox.warning(self, "Atenção", "A quantidade deve ser maior que zero.")
            return

        material_id = self.selected_material['ID']

        # VALIDAÇÃO: Movida para o módulo de operações
        is_valid, error_message = composition_operations.validate_bom_item(
            self.current_item_id, material_id
        )
        if not is_valid:
            QMessageBox.warning(self, "Erro de Validação", error_message)
            return

        # Verifica se o item já está na tabela (para atualização)
        for row in range(self.composition_table.rowCount()):
            if int(self.composition_table.item(row, 0).text()) == material_id:
                # Atualiza a quantidade
                self.composition_table.item(row, 2).setText(str(quantity))
                # Recalcula o custo total da linha
                unit_cost = float(self.composition_table.item(row, 4).text())
                total_cost = quantity * unit_cost
                self.composition_table.item(row, 5).setText(f"{total_cost:.4f}")
                self.update_total_cost()
                self._clear_material_form()
                return

        # Se não encontrou, adiciona uma nova linha
        response = self.item_service.get_item_by_id(material_id)
        unit_cost = response["data"]['CUSTO_MEDIO'] if response["success"] else 0

        self.add_row_to_composition_grid(
            material_id,
            self.selected_material['DESCRICAO'],
            quantity,
            unit_cost,
            self.selected_material['SIGLA']
        )
        self.update_total_cost()
        self._clear_material_form()
        self._set_unsaved_changes()

    def load_selected_for_edit(self):
        """Carrega um item da tabela de volta no formulário para edição."""
        selected_rows = self.composition_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Atenção", "Selecione um item na tabela para editar.")
            return

        selected_row = selected_rows[0].row()

        # Recria o dicionário `selected_material` com os dados da tabela
        self.selected_material = {
            'ID': int(self.composition_table.item(selected_row, 0).text()),
            'DESCRICAO': self.composition_table.item(selected_row, 1).text(),
            'SIGLA': self.composition_table.item(selected_row, 3).text()
        }

        # Preenche o formulário
        self.material_display.setText(self.selected_material['DESCRICAO'])
        self.unit_label.setText(self.selected_material['SIGLA'].upper())
        self.quantity_spinbox.setValue(float(self.composition_table.item(selected_row, 2).text()))

        self.add_update_button.setText("Atualizar Insumo")

    def remove_selected_composition_item(self):
        """Remove o item selecionado da tabela de composição."""
        selected_rows = self.composition_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Atenção", "Selecione um item na tabela para remover.")
            return

        # Remove em ordem reversa para não bagunçar os índices
        for index in sorted([idx.row() for idx in selected_rows], reverse=True):
            self.composition_table.removeRow(index)

        self.update_total_cost()
        self._set_unsaved_changes()

    def _clear_material_form(self):
        """Limpa o formulário de adição/edição de insumo."""
        self.selected_material = None
        self.material_display.clear()
        self.quantity_spinbox.setValue(0.0)
        self.unit_label.clear()
        self.add_update_button.setText("Adicionar")
        self.composition_table.clearSelection()

    def add_row_to_composition_grid(self, material_id, description, quantity, unit_cost, unit):
        row_position = self.composition_table.rowCount()
        self.composition_table.insertRow(row_position)

        total_cost = quantity * unit_cost

        self.composition_table.setItem(row_position, 0, NumericTableWidgetItem(str(material_id)))
        self.composition_table.setItem(row_position, 1, QTableWidgetItem(description))
        self.composition_table.setItem(row_position, 2, NumericTableWidgetItem(str(quantity)))
        self.composition_table.setItem(row_position, 3, QTableWidgetItem(unit.upper()))
        self.composition_table.setItem(row_position, 4, NumericTableWidgetItem(f"{unit_cost:.4f}"))
        self.composition_table.setItem(row_position, 5, NumericTableWidgetItem(f"{total_cost:.4f}"))

    def update_total_cost(self):
        total = 0.0
        for row in range(self.composition_table.rowCount()):
            total += float(self.composition_table.item(row, 5).text())
        self.total_cost_label.setText(f"Custo Total da Composição: R$ {total:.4f}")

    def new_item(self):
        self.current_item_id = None
        self.setWindowTitle("Novo Item")
        self.codigo_interno_input.clear()
        self.description_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.unit_combo.setCurrentIndex(0)
        self.supplier_combo.setCurrentIndex(0)
        self.composition_table.setRowCount(0)
        self.update_total_cost()
        self.toggle_composition_tab()
        self.description_input.setFocus()
        self._clear_material_form()

        # Reseta o estado para 'salvo'
        self.has_unsaved_changes = False
        self.setWindowTitle("Novo Item")


    def save_item(self):
        # Coleta dados da aba Principal
        codigo_interno = self.codigo_interno_input.text()
        description = self.description_input.text()
        item_type = self.type_combo.currentText()
        unit_id = self.unit_combo.currentData()
        supplier_id = self.supplier_combo.currentData()

        if not description or unit_id is None:
            QMessageBox.warning(self, "Atenção", "Descrição e Unidade são obrigatórios.")
            return

        # Salva o item principal
        if self.current_item_id is None:  # Novo item
            response = self.item_service.add_item(codigo_interno, description, item_type, unit_id, supplier_id)
            if response["success"]:
                self.current_item_id = response["data"]
            else:
                show_error_message(self, "Error", response["message"])
                return
        else:  # Item existente
            response = self.item_service.update_item(self.current_item_id, codigo_interno, description, item_type, unit_id, supplier_id)
            if not response["success"]:
                show_error_message(self, "Error", response["message"])
                return

        # Salva a composição se a aba estiver visível
        if self.tab_widget.isTabVisible(self.tab_widget.indexOf(self.composition_widget)):
            new_composition = []
            for row in range(self.composition_table.rowCount()):
                material_id = int(self.composition_table.item(row, 0).text())
                quantity = float(self.composition_table.item(row, 2).text())
                new_composition.append({'id_insumo': material_id, 'quantidade': quantity})

            composition_operations.update_composition(self.current_item_id, new_composition)

        QMessageBox.information(self, "Sucesso", "Item salvo com sucesso!")
        self.setWindowTitle(f"Editando Item #{self.current_item_id}")
        self.has_unsaved_changes = False

    def delete_item(self):
        """Lida com a exclusão do item atual."""
        if self.current_item_id is None:
            QMessageBox.warning(self, "Atenção", "Nenhum item carregado para excluir.")
            return

        reply = QMessageBox.question(
            self,
            'Confirmar Exclusão',
            f"Você tem certeza que deseja excluir o item #{self.current_item_id}?\nEsta ação não pode ser desfeita.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            response = self.item_service.delete_item(self.current_item_id)
            if response["success"]:
                QMessageBox.information(self, "Sucesso", response["message"])
                self.has_unsaved_changes = False # Para evitar o prompt de salvar ao fechar
                self.close()
            else:
                show_error_message(self, "Error", response["message"])
