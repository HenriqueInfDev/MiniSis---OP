# app/sales/sale_repository.py
import sqlite3
from app.database.db import get_db_manager

class SaleRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def create_sale(self, sale_date, observacao, total_value):
        conn = self.db_manager.get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO SAIDA (DATA_SAIDA, OBSERVACAO, STATUS, VALOR_TOTAL) VALUES (?, ?, 'Em Aberto', ?)",
                (sale_date, observacao, total_value)
            )
            sale_id = cursor.lastrowid
            conn.commit()
            return sale_id
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in create_sale: {e}")
            return None

    def update_sale_master(self, sale_id, sale_date, observacao, total_value):
        conn = self.db_manager.get_connection()
        try:
            conn.execute(
                "UPDATE SAIDA SET DATA_SAIDA = ?, OBSERVACAO = ?, VALOR_TOTAL = ? WHERE ID = ?",
                (sale_date, observacao, total_value, sale_id)
            )
            conn.commit()
            return True
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in update_sale_master: {e}")
            return False

    def update_sale_items(self, sale_id, items):
        conn = self.db_manager.get_connection()
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM SAIDA_ITENS WHERE ID_SAIDA = ?", (sale_id,))
                if items:
                    cursor.executemany(
                        "INSERT INTO SAIDA_ITENS (ID_SAIDA, ID_PRODUTO, QUANTIDADE, VALOR_UNITARIO) VALUES (?, ?, ?, ?)",
                        [(sale_id, item['id_produto'], item['quantidade'], item['valor_unitario']) for item in items]
                    )
            return True
        except sqlite3.Error as e:
            print(f"Database error in update_sale_items: {e}")
            return False

    def get_sale_details(self, sale_id):
        conn = self.db_manager.get_connection()
        master = conn.execute("SELECT * FROM SAIDA WHERE ID = ?", (sale_id,)).fetchone()
        if not master:
            return None
        items = conn.execute("""
            SELECT si.ID, si.ID_PRODUTO, i.DESCRICAO, u.SIGLA, si.QUANTIDADE, si.VALOR_UNITARIO
            FROM SAIDA_ITENS si
            JOIN ITEM i ON si.ID_PRODUTO = i.ID
            JOIN UNIDADE u ON i.ID_UNIDADE = u.ID
            WHERE si.ID_SAIDA = ?
        """, (sale_id,)).fetchall()
        return {"master": dict(master), "items": [dict(row) for row in items]}

    def list_sales(self, search_term="", search_field="id"):
        conn = self.db_manager.get_connection()
        query = "SELECT ID, DATA_SAIDA, VALOR_TOTAL, STATUS FROM SAIDA"
        params = ()
        if search_term:
            if search_field == "id" and search_term.isdigit():
                query += " WHERE ID = ?"
                params = (int(search_term),)
            else:
                query += f" WHERE {search_field} LIKE ?"
                params = (f'%{search_term}%',)
        query += " ORDER BY ID DESC"
        return [dict(row) for row in conn.execute(query, params).fetchall()]

    def finalize_sale(self, sale_id):
        conn = self.db_manager.get_connection()
        details = self.get_sale_details(sale_id)
        if not details or details['master']['STATUS'] == 'Finalizada':
            return False

        try:
            with conn:
                cursor = conn.cursor()
                for item in details['items']:
                    produto_id, quantity = item['ID_PRODUTO'], item['QUANTIDADE']
                    # Deduz do stock
                    cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = SALDO_ESTOQUE - ? WHERE ID = ?", (quantity, produto_id))
                    # Regista o movimento
                    cursor.execute(
                        "INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, VALOR_UNITARIO, DATA_MOVIMENTO) VALUES (?, 'Saída por Venda', ?, ?, ?)",
                        (produto_id, -quantity, item['VALOR_UNITARIO'], details['master']['DATA_SAIDA'])
                    )
                # Atualiza o status da saída
                cursor.execute("UPDATE SAIDA SET STATUS = 'Finalizada' WHERE ID = ?", (sale_id,))
            return True
        except sqlite3.Error as e:
            conn.rollback()
            print(f"Database error in finalize_sale: {e}")
            return False
