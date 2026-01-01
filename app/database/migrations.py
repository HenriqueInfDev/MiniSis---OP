# app/database/migrations.py

def run_migrations(connection):
    """Aplica todas as migrações de banco de dados pendentes."""
    _remove_codigo_interno_from_item(connection)


def _remove_codigo_interno_from_item(connection):
    """Remove a coluna CODIGO_INTERNO da tabela ITEM se ela existir."""
    cursor = connection.cursor()

    # Verifica se a coluna existe antes de tentar removê-la
    cursor.execute("PRAGMA table_info(ITEM)")
    columns = [column[1] for column in cursor.fetchall()]

    if 'CODIGO_INTERNO' in columns:
        try:
            # Recriar a tabela sem a coluna é a abordagem mais segura no SQLite
            # para evitar problemas com chaves estrangeiras e constraints.

            # 1. Renomear a tabela original
            cursor.execute("ALTER TABLE ITEM RENAME TO ITEM_old")

            # 2. Criar a nova tabela com a estrutura correta (sem a coluna)
            # A definição da tabela deve ser copiada da sua criação original,
            # exceto pela coluna a ser removida.
            cursor.execute("""
                CREATE TABLE ITEM (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    DESCRICAO TEXT NOT NULL UNIQUE,
                    TIPO_ITEM TEXT NOT NULL,
                    ID_UNIDADE INTEGER NOT NULL,
                    ID_FORNECEDOR_PADRAO INTEGER,
                    SALDO_ESTOQUE REAL DEFAULT 0,
                    CUSTO_MEDIO REAL DEFAULT 0,
                    FOREIGN KEY (ID_UNIDADE) REFERENCES UNIDADE(ID),
                    FOREIGN KEY (ID_FORNECEDOR_PADRAO) REFERENCES FORNECEDOR(ID)
                )
            """)

            # 3. Copiar os dados da tabela antiga para a nova
            # Certifique-se de que a lista de colunas corresponde à nova estrutura
            cursor.execute("""
                INSERT INTO ITEM (ID, DESCRICAO, TIPO_ITEM, ID_UNIDADE, ID_FORNECEDOR_PADRAO, SALDO_ESTOQUE, CUSTO_MEDIO)
                SELECT ID, DESCRICAO, TIPO_ITEM, ID_UNIDADE, ID_FORNECEDOR_PADRAO, SALDO_ESTOQUE, CUSTO_MEDIO
                FROM ITEM_old
            """)

            # 4. (Opcional) Deletar a tabela antiga
            cursor.execute("DROP TABLE ITEM_old")

            connection.commit()
            print("Coluna 'CODIGO_INTERNO' removida da tabela 'ITEM' com sucesso.")

        except Exception as e:
            print(f"Erro ao remover a coluna 'CODIGO_INTERNO': {e}")
            connection.rollback()
    else:
        print("Coluna 'CODIGO_INTERNO' já não existe na tabela 'ITEM'.")
