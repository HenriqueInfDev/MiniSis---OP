# app/services/item_service.py
from ..item.item_repository import ItemRepository

class ItemService:
    def __init__(self):
        self.item_repository = ItemRepository()

    def add_item(self, description, item_type, unit_id, supplier_id=None):
        if not all([description, item_type, unit_id]):
            return {"success": False, "message": "Todos os campos são obrigatórios."}

        try:
            new_id = self.item_repository.add(description, item_type, unit_id, supplier_id)
            if new_id:
                return {"success": True, "data": new_id, "message": "Item adicionado com sucesso."}
            else:
                return {"success": False, "message": "Item com esta descrição já existe."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao adicionar item: {e}"}

    def get_all_items(self):
        try:
            items = self.item_repository.get_all()
            return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar itens: {e}"}

    def get_item_by_id(self, item_id):
        try:
            item = self.item_repository.get_by_id(item_id)
            if item:
                return {"success": True, "data": item}
            else:
                return {"success": False, "message": "Item não encontrado."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar item: {e}"}

    def list_units(self):
        try:
            units = self.item_repository.list_units()
            return {"success": True, "data": units}
        except Exception as e:
            return {"success": False, "message": f"Erro ao listar unidades: {e}"}

    def update_item(self, item_id, description, item_type, unit_id, supplier_id=None):
        if not all([item_id, description, item_type, unit_id]):
            return {"success": False, "message": "Todos os campos são obrigatórios."}

        try:
            if self.item_repository.update(item_id, description, item_type, unit_id, supplier_id):
                return {"success": True, "message": "Item atualizado com sucesso."}
            else:
                return {"success": False, "message": "Item com esta descrição já existe."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar item: {e}"}

    def delete_item(self, item_id):
        try:
            if self.item_repository.is_item_in_composition(item_id):
                return {"success": False, "message": "Não é possível excluir: O item está sendo usado como insumo na composição de um produto."}
            if self.item_repository.is_item_in_production_order(item_id):
                return {"success": False, "message": "Não é possível excluir: O item (produto) está incluído em uma ou mais Ordens de Produção."}
            if self.item_repository.has_stock_movement(item_id):
                return {"success": False, "message": "Não é possível excluir: O item possui registros de movimentação de estoque."}
            if self.item_repository.has_composition(item_id):
                return {"success": False, "message": "Não é possível excluir: O produto possui uma composição definida. Remova os insumos primeiro."}

            if self.item_repository.delete(item_id):
                return {"success": True, "message": "Item excluído com sucesso."}
            else:
                return {"success": False, "message": "Erro: Item não encontrado para exclusão."}
        except Exception as e:
            return {"success": False, "message": f"Erro no banco de dados ao tentar excluir o item: {e}"}

    def search_items(self, search_type, search_text):
        try:
            items = self.item_repository.search(search_type, search_text)
            return {"success": True, "data": items}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar itens: {e}"}

    def manual_input_material(self, item_id, quantity, total_value):
        if not all([item_id, quantity, total_value]):
            return {"success": False, "message": "Todos os campos são obrigatórios."}

        if quantity <= 0 or total_value <= 0:
            return {"success": False, "message": "Quantidade e valor total devem ser positivos."}

        try:
            item = self.item_repository.get_by_id(item_id)
            if not item or item['TIPO_ITEM'] not in ('Insumo', 'Ambos'):
                return {"success": False, "message": "Apenas itens do tipo 'Insumo' ou 'Ambos' podem ter entrada manual."}

            old_balance = item['SALDO_ESTOQUE']
            old_average_cost = item['CUSTO_MEDIO']

            new_balance = old_balance + quantity
            input_unit_value = total_value / quantity

            new_average_cost = ((old_balance * old_average_cost) + (quantity * input_unit_value)) / new_balance

            self.item_repository.update_stock_and_cost(item_id, new_balance, new_average_cost)
            self.item_repository.add_stock_movement(item_id, 'Entrada Manual', quantity, input_unit_value)

            return {"success": True, "message": f"Entrada de {quantity} un. do item ID {item_id} registrada. Novo saldo: {new_balance}."}

        except Exception as e:
            return {"success": False, "message": f"Erro ao registrar entrada de material: {e}"}
