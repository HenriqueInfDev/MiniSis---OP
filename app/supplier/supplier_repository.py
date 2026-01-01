# app/supplier/supplier_repository.py
import sqlite3
from ..database import get_db_manager

class SupplierRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def add(self, supplier_data):
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO T_FORNECEDOR (
                    NOME_RAZAO_SOCIAL, CPF_CNPJ, TIPO_PESSOA, TELEFONE, EMAIL,
                    CEP, ENDERECO, NUMERO, COMPLEMENTO, BAIRRO, CIDADE, ESTADO
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    supplier_data['nome_razao_social'], supplier_data['cpf_cnpj'],
                    supplier_data['tipo_pessoa'], supplier_data['telefone'],
                    supplier_data['email'], supplier_data['cep'],
                    supplier_data['endereco'], supplier_data['numero'],
                    supplier_data['complemento'], supplier_data['bairro'],
                    supplier_data['cidade'], supplier_data['estado']
                )
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except sqlite3.IntegrityError:
            self.db_manager.get_connection().rollback()
            return None

    def update(self, supplier_id, supplier_data):
        try:
            conn = self.db_manager.get_connection()
            conn.execute(
                """UPDATE T_FORNECEDOR SET
                    NOME_RAZAO_SOCIAL = ?, CPF_CNPJ = ?, TIPO_PESSOA = ?, TELEFONE = ?,
                    EMAIL = ?, CEP = ?, ENDERECO = ?, NUMERO = ?, COMPLEMENTO = ?,
                    BAIRRO = ?, CIDADE = ?, ESTADO = ?
                WHERE ID = ?""",
                (
                    supplier_data['nome_razao_social'], supplier_data['cpf_cnpj'],
                    supplier_data['tipo_pessoa'], supplier_data['telefone'],
                    supplier_data['email'], supplier_data['cep'],
                    supplier_data['endereco'], supplier_data['numero'],
                    supplier_data['complemento'], supplier_data['bairro'],
                    supplier_data['cidade'], supplier_data['estado'],
                    supplier_id
                )
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            self.db_manager.get_connection().rollback()
            return False

    def delete(self, supplier_id):
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM T_FORNECEDOR WHERE ID = ?', (supplier_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            self.db_manager.get_connection().rollback()
            return False

    def get_by_id(self, supplier_id):
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT * FROM T_FORNECEDOR WHERE ID = ?', (supplier_id,)).fetchone()

    def get_all(self):
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT ID, NOME_RAZAO_SOCIAL, CPF_CNPJ, TELEFONE, CIDADE, ESTADO FROM T_FORNECEDOR').fetchall()
