# app/supplier/supplier_repository.py
import sqlite3
from app.database.db import get_db_manager

class SupplierRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def add(self, razao_social, nome_fantasia, cnpj, phone, email, address, status):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO FORNECEDOR
                   (RAZAO_SOCIAL, NOME_FANTASIA, CNPJ, TELEFONE, EMAIL, LOGRADOURO, NUMERO, COMPLEMENTO, BAIRRO, CIDADE, UF, CEP, STATUS)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (razao_social, nome_fantasia, cnpj, phone, email, address['logradouro'], address['numero'], address['complemento'],
                 address['bairro'], address['cidade'], address['uf'], address['cep'], status)
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except sqlite3.IntegrityError:
            conn.rollback()
            return None

    def get_all(self):
        conn = self.db_manager.get_connection()
        return conn.execute("SELECT ID, RAZAO_SOCIAL, NOME_FANTASIA, CNPJ, TELEFONE, EMAIL, CIDADE, UF, STATUS FROM FORNECEDOR ORDER BY NOME_FANTASIA").fetchall()

    def get_by_id(self, supplier_id):
        conn = self.db_manager.get_connection()
        return conn.execute("SELECT * FROM FORNECEDOR WHERE ID = ?", (supplier_id,)).fetchone()

    def update(self, supplier_id, razao_social, nome_fantasia, cnpj, phone, email, address, status):
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                """UPDATE FORNECEDOR
                   SET RAZAO_SOCIAL = ?, NOME_FANTASIA = ?, CNPJ = ?, TELEFONE = ?, EMAIL = ?,
                       LOGRADOURO = ?, NUMERO = ?, COMPLEMENTO = ?, BAIRRO = ?,
                       CIDADE = ?, UF = ?, CEP = ?, STATUS = ?
                   WHERE ID = ?""",
                (razao_social, nome_fantasia, cnpj, phone, email, address['logradouro'], address['numero'], address['complemento'],
                 address['bairro'], address['cidade'], address['uf'], address['cep'], status, supplier_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            conn.rollback()
            return False

    def delete(self, supplier_id):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("UPDATE FORNECEDOR SET STATUS = 'Inativo' WHERE ID = ?", (supplier_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False

    def has_stock_entries(self, supplier_id):
        conn = self.db_manager.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM ENTRADANOTA WHERE ID_FORNECEDOR = ?", (supplier_id,))
        return cursor.fetchone() is not None

    def search(self, search_text, search_field):
        conn = self.db_manager.get_connection()

        field_map = {
            "ID": "ID",
            "Razão Social": "RAZAO_SOCIAL",
            "Nome Fantasia": "NOME_FANTASIA",
            "CNPJ": "CNPJ",
            "Cidade": "CIDADE"
        }

        column = field_map.get(search_field, "NOME_FANTASIA")

        query = f"SELECT ID, RAZAO_SOCIAL, NOME_FANTASIA, CNPJ, TELEFONE, EMAIL, CIDADE, UF FROM FORNECEDOR WHERE {column} LIKE ?"

        return conn.execute(query, (f'%{search_text}%',)).fetchall()
