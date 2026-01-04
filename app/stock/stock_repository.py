# app/stock/stock_repository.py
import sqlite3
from app.database.db import get_db_manager

class StockRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def create_entry(self, entry_date, typing_date, note_number, observacao):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO ENTRADANOTA (DATA_ENTRADA, DATA_DIGITACAO, NUMERO_NOTA, OBSERVACAO, STATUS, VALOR_TOTAL) VALUES (?, ?, ?, ?, 'Em Aberto', 0.0)",
                (entry_date, typing_date, note_number, observacao)
            )
            entry_id = cursor.lastrowid
            conn.commit()
            return entry_id
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in create_entry: {e}")
            return None

    def update_entry_master(self, entry_id, entry_date, typing_date, note_number, observacao, total_value):
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "UPDATE ENTRADANOTA SET DATA_ENTRADA = ?, DATA_DIGITACAO = ?, NUMERO_NOTA = ?, OBSERVACAO = ?, VALOR_TOTAL = ? WHERE ID = ?",
                (entry_date, typing_date, note_number, observacao, total_value, entry_id)
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
                        "INSERT INTO ENTRADANOTA_ITENS (ID_ENTRADA, ID_INSUMO, ID_FORNECEDOR, QUANTIDADE, VALOR_UNITARIO) VALUES (?, ?, ?, ?, ?)",
                        [(entry_id, item['id_insumo'], item['id_fornecedor'], item['quantidade'], item['valor_unitario']) for item in items]
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
            SELECT tei.ID, tei.ID_INSUMO, tei.ID_FORNECEDOR, f.NOME_FANTASIA as FORNECEDOR, i.DESCRICAO, u.SIGLA, tei.QUANTIDADE, tei.VALOR_UNITARIO
            FROM ENTRADANOTA_ITENS tei
            JOIN ITEM i ON tei.ID_INSUMO = i.ID
            JOIN UNIDADE u ON i.ID_UNIDADE = u.ID
            JOIN FORNECEDOR f ON tei.ID_FORNECEDOR = f.ID
            WHERE tei.ID_ENTRADA = ?
        """, (entry_id,)).fetchall()
        return {"master": dict(master), "items": [dict(row) for row in items]}

    def list_entries(self, search_term="", search_field="ID"):
        conn = self.db_manager.get_connection()
        query = """
            SELECT T.ID, T.DATA_ENTRADA, T.DATA_DIGITACAO, T.NUMERO_NOTA, T.VALOR_TOTAL, T.STATUS
            FROM ENTRADANOTA T
        """
        params = ()
        if search_term:
            # Mapeamento dos campos da UI para as colunas do banco de dados
            field_map = {
                "ID": "T.ID",
                "Nº Nota": "T.NUMERO_NOTA",
                "Data Entrada": "T.DATA_ENTRADA",
                "Valor Total": "T.VALOR_TOTAL",
                "Status": "T.STATUS"
            }
            column = field_map.get(search_field, "T.ID")

            # Tratamento especial para cada tipo de campo
            if search_field == "ID":
                if search_term.isdigit():
                    query += f" WHERE {column} = ?"
                    params = (int(search_term),)
                else: # Se o ID não for um número, não retorna nada
                    return []
            elif search_field == "Valor Total":
                try:
                    # Permite pesquisar valores aproximados
                    query += f" WHERE {column} >= ? AND {column} < ?"
                    val = float(search_term.replace(',', '.'))
                    params = (val, val + 1)
                except ValueError:
                    return [] # Se não for um número válido, não retorna nada
            else: # Para Nº Nota, Data Entrada, Status
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

    def reopen_entry(self, entry_id):
        conn = self.db_manager.get_connection()
        details = self.get_entry_details(entry_id)
        if not details or details['master']['STATUS'] != 'Finalizada':
            return False

        try:
            with conn:
                cursor = conn.cursor()
                for item in details['items']:
                    insumo_id, quantity, unit_cost = item['ID_INSUMO'], item['QUANTIDADE'], item['VALOR_UNITARIO']

                    # Estorna o estoque
                    current_item = cursor.execute("SELECT SALDO_ESTOQUE, CUSTO_MEDIO FROM ITEM WHERE ID = ?", (insumo_id,)).fetchone()
                    old_balance, old_avg_cost = current_item['SALDO_ESTOQUE'], current_item['CUSTO_MEDIO']

                    new_balance = old_balance - quantity

                    # Recalcula o custo médio.
                    # Este é o inverso da fórmula de entrada.
                    # Se o saldo zerar, o custo médio também zera.
                    new_avg_cost = ((old_balance * old_avg_cost) - (quantity * unit_cost)) / new_balance if new_balance > 0 else 0

                    cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?", (new_balance, new_avg_cost, insumo_id))

                    # Adiciona um movimento de estorno para rastreabilidade
                    cursor.execute(
                        "INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, VALOR_UNITARIO, DATA_MOVIMENTO) VALUES (?, 'Estorno de Entrada', ?, ?, ?)",
                        (insumo_id, -quantity, unit_cost, details['master']['DATA_ENTRADA'])
                    )

                # Muda o status da nota para 'Em Aberto'
                cursor.execute("UPDATE ENTRADANOTA SET STATUS = 'Em Aberto' WHERE ID = ?", (entry_id,))
            return True
        except sqlite3.Error as e:
            print(f"Database error in reopen_entry: {e}")
            conn.rollback()
            return False

    def get_item_details(self, item_id):
        conn = self.db_manager.get_connection()
        query = """
            SELECT i.*, f.NOME_FANTASIA AS NOME_FANTASIA_PADRAO, u.SIGLA
            FROM ITEM i
            LEFT JOIN FORNECEDOR f ON i.ID_FORNECEDOR_PADRAO = f.ID
            LEFT JOIN UNIDADE u ON i.ID_UNIDADE = u.ID
            WHERE i.ID = ?
        """
        return conn.execute(query, (item_id,)).fetchone()
