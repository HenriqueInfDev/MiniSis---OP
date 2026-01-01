# app/supplier/supplier_repository.py
import sqlite3
from ..database import get_db_manager

class SupplierRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def add(self, name, contact):
        """
        Adiciona um novo fornecedor na tabela TFORNECEDOR.
        Retorna o ID do novo fornecedor em caso de sucesso, ou None em caso de falha.
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO TFORNECEDOR (NOME, CONTATO) VALUES (?, ?)',
                (name, contact)
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except sqlite3.IntegrityError:
            self.db_manager.get_connection().rollback()
            return None

    def get_all(self):
        """Lista todos os fornecedores."""
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT ID, NOME, CONTATO FROM TFORNECEDOR ORDER BY NOME').fetchall()

    def get_by_id(self, supplier_id):
        """Busca um fornecedor específico pelo seu ID."""
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT * FROM TFORNECEDOR WHERE ID = ?', (supplier_id,)).fetchone()

    def update(self, supplier_id, name, contact):
        """Atualiza os dados de um fornecedor existente."""
        try:
            conn = self.db_manager.get_connection()
            conn.execute(
                'UPDATE TFORNECEDOR SET NOME = ?, CONTATO = ? WHERE ID = ?',
                (name, contact, supplier_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            self.db_manager.get_connection().rollback()
            return False

    def delete(self, supplier_id):
        """Exclui um fornecedor do banco de dados."""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM TFORNECEDOR WHERE ID = ?', (supplier_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            self.db_manager.get_connection().rollback()
            return False

    def search(self, search_text):
        """Busca fornecedores por nome."""
        conn = self.db_manager.get_connection()
        return conn.execute(
            'SELECT ID, NOME, CONTATO FROM TFORNECEDOR WHERE NOME LIKE ? ORDER BY NOME',
            (f'%{search_text}%',)
        ).fetchall()
