# app/production/order_operations.py
from datetime import datetime
from app.database.db import get_db_manager

def create_op(numero, due_date, items_to_produce):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        op_id = cursor.execute(
            "INSERT INTO ORDEMPRODUCAO (NUMERO, DATA_CRIACAO, DATA_PREVISTA, STATUS) VALUES (?, ?, ?, 'Em Andamento')",
            (numero, current_date, due_date)
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

def update_op(op_id, numero, due_date, items_to_produce):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ORDEMPRODUCAO SET NUMERO = ?, DATA_PREVISTA = ? WHERE ID = ?", (numero, due_date, op_id))
        
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

def finalize_op(op_id, produced_quantity):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        # Obter detalhes da OP
        op_details = get_op_details(op_id)
        if not op_details:
            raise Exception("Ordem de Produção não encontrada.")

        total_cost = 0
        for item in op_details['items']:
            # Verificar estoque antes de consumir
            can_produce, message = check_stock_for_production(item['ID_PRODUTO'], produced_quantity)
            if not can_produce:
                raise Exception(message)

            # Consumir insumos e calcular custo
            cost = consume_stock_for_production(op_id, item['ID_PRODUTO'], produced_quantity)
            total_cost += cost
            
            # Dar entrada no produto acabado
            increase_product_stock(op_id, item['ID_PRODUTO'], produced_quantity, cost)

        # Atualizar a OP com o status, quantidade produzida e custo
        cursor.execute(
            "UPDATE ORDEMPRODUcao SET STATUS = 'Concluída', QUANTIDADE_PRODUZIDA = ?, CUSTO_TOTAL = ? WHERE ID = ?",
            (produced_quantity, total_cost, op_id)
        )
        
        conn.commit()
        return True, "Ordem de Produção finalizada com sucesso."
    except Exception as e:
        conn.rollback()
        print(f"Erro ao finalizar Ordem de Produção: {e}")
        return False, str(e)

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
    
    items_with_cost = []
    for item in op_items:
        item_dict = dict(item)
        item_dict['CUSTO_MEDIO'] = calculate_product_cost(item_dict['ID_PRODUTO'])
        items_with_cost.append(item_dict)

    return {"master": dict(op_master), "items": items_with_cost}

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
    cursor.execute("SELECT ID_INSUMO, QUANTIDADE, CUSTO_MEDIO FROM COMPOSICAO C JOIN ITEM I ON C.ID_INSUMO = I.ID WHERE C.ID_PRODUTO = ?", (product_id,))
    composition = cursor.fetchall()
    total_cost = 0
    for insumo in composition:
        consumed_quantity = insumo['QUANTIDADE'] * quantity
        cost = insumo['CUSTO_MEDIO'] * consumed_quantity
        total_cost += cost
        cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = SALDO_ESTOQUE - ? WHERE ID = ?", (consumed_quantity, insumo['ID_INSUMO']))
        cursor.execute("INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, ID_ORDEM_PRODUCAO, DATA_MOVIMENTO) VALUES (?, 'Saída por OP', ?, ?, date('now'))", (insumo['ID_INSUMO'], consumed_quantity, op_id))
    return total_cost

def increase_product_stock(op_id, product_id, quantity, cost):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    
    # Get current stock and average cost
    cursor.execute("SELECT SALDO_ESTOQUE, CUSTO_MEDIO FROM ITEM WHERE ID = ?", (product_id,))
    current_stock, current_avg_cost = cursor.fetchone()

    # Calculate new average cost
    new_stock = current_stock + quantity
    if new_stock > 0:
        new_avg_cost = ((current_stock * current_avg_cost) + cost) / new_stock
    else:
        new_avg_cost = current_avg_cost

    cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?", (new_stock, new_avg_cost, product_id))
    cursor.execute("INSERT INTO MOVIMENTO (ID_ITEM, TIPO_MOVIMENTO, QUANTIDADE, ID_ORDEM_PRODUCAO, DATA_MOVIMENTO) VALUES (?, 'Entrada por OP', ?, ?, date('now'))", (product_id, quantity, op_id))

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

def calculate_product_cost(product_id):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT SUM(C.QUANTIDADE * I.CUSTO_MEDIO) AS CUSTO_TOTAL
        FROM COMPOSICAO C
        JOIN ITEM I ON C.ID_INSUMO = I.ID
        WHERE C.ID_PRODUTO = ?
    """, (product_id,))
    result = cursor.fetchone()
    return result['CUSTO_TOTAL'] if result and result['CUSTO_TOTAL'] is not None else 0

def cancel_op(op_id):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ORDEMPRODUCAO SET STATUS = 'Cancelada' WHERE ID = ?", (op_id,))
        conn.commit()
        return True, "Ordem de Produção cancelada com sucesso."
    except Exception as e:
        conn.rollback()
        print(f"Erro ao cancelar Ordem de Produção: {e}")
        return False, str(e)

def _reverse_production_stock_update(cursor, product_id, produced_quantity, production_cost):
    # Get current stock and average cost
    cursor.execute("SELECT SALDO_ESTOQUE, CUSTO_MEDIO FROM ITEM WHERE ID = ?", (product_id,))
    current_stock, current_avg_cost = cursor.fetchone()

    # Calculate new average cost by removing the production cost
    new_stock = current_stock - produced_quantity
    if new_stock > 0:
        current_total_value = current_stock * current_avg_cost
        new_avg_cost = (current_total_value - production_cost) / new_stock
        if new_avg_cost < 0:
            new_avg_cost = 0 # Cost should not be negative
    else:
        new_avg_cost = 0 # If stock is zero, cost is zero

    cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = ?, CUSTO_MEDIO = ? WHERE ID = ?", (new_stock, new_avg_cost, product_id))


def delete_op(op_id):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        # Get OP details before deleting
        cursor.execute("SELECT * FROM ORDEMPRODUCAO WHERE ID = ?", (op_id,))
        op_master = cursor.fetchone()
        
        if not op_master:
            raise Exception("Ordem de Produção não encontrada.")

        op_details = get_op_details(op_id)

        status = op_master['STATUS']
        
        if status == 'Concluída':
            produced_quantity = op_master['QUANTIDADE_PRODUZIDA']
            total_cost = op_master['CUSTO_TOTAL']

            if produced_quantity and produced_quantity > 0 and total_cost is not None:
                for item in op_details['items']:
                    product_id = item['ID_PRODUTO']
                    
                    # Revert stock and cost for the produced item
                    _reverse_production_stock_update(cursor, product_id, produced_quantity, total_cost)
                    
                    # Return consumed components to stock
                    cursor.execute("SELECT ID_INSUMO, QUANTIDADE FROM COMPOSICAO WHERE ID_PRODUTO = ?", (product_id,))
                    composition = cursor.fetchall()
                    for insumo in composition:
                        returned_quantity = insumo['QUANTIDADE'] * produced_quantity
                        cursor.execute("UPDATE ITEM SET SALDO_ESTOQUE = SALDO_ESTOQUE + ? WHERE ID = ?", (returned_quantity, insumo['ID_INSUMO']))

        # Delete all movements related to this OP
        cursor.execute("DELETE FROM MOVIMENTO WHERE ID_ORDEM_PRODUCAO = ?", (op_id,))
        
        # Delete items from the production order
        cursor.execute("DELETE FROM ORDEMPRODUCAO_ITENS WHERE ID_ORDEM_PRODUCAO = ?", (op_id,))
        
        # Finally, delete the production order itself
        cursor.execute("DELETE FROM ORDEMPRODUCAO WHERE ID = ?", (op_id,))
        
        conn.commit()
        return True, "Ordem de Produção excluída com sucesso."
    except Exception as e:
        conn.rollback()
        print(f"Erro ao excluir Ordem de Produção: {e}")
        return False, str(e)

def reopen_op(op_id):
    conn = get_db_manager().get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE ORDEMPRODUCAO SET STATUS = 'Em Andamento' WHERE ID = ?", (op_id,))
        conn.commit()
        return True, "Ordem de Produção reaberta com sucesso."
    except Exception as e:
        conn.rollback()
        print(f"Erro ao reabrir Ordem de Produção: {e}")
        return False, str(e)
