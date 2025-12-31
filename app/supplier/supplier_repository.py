# app/supplier/supplier_repository.py
import sqlite3
from ..database import get_db_manager

class SupplierRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def add(self, name, cnpj, phone, email):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO TFORNECEDOR (NOME, CNPJ, TELEFONE, EMAIL) VALUES (?, ?, ?, ?)",
                (name, cnpj, phone, email)
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except sqlite3.IntegrityError:
            conn.rollback()
            return None

    def get_all(self):
        conn = self.db_manager.get_connection()
        return conn.execute("SELECT ID, NOME, CNPJ, TELEFONE, EMAIL FROM TFORNECEDOR ORDER BY NOME").fetchall()

    def get_by_id(self, supplier_id):
        conn = self.db_manager.get_connection()
        return conn.execute("SELECT * FROM TFORNECEDOR WHERE ID = ?", (supplier_id,)).fetchone()

    def update(self, supplier_id, name, cnpj, phone, email):
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "UPDATE TFORNECEDOR SET NOME = ?, CNPJ = ?, TELEFONE = ?, EMAIL = ? WHERE ID = ?",
                (name, cnpj, phone, email, supplier_id)
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
            cursor.execute("DELETE FROM TFORNECEDOR WHERE ID = ?", (supplier_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            conn.rollback()
            return False
