# app/sales/sale_service.py
from app.sales.sale_repository import SaleRepository

class SaleService:
    def __init__(self):
        self.sale_repository = SaleRepository()

    def create_sale(self, sale_date, observacao, items):
        if not sale_date:
            return {"success": False, "message": "A data da saída é obrigatória."}

        total_value = sum(item['quantidade'] * item['valor_unitario'] for item in items)

        try:
            sale_id = self.sale_repository.create_sale(sale_date, observacao, total_value)
            if sale_id:
                self.sale_repository.update_sale_items(sale_id, items)
                return {"success": True, "data": sale_id, "message": "Saída criada com sucesso."}
            else:
                return {"success": False, "message": "Erro ao criar saída no banco de dados."}
        except Exception as e:
            return {"success": False, "message": f"Erro inesperado: {e}"}

    def update_sale(self, sale_id, sale_date, observacao, items):
        if not all([sale_id, sale_date]):
            return {"success": False, "message": "ID da Saída e Data são obrigatórios."}

        total_value = sum(item['quantidade'] * item['valor_unitario'] for item in items)

        try:
            self.sale_repository.update_sale_master(sale_id, sale_date, observacao, total_value)
            self.sale_repository.update_sale_items(sale_id, items)
            return {"success": True, "message": "Saída atualizada com sucesso."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar saída: {e}"}

    def get_sale_details(self, sale_id):
        try:
            details = self.sale_repository.get_sale_details(sale_id)
            if details:
                return {"success": True, "data": details}
            else:
                return {"success": False, "message": "Saída não encontrada."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar detalhes da saída: {e}"}

    def list_sales(self, search_term="", search_field="id"):
        try:
            sales = self.sale_repository.list_sales(search_term, search_field)
            return {"success": True, "data": sales}
        except Exception as e:
            return {"success": False, "message": f"Erro ao listar saídas: {e}"}

    def finalize_sale(self, sale_id):
        if not sale_id:
            return {"success": False, "message": "ID da saída não fornecido."}

        details_response = self.get_sale_details(sale_id)
        if not details_response["success"]:
            return details_response

        details = details_response["data"]
        if details['master']['STATUS'] == 'Finalizada':
            return {"success": False, "message": "Esta saída já foi finalizada."}
        if not details['items']:
            return {"success": False, "message": "Não é possível finalizar uma saída sem itens."}

        try:
            success = self.sale_repository.finalize_sale(sale_id)
            if success:
                return {"success": True, "message": f"Saída #{sale_id} finalizada com sucesso."}
            else:
                return {"success": False, "message": "Erro no banco de dados ao finalizar a saída."}
        except Exception as e:
            return {"success": False, "message": f"Um erro inesperado ocorreu: {e}"}
