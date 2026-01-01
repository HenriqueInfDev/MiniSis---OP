# app/services/supplier_service.py
from ..supplier.supplier_repository import SupplierRepository
from ..validators import validate_cpf_cnpj

class SupplierService:
    def __init__(self):
        self.supplier_repository = SupplierRepository()

    def add_supplier(self, razao_social, nome_fantasia, cnpj, phone, email, address):
        if not razao_social:
            return {"success": False, "message": "A Razão Social do fornecedor é obrigatória."}

        if cnpj and not validate_cpf_cnpj(cnpj)[0]:
            return {"success": False, "message": "CPF/CNPJ inválido."}

        try:
            new_id = self.supplier_repository.add(razao_social, nome_fantasia, cnpj, phone, email, address)
            if new_id:
                return {"success": True, "data": new_id, "message": "Fornecedor adicionado com sucesso."}
            else:
                return {"success": False, "message": "Já existe um fornecedor com esta Razão Social."}
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

    def update_supplier(self, supplier_id, razao_social, nome_fantasia, cnpj, phone, email, address):
        if not razao_social:
            return {"success": False, "message": "A Razão Social do fornecedor é obrigatória."}

        if cnpj and not validate_cpf_cnpj(cnpj)[0]:
            return {"success": False, "message": "CPF/CNPJ inválido."}

        try:
            if self.supplier_repository.update(supplier_id, razao_social, nome_fantasia, cnpj, phone, email, address):
                return {"success": True, "message": "Fornecedor atualizado com sucesso."}
            else:
                return {"success": False, "message": "Já existe um fornecedor com esta Razão Social."}
        except Exception as e:
            return {"success": False, "message": f"Erro ao atualizar fornecedor: {e}"}

    def delete_supplier(self, supplier_id):
        try:
            if self.supplier_repository.delete(supplier_id):
                return {"success": True, "message": "Fornecedor excluído com sucesso."}
            else:
                return {"success": False, "message": "Erro: Fornecedor não encontrado para exclusão."}
        except Exception as e:
            return {"success": False, "message": f"Erro no banco de dados ao tentar excluir o fornecedor: {e}"}

    def search_suppliers(self, search_field, search_text):
        try:
            suppliers = self.supplier_repository.search(search_text, search_field)
            return {"success": True, "data": suppliers}
        except Exception as e:
            return {"success": False, "message": f"Erro ao buscar fornecedores: {e}"}
