# app/production/composition_operations.py
import sqlite3
from ..database import get_db_manager

def validate_bom_item(product_id, material_id):
    """
    Valida se um insumo pode ser adicionado à composição de um produto.
    Retorna (True, None) se válido, ou (False, "mensagem de erro") se inválido.
    """
    if material_id == product_id:
        return False, "Um produto não pode ser componente de si mesmo."

    conn = get_db_manager().get_connection()
    material = conn.execute('SELECT DESCRICAO, TIPO_ITEM FROM ITEM WHERE ID = ?', (material_id,)).fetchone()

    if not material or material['TIPO_ITEM'] not in ('Insumo', 'Ambos'):
        return False, f"O item '{material['DESCRICAO'] if material else ''}' é um 'Produto' e não pode ser usado como insumo."

    return True, None

def get_bom(product_id):
    """Busca a Composição (BOM) de um determinado produto."""
    conn = get_db_manager().get_connection()
    bom = conn.execute('''
        SELECT
            C.ID,
            I.ID as ID_INSUMO,
            I.DESCRICAO,
            C.QUANTIDADE,
            U.SIGLA,
            I.CUSTO_MEDIO
        FROM COMPOSICAO C
        JOIN ITEM I ON C.ID_INSUMO = I.ID
        JOIN UNIDADE U ON I.ID_UNIDADE = U.ID
        WHERE C.ID_PRODUTO = ?
    ''', (product_id,)).fetchall()
    return bom

def add_bom_item(product_id, material_id, quantity):
    """Adiciona um novo item à Composição (BOM)."""
    try:
        conn = get_db_manager().get_connection()
        conn.execute(
            'INSERT INTO COMPOSICAO (ID_PRODUTO, ID_INSUMO, QUANTIDADE) VALUES (?, ?, ?)',
            (product_id, material_id, quantity)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        get_db_manager().get_connection().rollback()
        return False

def update_bom_item(bom_id, quantity):
    """Atualiza a quantidade de um item na Composição (BOM)."""
    conn = get_db_manager().get_connection()
    conn.execute(
        'UPDATE COMPOSICAO SET QUANTIDADE = ? WHERE ID = ?',
        (quantity, bom_id)
    )
    conn.commit()

def delete_bom_item(bom_id):
    """Exclui um item da Composição (BOM)."""
    conn = get_db_manager().get_connection()
    conn.execute('DELETE FROM COMPOSICAO WHERE ID = ?', (bom_id,))
    conn.commit()

def update_composition(product_id, new_composition):
    """
    Atualiza a composição de um produto.
    Apaga a composição antiga e insere a nova.
    """
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        with conn:
            cursor.execute("DELETE FROM COMPOSICAO WHERE ID_PRODUTO = ?", (product_id,))
            if new_composition:
                cursor.executemany(
                    "INSERT INTO COMPOSICAO (ID_PRODUTO, ID_INSUMO, QUANTIDADE) VALUES (?, ?, ?)",
                    [(product_id, item['id_insumo'], item['quantidade']) for item in new_composition]
                )
        print(f"Composição do produto ID {product_id} atualizada com sucesso.")
        return True
    except sqlite3.Error as e:
        print(f"Erro ao atualizar a composição: {e}")
        return False
