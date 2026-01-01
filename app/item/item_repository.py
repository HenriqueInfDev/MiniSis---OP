# app/item/item_repository.py
import sqlite3
from datetime import datetime
from ..database import get_db_manager

class ItemRepository:
    def __init__(self):
        self.db_manager = get_db_manager()

    def add(self, description, item_type, unit_id):
        """
        Adiciona um novo item na tabela T_ITEM.
        Retorna o ID do novo item em caso de sucesso, ou None em caso de falha.
        """
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO T_ITEM (DESCRICAO, TIPO_ITEM, ID_UNIDADE) VALUES (?, ?, ?)',
                (description, item_type, unit_id)
            )
            new_id = cursor.lastrowid
            conn.commit()
            return new_id
        except sqlite3.IntegrityError:
            self.db_manager.get_connection().rollback()
            return None

    def get_all(self):
        """Lista todos os itens com seus saldos e custos."""
        conn = self.db_manager.get_connection()
        return conn.execute('''
            SELECT I.ID, I.DESCRICAO, I.TIPO_ITEM, U.SIGLA, I.SALDO_ESTOQUE, I.CUSTO_MEDIO
            FROM T_ITEM I
            JOIN T_UNIDADE U ON I.ID_UNIDADE = U.ID
            ORDER BY I.ID
        ''').fetchall()

    def get_by_id(self, item_id):
        """Busca um item específico pelo seu ID."""
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT * FROM T_ITEM WHERE ID = ?', (item_id,)).fetchone()

    def list_units(self):
        """Lista todas as unidades de medida disponíveis."""
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT ID, NOME, SIGLA FROM T_UNIDADE').fetchall()

    def update(self, item_id, description, item_type, unit_id):
        """Atualiza os dados de um item existente."""
        try:
            conn = self.db_manager.get_connection()
            conn.execute(
                'UPDATE T_ITEM SET DESCRICAO = ?, TIPO_ITEM = ?, ID_UNIDADE = ? WHERE ID = ?',
                (description, item_type, unit_id, item_id)
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            self.db_manager.get_connection().rollback()
            return False

    def delete(self, item_id):
        """Exclui um item do banco de dados."""
        try:
            conn = self.db_manager.get_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM T_ITEM WHERE ID = ?', (item_id,))
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            self.db_manager.get_connection().rollback()
            return False

    def update_stock_and_cost(self, item_id, new_balance, new_average_cost):
        """Atualiza o saldo de estoque e o custo médio de um item."""
        conn = self.db_manager.get_connection()
        conn.execute(
            'UPDATE T_ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?',
            (new_balance, new_average_cost, item_id)
        )

    def add_stock_movement(self, item_id, movement_type, quantity, unit_value):
        """Adiciona um registro de movimentação de estoque."""
        conn = self.db_manager.get_connection()
        conn.execute(
            '''INSERT INTO T_MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, VALOR_UNITARIO, DATA_MOVIMENTO)
               VALUES (?, ?, ?, ?, ?)''',
            (item_id, movement_type, quantity, unit_value, datetime.now().isoformat())
        )

    def is_item_in_composition(self, item_id):
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT 1 FROM T_COMPOSICAO WHERE ID_INSUMO = ?', (item_id,)).fetchone() is not None

    def is_item_in_production_order(self, item_id):
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT 1 FROM T_ORDEM_PRODUCAO_ITENS WHERE ID_PRODUTO = ?', (item_id,)).fetchone() is not None

    def has_stock_movement(self, item_id):
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT 1 FROM T_MOVIMENTO WHERE ID_ITEM = ?', (item_id,)).fetchone() is not None

    def has_composition(self, item_id):
        conn = self.db_manager.get_connection()
        return conn.execute('SELECT 1 FROM T_COMPOSICAO WHERE ID_PRODUTO = ?', (item_id,)).fetchone() is not None

    def search(self, search_type, search_text):
        """Busca itens por um campo específico."""
        conn = self.db_manager.get_connection()
        base_query = '''
            SELECT I.ID, I.DESCRICAO, I.TIPO_ITEM, U.SIGLA, I.SALDO_ESTOQUE, I.CUSTO_MEDIO
            FROM T_ITEM I
            JOIN T_UNIDADE U ON I.ID_UNIDADE = U.ID
        '''
        params = ()
        if search_type == 'ID':
            query = base_query + " WHERE I.ID = ?"
            params = (int(search_text),) if search_text.isdigit() else (-1,)
        elif search_type == 'Unidade':
            query = base_query + " WHERE U.SIGLA LIKE ?"
            params = (f'%{search_text}%',)
        elif search_type == 'Quantidade':
            try:
                val = float(search_text)
                query = base_query + " WHERE I.SALDO_ESTOQUE = ?"
                params = (val,)
            except ValueError:
                return []
        else:
            query = base_query + " WHERE I.DESCRICAO LIKE ?"
            params = (f'%{search_text}%',)

        return conn.execute(query, params).fetchall()
