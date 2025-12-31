# app/services/supplier_service.py
from ..supplier.supplier_repository import SupplierRepository

class SupplierService:
    def __init__(self):
        self.supplier_repository = SupplierRepository()

    def add_supplier(self, name, cnpj, phone, email):
        if not name:
            return {"success": False, "message": "O nome do fornecedor é obrigatório."}

        try:
            new_id = self.supplier_repository.add(name, cnpj, phone, email)
            if new_id:
                return {"success": True, "data": new_id, "message": "Fornecedor adicionado com sucesso."}
            else:
                return {"success": False, "message": "Fornecedor com este nome já existe."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao adicionar fornecedor: {e}"}

    def get_all_suppliers(self):
        try:
            suppliers = self.supplier_repository.get_all()
            return {"success": True, "data": suppliers}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar fornecedores: {e}"}

    def get_supplier_by_id(self, supplier_id):
        try:
            supplier = self.supplier_repository.get_by_id(supplier_id)
            if supplier:
                return {"success": True, "data": supplier}
            else:
                return {"success": False, "message": "Fornecedor não encontrado."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar fornecedor: {e}"}

    def update_supplier(self, supplier_id, name, cnpj, phone, email):
        if not name:
            return {"success": False, "message": "O nome do fornecedor é obrigatório."}

        try:
            if self.supplier_repository.update(supplier_id, name, cnpj, phone, email):
                return {"success": True, "message": "Fornecedor atualizado com sucesso."}
            else:
                return {"success": False, "message": "Fornecedor com este nome já existe."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar fornecedor: {e}"}

    def delete_supplier(self, supplier_id):
        try:
            # Check for dependencies before deleting
            # (e.g., if the supplier is used in any stock entry)
            # For now, we'll just delete directly.
            if self.supplier_repository.delete(supplier_id):
                return {"success": True, "message": "Fornecedor excluído com sucesso."}
            else:
                return {"success": False, "message": "Erro: Fornecedor não encontrado para exclusão."}
        except Exception as e:
            return {"success": False, "message": f"Erro no banco de dados ao tentar excluir o fornecedor: {e}"}
