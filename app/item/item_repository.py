# app/item/item_repository.py
from app.database.db import get_db_manager

class ItemRepository:
    def __init__(self):
        self.db_manager = get_db_manager()
        self.connection = self.db_manager.get_connection()

    def add(self, description, item_type, unit_id, id_fornecedor_padrao):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO ITEM (DESCRICAO, TIPO_ITEM, ID_UNIDADE, ID_FORNECEDOR_PADRAO) VALUES (?, ?, ?, ?)",
                (description, item_type, unit_id, id_fornecedor_padrao)
            )
            self.connection.commit()
            return cursor.lastrowid
        except self.connection.IntegrityError:
            self.connection.rollback()
            return None

    def get_all(self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT i.ID, i.DESCRICAO, i.TIPO_ITEM, u.SIGLA, i.SALDO_ESTOQUE, i.CUSTO_MEDIO
            FROM ITEM i
            JOIN UNIDADE u ON i.ID_UNIDADE = u.ID
            ORDER BY i.DESCRICAO
        """)
        return cursor.fetchall()

    def get_by_id(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM ITEM WHERE ID = ?", (item_id,))
        return cursor.fetchone()

    def list_units(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT ID, NOME, SIGLA FROM UNIDADE ORDER BY NOME")
        return cursor.fetchall()

    def update(self, item_id, description, item_type, unit_id, id_fornecedor_padrao):
        cursor = self.connection.cursor()
        try:
            cursor.execute(
                "UPDATE ITEM SET DESCRICAO = ?, TIPO_ITEM = ?, ID_UNIDADE = ?, ID_FORNECEDOR_PADRAO = ? WHERE ID = ?",
                (description, item_type, unit_id, id_fornecedor_padrao, item_id)
            )
            self.connection.commit()
            return True
        except self.connection.IntegrityError:
            self.connection.rollback()
            return False

    def delete(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM ITEM WHERE ID = ?", (item_id,))
        self.connection.commit()
        return cursor.rowcount > 0

    def is_item_in_composition(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM COMPOSICAO WHERE ID_INSUMO = ?", (item_id,))
        return cursor.fetchone() is not None

    def is_item_in_production_order(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM ORDEMPRODUCAO_ITENS WHERE ID_PRODUTO = ?", (item_id,))
        return cursor.fetchone() is not None

    def has_stock_movement(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM MOVIMENTO WHERE ID_ITEM = ?", (item_id,))
        return cursor.fetchone() is not None

    def has_composition(self, item_id):
        cursor = self.connection.cursor()
        cursor.execute("SELECT 1 FROM COMPOSICAO WHERE ID_PRODUTO = ?", (item_id,))
        return cursor.fetchone() is not None

    def search(self, search_type, search_text):
        cursor = self.connection.cursor()
        query = "SELECT i.ID, i.DESCRICAO, i.TIPO_ITEM, u.SIGLA, i.SALDO_ESTOQUE, i.CUSTO_MEDIO FROM ITEM i JOIN UNIDADE u ON i.ID_UNIDADE = u.ID"
        if search_type == "description":
            query += " WHERE i.DESCRICAO LIKE ?"
            params = (f"%{search_text}%",)
        else: # id
            query += " WHERE i.ID = ?"
            params = (search_text,)
        query += " ORDER BY i.DESCRICAO"
        cursor.execute(query, params)
        return cursor.fetchall()

    def update_stock_and_cost(self, item_id, new_balance, new_average_cost):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?", (new_balance, new_average_cost, item_id))
        self.connection.commit()

    def add_stock_movement(self, item_id, movement_type, quantity, unit_value):
        cursor = self.connection.cursor()
        cursor.execute("INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, VALOR_UNITARIO, DATA_MOVIMENTO) VALUES (?, ?, ?, ?, date('now'))", (item_id, movement_type, quantity, unit_value))
        self.connection.commit()
