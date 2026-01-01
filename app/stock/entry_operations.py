# app/stock/entry_operations.py
from datetime import datetime
import sqlite3
from ..database import get_db_manager

def create_entry(entry_date, supplier, note_number):
    """
    Cria uma nova nota de entrada de insumos com status 'Em Aberto'.
    Retorna o ID da nova entrada.
    """
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO T_ENTRADA_NOTA (DATA_ENTRADA, FORNECEDOR, NUMERO_NOTA, STATUS) VALUES (?, ?, ?, 'Em Aberto')",
            (entry_date, supplier, note_number)
        )
        entry_id = cursor.lastrowid
        conn.commit()
        return entry_id
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Erro ao criar nota de entrada: {e}")
        return None

def update_entry_master(entry_id, entry_date, supplier, note_number):
    """Atualiza os dados mestre de uma nota de entrada."""
    conn = get_db_manager().get_connection()
    try:
        conn.execute(
            "UPDATE T_ENTRADA_NOTA SET DATA_ENTRADA = ?, FORNECEDOR = ?, NUMERO_NOTA = ? WHERE ID = ?",
            (entry_date, supplier, note_number, entry_id)
        )
        conn.commit()
        return True
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Erro ao atualizar dados mestre da entrada: {e}")
        return False

def update_entry_items(entry_id, items):
    """
    Atualiza todos os itens de uma nota de entrada.
    A lista 'items' deve conter dicionários com 'id_insumo', 'quantidade', 'valor_unitario'.
    """
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        with conn:
            # Apaga os itens antigos
            cursor.execute("DELETE FROM T_ENTRADA_NOTA_ITENS WHERE ID_ENTRADA = ?", (entry_id,))
            # Insere os novos itens
            if items:
                cursor.executemany(
                    "INSERT INTO T_ENTRADA_NOTA_ITENS (ID_ENTRADA, ID_INSUMO, QUANTIDADE, VALOR_UNITARIO) VALUES (?, ?, ?, ?)",
                    [(entry_id, item['id_insumo'], item['quantidade'], item['valor_unitario']) for item in items]
                )
        return True
    except sqlite3.Error as e:
        print(f"Erro ao atualizar itens da nota de entrada: {e}")
        return False

def get_entry_details(entry_id):
    """Busca os detalhes completos de uma nota de entrada (mestre e itens)."""
    conn = get_db_manager().get_connection()
    master = conn.execute("SELECT * FROM T_ENTRADA_NOTA WHERE ID = ?", (entry_id,)).fetchone()
    if not master:
        return None

    items = conn.execute("""
        SELECT
            tei.ID,
            tei.ID_INSUMO,
            ti.DESCRICAO,
            tu.SIGLA,
            tei.QUANTIDADE,
            tei.VALOR_UNITARIO
        FROM T_ENTRADA_NOTA_ITENS tei
        JOIN T_ITEM ti ON tei.ID_INSUMO = ti.ID
        JOIN T_UNIDADE tu ON ti.ID_UNIDADE = tu.ID
        WHERE tei.ID_ENTRADA = ?
    """, (entry_id,)).fetchall()

    return {"master": dict(master), "items": [dict(row) for row in items]}

def list_entries(search_term="", search_field="id"):
    """Lista todas as notas de entrada, com filtro opcional."""
    conn = get_db_manager().get_connection()
    query = "SELECT ID, DATA_ENTRADA, FORNECEDOR, NUMERO_NOTA, VALOR_TOTAL, STATUS FROM T_ENTRADA_NOTA"
    params = ()

    if search_term:
        field_map = {"ID": "ID", "FORNECEDOR": "FORNECEDOR", "Nº NOTA": "NUMERO_NOTA", "STATUS": "STATUS"}
        column = field_map.get(search_field, "ID")

        if column == "ID" and search_term.isdigit():
            query += f" WHERE {column} = ?"
            params = (int(search_term),)
        else:
            query += f" WHERE {column} LIKE ?"
            params = (f'%{search_term}%',)

    query += " ORDER BY ID DESC"
    entries = conn.execute(query, params).fetchall()
    return [dict(row) for row in entries]

def finalize_entry(entry_id):
    """
    Finaliza uma nota de entrada, atualizando o estoque e o custo médio dos insumos.
    Retorna (True, "Mensagem") em caso de sucesso, ou (False, "Mensagem de Erro").
    """
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()

    details = get_entry_details(entry_id)
    if not details:
        return False, "Nota de entrada não encontrada."

    if details['master']['STATUS'] == 'Finalizada':
        return False, "Esta nota de entrada já foi finalizada."

    if not details['items']:
        return False, "Não é possível finalizar uma entrada sem itens."

    try:
        with conn:
            total_value = 0
            for item in details['items']:
                insumo_id = item['ID_INSUMO']
                quantity = item['QUANTIDADE']
                unit_cost = item['VALOR_UNITARIO']
                total_item_value = quantity * unit_cost
                total_value += total_item_value

                # 1. Obter o saldo e custo atuais do insumo
                current_item = cursor.execute(
                    "SELECT SALDO_ESTOQUE, CUSTO_MEDIO FROM T_ITEM WHERE ID = ?",
                    (insumo_id,)
                ).fetchone()

                old_balance = current_item['SALDO_ESTOQUE']
                old_avg_cost = current_item['CUSTO_MEDIO']

                # 2. Calcular novo saldo e novo custo médio
                new_balance = old_balance + quantity
                new_avg_cost = ((old_balance * old_avg_cost) + (quantity * unit_cost)) / new_balance if new_balance > 0 else 0

                # 3. Atualizar o saldo e custo médio na T_ITEM
                cursor.execute(
                    "UPDATE T_ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?",
                    (new_balance, new_avg_cost, insumo_id)
                )

                # 4. Registrar na T_MOVIMENTO
                cursor.execute(
                    """INSERT INTO T_MOVIMENTO
                       (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, VALOR_UNITARIO, DATA_MOVIMENTO, ID_ORDEM_PRODUCAO)
                       VALUES (?, 'Entrada por Nota', ?, ?, ?, NULL)""",
                    (insumo_id, quantity, unit_cost, details['master']['DATA_ENTRADA'])
                )

            # 5. Atualizar o valor total e o status da nota de entrada
            cursor.execute(
                "UPDATE T_ENTRADA_NOTA SET VALOR_TOTAL = ?, STATUS = 'Finalizada' WHERE ID = ?",
                (total_value, entry_id)
            )

        return True, f"Entrada #{entry_id} finalizada com sucesso. Valor total: {total_value:.2f}"

    except sqlite3.Error as e:
        return False, f"Erro no banco de dados ao finalizar a entrada: {e}"
    except Exception as e:
        return False, f"Um erro inesperado ocorreu: {e}"
