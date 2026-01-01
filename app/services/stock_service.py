# app/services/stock_service.py
from ..stock.stock_repository import StockRepository

class StockService:
    def __init__(self):
        self.stock_repository = StockRepository()

    def create_entry(self, entry_date, typing_date, supplier_id, note_number):
        if not all([entry_date, typing_date, supplier_id, note_number]):
            return {"success": False, "message": "Todos os campos do cabeçalho são obrigatórios."}

        try:
            entry_id = self.stock_repository.create_entry(entry_date, typing_date, supplier_id, note_number)
            if entry_id:
                return {"success": True, "data": entry_id, "message": "Nota de entrada criada com sucesso."}
            else:
                return {"success": False, "message": "Erro ao criar nota de entrada no banco de dados."}
        except Exception as e:
            return {"success": False, "message": f"Erro inesperado: {e}"}

    def update_entry(self, entry_id, entry_date, typing_date, supplier_id, note_number, items):
        if not all([entry_id, entry_date, typing_date, supplier_id, note_number]):
            return {"success": False, "message": "Todos os campos do cabeçalho são obrigatórios."}

        try:
            self.stock_repository.update_entry_master(entry_id, entry_date, typing_date, supplier_id, note_number)
            self.stock_repository.update_entry_items(entry_id, items)
            return {"success": True, "message": "Nota de entrada atualizada com sucesso."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar nota de entrada: {e}"}

    def update_entry_items(self, entry_id, items):
        try:
            self.stock_repository.update_entry_items(entry_id, items)
            return {"success": True, "message": "Itens da nota de entrada atualizados com sucesso."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar os itens da nota de entrada: {e}"}


    def get_entry_details(self, entry_id):
        try:
            details = self.stock_repository.get_entry_details(entry_id)
            if details:
                return {"success": True, "data": details}
            else:
                return {"success": False, "message": "Nota de entrada não encontrada."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar detalhes da nota de entrada: {e}"}

    def list_entries(self, search_term="", search_field="id"):
        try:
            entries = self.stock_repository.list_entries(search_term, search_field)
            return {"success": True, "data": entries}
        except Exception as e:
            return {"success": False, "message": f"Erro ao listar notas de entrada: {e}"}

    def finalize_entry(self, entry_id):
        if not entry_id:
            return {"success": False, "message": "ID da nota de entrada não fornecido."}

        details = self.stock_repository.get_entry_details(entry_id)
        if not details:
            return {"success": False, "message": "Nota de entrada não encontrada."}
        if details['master']['STATUS'] == 'Finalizada':
            return {"success": False, "message": "Esta nota de entrada já foi finalizada."}
        if not details['items']:
            return {"success": False, "message": "Não é possível finalizar uma entrada sem itens."}

        try:
            success, total_value = self.stock_repository.finalize_entry(entry_id)
            if success:
                return {"success": True, "message": f"Entrada #{entry_id} finalizada com sucesso. Valor total: {total_value:.2f}"}
            else:
                return {"success": False, "message": "Erro no banco de dados ao finalizar a entrada."}
        except Exception as e:
            return {"success": False, "message": f"Um erro inesperado ocorreu: {e}"}
