# app/production/order_operations.py
from datetime import datetime
from app.database.db import get_db_manager

def create_op(numero, due_date, items_to_produce):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        for item in items_to_produce:
            can_produce, message = check_stock_for_production(item['id_produto'], item['quantidade'])
            if not can_produce:
                raise Exception(message)

        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        op_id = cursor.execute(
            "INSERT INTO ORDEMPRODUCAO (NUMERO, DATA_CRIACAO, DATA_PREVISTA, STATUS) VALUES (?, ?, ?, 'Planejada')",
            (numero, current_date, due_date)
        ).lastrowid
        for item in items_to_produce:
            cursor.execute(
                "INSERT INTO ORDEMPRODUCAO_ITENS (ID_ORDEM_PRODUCAO, ID_PRODUTO, QUANTIDADE_PRODUZIR) VALUES (?, ?, ?)",
                (op_id, item['id_produto'], item['quantidade'])
            )
            consume_stock_for_production(op_id, item['id_produto'], item['quantidade'])

        conn.commit()
        return op_id
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar Ordem de Produção: {e}")
        return None

def update_op(op_id, numero, due_date, items_to_produce):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ORDEMPRODUCAO SET NUMERO = ?, DATA_PREVISTA = ? WHERE ID = ?", (numero, due_date, op_id))

        # Reverte o estoque consumido anteriormente
        op_items = get_op_details(op_id)['items']
        for item in op_items:
            return_stock_for_production(op_id, item['ID_PRODUTO'], item['QUANTIDADE_PRODUZIR'])

        cursor.execute("DELETE FROM ORDEMPRODUCAO_ITENS WHERE ID_ORDEM_PRODUCAO = ?", (op_id,))

        for item in items_to_produce:
            can_produce, message = check_stock_for_production(item['id_produto'], item['quantidade'])
            if not can_produce:
                raise Exception(message)

            cursor.execute(
                "INSERT INTO ORDEMPRODUCAO_ITENS (ID_ORDEM_PRODUCAO, ID_PRODUTO, QUANTIDADE_PRODUZIR) VALUES (?, ?, ?)",
                (op_id, item['id_produto'], item['quantidade'])
            )
            consume_stock_for_production(op_id, item['id_produto'], item['quantidade'])

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
    query = "SELECT ID, NUMERO, DATA_CRIACAO, DATA_PREVISTA, STATUS FROM ORDEMPRODUCAO"
    params = ()
    if search_term:
        allowed_fields = {"ID": "ID", "STATUS": "STATUS", "NUMERO": "NUMERO"}
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

def check_stock_for_production(product_id, quantity):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID_INSUMO, QUANTIDADE FROM COMPOSICAO WHERE ID_PRODUTO = ?", (product_id,))
    composition = cursor.fetchall()
    for insumo in composition:
        cursor.execute("SELECT SALDO_ESTOQUE FROM ITEM WHERE ID = ?", (insumo['ID_INSUMO'],))
        stock = cursor.fetchone()
        if stock['SALDO_ESTOQUE'] < insumo['QUANTIDADE'] * quantity:
            return False, f"Estoque insuficiente para o insumo ID {insumo['ID_INSUMO']}"
    return True, ""

def consume_stock_for_production(op_id, product_id, quantity):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID_INSUMO, QUANTIDADE FROM COMPOSICAO WHERE ID_PRODUTO = ?", (product_id,))
    composition = cursor.fetchall()
    for insumo in composition:
        consumed_quantity = insumo['QUANTIDADE'] * quantity
        cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = SALDO_ESTOQUE - ? WHERE ID = ?", (consumed_quantity, insumo['ID_INSUMO']))
        cursor.execute("INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, ID_ORDEM_PRODUCAO, DATA_MOVIMENTO) VALUES (?, 'Saída por OP', ?, ?, date('now'))", (insumo['ID_INSUMO'], consumed_quantity, op_id))
    conn.commit()

def return_stock_for_production(op_id, product_id, quantity):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ID_INSUMO, QUANTIDADE FROM COMPOSICAO WHERE ID_PRODUTO = ?", (product_id,))
    composition = cursor.fetchall()
    for insumo in composition:
        returned_quantity = insumo['QUANTIDADE'] * quantity
        cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = SALDO_ESTOQUE + ? WHERE ID = ?", (returned_quantity, insumo['ID_INSUMO']))
        cursor.execute("INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, ID_ORDEM_PRODUCAO, DATA_MOVIMENTO) VALUES (?, 'Retorno por OP', ?, ?, date('now'))", (insumo['ID_INSUMO'], returned_quantity, op_id))
    conn.commit()
