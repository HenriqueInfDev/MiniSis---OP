# app/stock/stock_repository.py
import sqlite3
from app.database.db import get_db_manager

class StockRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def create_entry(self, data, entry_date, typing_date, supplier_id, note_number, observacao):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ENTRADANOTA (DATA, DATA_ENTRADA, DATA_DIGITACAO, ID_FORNECEDOR, NUMERO_NOTA, OBSERVACAO, STATUS) VALUES (?, ?, ?, ?, ?, ?, 'Em Aberto')",
                (data, entry_date, typing_date, supplier_id, note_number, observacao)
            )
            entry_id = cursor.lastrowid
            conn.commit()
            return entry_id
        except sqlite3.Error:
            conn.rollback()
            return None

    def update_entry_master(self, entry_id, data, entry_date, typing_date, supplier_id, note_number, observacao):
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "UPDATE ENTRADANOTA SET DATA = ?, DATA_ENTRADA = ?, DATA_DIGITACAO = ?, ID_FORNECEDOR = ?, NUMERO_NOTA = ?, OBSERVACAO = ? WHERE ID = ?",
                (data, entry_date, typing_date, supplier_id, note_number, observacao, entry_id)
            )
            conn.commit()
            return True
        except sqlite3.Error:
            conn.rollback()
            return False

    def update_entry_items(self, entry_id, items):
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM ENTRADANOTA_ITENS WHERE ID_ENTRADA = ?", (entry_id,))
                if items:
                    cursor.executemany(
                        "INSERT INTO ENTRADANOTA_ITENS (ID_ENTRADA, ID_INSUMO, QUANTIDADE, VALOR_UNITARIO) VALUES (?, ?, ?, ?)",
                        [(entry_id, item['id_insumo'], item['quantidade'], item['valor_unitario']) for item in items]
                    )
            return True
        except sqlite3.Error:
            return False

    def get_entry_details(self, entry_id):
        conn = self.db_manager.get_connection()
        master = conn.execute("SELECT * FROM ENTRADANOTA WHERE ID = ?", (entry_id,)).fetchone()
        if not master:
            return None
        items = conn.execute("""
            SELECT tei.ID, tei.ID_INSUMO, i.DESCRICAO, u.SIGLA, tei.QUANTIDADE, tei.VALOR_UNITARIO
            FROM ENTRADANOTA_ITENS tei
            JOIN ITEM i ON tei.ID_INSUMO = i.ID
            JOIN UNIDADE u ON i.ID_UNIDADE = u.ID
            WHERE tei.ID_ENTRADA = ?
        """, (entry_id,)).fetchall()
        return {"master": dict(master), "items": [dict(row) for row in items]}

    def list_entries(self, search_term="", search_field="id"):
        conn = self.db_manager.get_connection()
        query = """
            SELECT T.ID, T.DATA_ENTRADA, T.DATA_DIGITACAO, F.NOME_FANTASIA AS FORNECEDOR, T.NUMERO_NOTA, T.VALOR_TOTAL, T.STATUS
            FROM ENTRADANOTA T
            LEFT JOIN FORNECEDOR F ON T.ID_FORNECEDOR = F.ID
        """
        params = ()
        if search_term:
            field_map = {"ID": "T.ID", "FORNECEDOR": "F.NOME_FANTASIA", "Nº NOTA": "T.NUMERO_NOTA", "STATUS": "T.STATUS"}
            column = field_map.get(search_field, "T.ID")
            if column == "T.ID" and search_term.isdigit():
                query += f" WHERE {column} = ?"
                params = (int(search_term),)
            else:
                query += f" WHERE {column} LIKE ?"
                params = (f'%{search_term}%',)
        query += " ORDER BY T.ID DESC"
        return [dict(row) for row in conn.execute(query, params).fetchall()]

    def finalize_entry(self, entry_id):
        conn = self.db_manager.get_connection()
        details = self.get_entry_details(entry_id)
        if not details or details['master']['STATUS'] == 'Finalizada':
            return False, 0

        try:
            with conn:
                cursor = conn.cursor()
                total_value = 0
                for item in details['items']:
                    insumo_id, quantity, unit_cost = item['ID_INSUMO'], item['QUANTIDADE'], item['VALOR_UNITARIO']
                    total_value += quantity * unit_cost
                    current_item = cursor.execute("SELECT SALDO_ESTOQUE, CUSTO_MEDIO FROM ITEM WHERE ID = ?", (insumo_id,)).fetchone()
                    old_balance, old_avg_cost = current_item['SALDO_ESTOQUE'], current_item['CUSTO_MEDIO']
                    new_balance = old_balance + quantity
                    new_avg_cost = ((old_balance * old_avg_cost) + (quantity * unit_cost)) / new_balance if new_balance > 0 else 0
                    cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?", (new_balance, new_avg_cost, insumo_id))
                    cursor.execute(
                        "INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, VALOR_UNITARIO, DATA_MOVIMENTO) VALUES (?, 'Entrada por Nota', ?, ?, ?)",
                        (insumo_id, quantity, unit_cost, details['master']['DATA_ENTRADA'])
                    )
                cursor.execute("UPDATE ENTRADANOTA SET VALOR_TOTAL = ?, STATUS = 'Finalizada' WHERE ID = ?", (total_value, entry_id))
            return True, total_value
        except sqlite3.Error:
            conn.rollback()
            return False, 0
