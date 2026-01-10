# app/production_line/line_operations.py
from app.database.db import get_db_manager

def create_production_line(name, description, status, items):
    """
    Cria uma nova linha de produção com seus itens.
    Retorna o ID da nova linha de produção ou None em caso de erro.
    """
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO LINHAPRODUCAO_MASTER (NOME, DESCRICAO, STATUS) VALUES (?, ?, ?)",
            (name, description, status)
        )
        line_id = cursor.lastrowid
        if items:
            item_data = [
                (line_id, item['id_produto'], item['quantidade'])
                for item in items
            ]
            cursor.executemany(
                "INSERT INTO LINHAPRODUCAO_ITEMS (ID_LINHA_PRODUCAO, ID_PRODUTO, QUANTIDADE) VALUES (?, ?, ?)",
                item_data
            )
        conn.commit()
        return line_id
    except sqlite3.IntegrityError as e:
        conn.rollback()
        print(f"Erro de integridade ao criar linha de produção: {e}")
        return None
    except Exception as e:
        conn.rollback()
        print(f"Erro ao criar linha de produção: {e}")
        return None

def get_all_production_lines():
    """Busca todas as linhas de produção com a contagem de produtos."""
    query = """
        SELECT
            lm.ID,
            lm.NOME,
            lm.STATUS,
            COUNT(li.ID_PRODUTO) AS QTD_PRODUTOS
        FROM LINHAPRODUCAO_MASTER lm
        LEFT JOIN LINHAPRODUCAO_ITEMS li ON lm.ID = li.ID_LINHA_PRODUCAO
        GROUP BY lm.ID, lm.NOME, lm.STATUS
        ORDER BY lm.NOME;
    """
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    cursor.execute(query)
    return [dict(row) for row in cursor.fetchall()]

def get_production_line_details(line_id):
    """Busca os detalhes de uma linha de produção, incluindo mestre e itens."""
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    
    # Busca os dados mestre
    cursor.execute("SELECT * FROM LINHAPRODUCAO_MASTER WHERE ID = ?", (line_id,))
    master = cursor.fetchone()
    if not master:
        return None
    
    # Busca os itens da linha
    cursor.execute("""
        SELECT
            li.ID_PRODUTO,
            i.DESCRICAO,
            li.QUANTIDADE,
            u.SIGLA AS UNIDADE
        FROM LINHAPRODUCAO_ITEMS li
        JOIN ITEM i ON li.ID_PRODUTO = i.ID
        JOIN UNIDADE u ON i.ID_UNIDADE = u.ID
        WHERE li.ID_LINHA_PRODUCAO = ?
    """, (line_id,))
    items = cursor.fetchall()
    
    return {
        "master": dict(master),
        "items": [dict(item) for item in items]
    }

def update_production_line(line_id, name, description, status, items):
    """
    Atualiza uma linha de produção existente.
    Retorna True em caso de sucesso, False em caso de erro.
    """
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        # Atualiza o mestre
        cursor.execute(
            "UPDATE LINHAPRODUCAO_MASTER SET NOME = ?, DESCRICAO = ?, STATUS = ? WHERE ID = ?",
            (name, description, status, line_id)
        )
        
        # Remove itens antigos
        cursor.execute("DELETE FROM LINHAPRODUCAO_ITEMS WHERE ID_LINHA_PRODUCAO = ?", (line_id,))
        
        # Insere novos itens
        if items:
            item_data = [
                (line_id, item['id_produto'], item['quantidade'])
                for item in items
            ]
            cursor.executemany(
                "INSERT INTO LINHAPRODUCAO_ITEMS (ID_LINHA_PRODUCAO, ID_PRODUTO, QUANTIDADE) VALUES (?, ?, ?)",
                item_data
            )
            
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao atualizar a linha de produção: {e}")
        return False

def delete_production_line(line_id):
    """
    Exclui uma linha de produção. A exclusão é em cascata para os itens.
    Retorna True em caso de sucesso, False em caso de erro.
    """
    db_manager = get_db_manager()
    conn = db_manager.get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM LINHAPRODUCAO_MASTER WHERE ID = ?", (line_id,))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print(f"Erro ao excluir a linha de produção: {e}")
        return False
