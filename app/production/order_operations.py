# app/production/order_operations.py
from datetime import datetime
from ..database import get_db_manager

def create_op(due_date, items_to_produce):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        op_id = cursor.execute(
            "INSERT INTO ORDEMPRODUCAO (DATA_CRIACAO, DATA_PREVISTA, STATUS) VALUES (?, ?, 'Planejada')",
            (current_date, due_date)
        ).lastrowid
        for item in items_to_produce:
            cursor.execute(
                "INSERT INTO ORDEMPRODUCAO_ITENS (ID_ORDEM_PRODUCAO, ID_PRODUTO, QUANTIDADE_PRODUZIR) VALUES (?, ?, ?)",
                (op_id, item['id_produto'], item['quantidade'])
            )
        conn.commit()
        return op_id
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar Ordem de Produção: {e}")
        return None

def update_op(op_id, due_date, items_to_produce):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ORDEMPRODUCAO SET DATA_PREVISTA = ? WHERE ID = ?", (due_date, op_id))
        cursor.execute("DELETE FROM ORDEMPRODUCAO_ITENS WHERE ID_ORDEM_PRODUCAO = ?", (op_id,))
        for item in items_to_produce:
            cursor.execute(
                "INSERT INTO ORDEMPRODUCAO_ITENS (ID_ORDEM_PRODUCAO, ID_PRODUTO, QUANTIDADE_PRODUZIR) VALUES (?, ?, ?)",
                (op_id, item['id_produto'], item['quantidade'])
            )
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar Ordem de Produção: {e}")
        return False

def get_op_details(op_id):
    conn = get_db_manager().get_connection()
    op_master = conn.execute("SELECT * FROM ORDEMPRODUCAO WHERE ID = ?", (op_id,)).fetchone()
    if not op_master:
        return None
    op_items = conn.execute("""
        SELECT OPI.ID_PRODUTO, I.DESCRICAO, OPI.QUANTIDADE_PRODUZIR, U.SIGLA AS UNIDADE
        FROM ORDEMPRODUCAO_ITENS OPI
        JOIN ITEM I ON OPI.ID_PRODUTO = I.ID
        JOIN UNIDADE U ON I.ID_UNIDADE = U.ID
        WHERE OPI.ID_ORDEM_PRODUCAO = ?
    """, (op_id,)).fetchall()
    return {"master": dict(op_master), "items": [dict(row) for row in op_items]}

def list_ops(search_term="", search_field="id"):
    conn = get_db_manager().get_connection()
    query = "SELECT ID, DATA_CRIACAO, DATA_PREVISTA, STATUS FROM ORDEMPRODUCAO"
    params = ()
    if search_term:
        allowed_fields = {"ID": "ID", "STATUS": "STATUS"}
        column = allowed_fields.get(search_field.upper(), "ID")
        if column == "ID":
            try:
                int(search_term)
                query += f" WHERE {column} = ?"
                params = (search_term,)
            except ValueError:
                return []
        else:
            query += f" WHERE {column} LIKE ?"
            params = (f"%{search_term}%",)
    query += " ORDER BY ID DESC"
    orders = conn.execute(query, params).fetchall()
    return [dict(row) for row in orders]
