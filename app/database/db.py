# app/database/db.py
import sqlite3
import os
import atexit
import logging

class DatabaseManager:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.db_path = self._get_db_path()
            self.connection = None
            self.initialize_database()
            atexit.register(self.close_connection)
            self.initialized = True

    def _get_db_path(self):
        # Build a path relative to the project root
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        return os.path.join(project_root, "Gestão de Produção", "Dados", "DADOS.DB")

    def initialize_database(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
        
        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        self._run_migrations()
        self.connection.commit()
        logging.info(f"Banco de dados inicializado em: {self.db_path}")

    def get_connection(self):
        if self.connection is None:
            raise Exception("A conexão com o banco de dados não foi inicializada.")
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("Conexão com o banco de dados fechada.")

    def _create_tables(self):
        cursor = self.connection.cursor()
        # Define all CREATE TABLE statements
        tables = {
            "UNIDADE": '''CREATE TABLE IF NOT EXISTS UNIDADE (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT, NOME TEXT NOT NULL UNIQUE, SIGLA TEXT NOT NULL UNIQUE )''',
            "ITEM": '''CREATE TABLE IF NOT EXISTS ITEM (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT, CODIGO_INTERNO TEXT, DESCRICAO TEXT NOT NULL UNIQUE,
                        TIPO_ITEM TEXT NOT NULL CHECK(TIPO_ITEM IN ('Insumo', 'Produto', 'Ambos')), ID_UNIDADE INTEGER NOT NULL,
                        ID_FORNECEDOR_PADRAO INTEGER, SALDO_ESTOQUE REAL NOT NULL DEFAULT 0, CUSTO_MEDIO REAL NOT NULL DEFAULT 0,
                        FOREIGN KEY (ID_UNIDADE) REFERENCES UNIDADE (ID) ON DELETE RESTRICT,
                        FOREIGN KEY (ID_FORNECEDOR_PADRAO) REFERENCES FORNECEDOR (ID) ON DELETE RESTRICT )''',
            "FORNECEDOR": '''CREATE TABLE IF NOT EXISTS FORNECEDOR (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT, RAZAO_SOCIAL TEXT NOT NULL UNIQUE, NOME_FANTASIA TEXT,
                                CNPJ TEXT UNIQUE, STATUS TEXT NOT NULL DEFAULT 'Ativo', TELEFONE TEXT, EMAIL TEXT,
                                LOGRADOURO TEXT, NUMERO TEXT, COMPLEMENTO TEXT, BAIRRO TEXT, CIDADE TEXT, UF TEXT, CEP TEXT )''',
            "ENTRADANOTA": '''CREATE TABLE IF NOT EXISTS ENTRADANOTA (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT, DATA_ENTRADA TEXT NOT NULL, DATA_DIGITACAO TEXT,
                                NUMERO_NOTA TEXT, VALOR_TOTAL REAL, OBSERVACAO TEXT,
                                STATUS TEXT NOT NULL CHECK(STATUS IN ('Em Aberto', 'Finalizada')) )''',
            "COMPOSICAO": '''CREATE TABLE IF NOT EXISTS COMPOSICAO (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT, ID_PRODUTO INTEGER NOT NULL, ID_INSUMO INTEGER NOT NULL,
                                QUANTIDADE REAL NOT NULL, FOREIGN KEY (ID_PRODUTO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
                                FOREIGN KEY (ID_INSUMO) REFERENCES ITEM (ID) ON DELETE RESTRICT, UNIQUE (ID_PRODUTO, ID_INSUMO) )''',
            "ORDEMPRODUCAO": '''CREATE TABLE IF NOT EXISTS ORDEMPRODUCAO (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT, NUMERO TEXT, DATA_CRIACAO TEXT NOT NULL,
                                    DATA_PREVISTA TEXT, STATUS TEXT NOT NULL CHECK(STATUS IN ('Em Andamento', 'Concluída', 'Cancelada')),
                                    QUANTIDADE_PRODUZIDA REAL, CUSTO_TOTAL REAL )''',
            "ORDEMPRODUCAO_ITENS": '''CREATE TABLE IF NOT EXISTS ORDEMPRODUCAO_ITENS (
                                        ID INTEGER PRIMARY KEY AUTOINCREMENT, ID_ORDEM_PRODUCAO INTEGER NOT NULL,
                                        ID_PRODUTO INTEGER NOT NULL, QUANTIDADE_PRODUZIR REAL NOT NULL,
                                        FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES ORDEMPRODUCAO (ID) ON DELETE RESTRICT,
                                        FOREIGN KEY (ID_PRODUTO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
                                        UNIQUE (ID_ORDEM_PRODUCAO, ID_PRODUTO) )''',
            "MOVIMENTO": '''CREATE TABLE IF NOT EXISTS MOVIMENTO (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT, ID_ITEM INTEGER NOT NULL, TIPO_MOVIMENTO TEXT NOT NULL,
                                QUANTIDADE REAL NOT NULL, VALOR_UNITARIO REAL, ID_ORDEM_PRODUCAO INTEGER, DATA_MOVIMENTO TEXT NOT NULL,
                                FOREIGN KEY (ID_ITEM) REFERENCES ITEM (ID) ON DELETE RESTRICT,
                                FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES ORDEMPRODUCAO (ID) ON DELETE RESTRICT )''',
            "ENTRADANOTA_ITENS": '''CREATE TABLE IF NOT EXISTS ENTRADANOTA_ITENS (
                                    ID INTEGER PRIMARY KEY AUTOINCREMENT, ID_ENTRADA INTEGER NOT NULL, ID_INSUMO INTEGER NOT NULL,
                                    ID_FORNECEDOR INTEGER NOT NULL, QUANTIDADE REAL NOT NULL, VALOR_UNITARIO REAL NOT NULL,
                                    FOREIGN KEY (ID_ENTRADA) REFERENCES ENTRADANOTA (ID) ON DELETE RESTRICT,
                                    FOREIGN KEY (ID_INSUMO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
                                    FOREIGN KEY (ID_FORNECEDOR) REFERENCES FORNECEDOR (ID) ON DELETE RESTRICT,
                                    UNIQUE (ID_ENTRADA, ID_INSUMO) )''',
            "SAIDA": '''CREATE TABLE IF NOT EXISTS SAIDA (
                            ID INTEGER PRIMARY KEY AUTOINCREMENT, DATA_SAIDA TEXT NOT NULL, VALOR_TOTAL REAL,
                            OBSERVACAO TEXT, STATUS TEXT NOT NULL CHECK(STATUS IN ('Em Aberto', 'Finalizada')) )''',
            "SAIDA_ITENS": '''CREATE TABLE IF NOT EXISTS SAIDA_ITENS (
                                ID INTEGER PRIMARY KEY AUTOINCREMENT, ID_SAIDA INTEGER NOT NULL, ID_PRODUTO INTEGER NOT NULL,
                                QUANTIDADE REAL NOT NULL, VALOR_UNITARIO REAL NOT NULL,
                                FOREIGN KEY (ID_SAIDA) REFERENCES SAIDA (ID) ON DELETE RESTRICT,
                                FOREIGN KEY (ID_PRODUTO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
                                UNIQUE (ID_SAIDA, ID_PRODUTO) )'''
        }
        for table_sql in tables.values():
            cursor.execute(table_sql)
        # Seed initial data
        unidades = [('Grama', 'g'), ('Quilograma', 'kg'), ('Mililitro', 'ml'), ('Litro', 'L'), ('Unidade', 'un')]
        for nome, sigla in unidades:
            cursor.execute("SELECT ID FROM UNIDADE WHERE NOME = ?", (nome,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO UNIDADE (NOME, SIGLA) VALUES (?, ?)", (nome, sigla))

    def _run_migrations(self):
        cursor = self.connection.cursor()
        # Migration versioning
        cursor.execute("PRAGMA user_version")
        db_version = cursor.fetchone()[0]

        if db_version < 1:
            self._migrate_v1(cursor)
            cursor.execute("PRAGMA user_version = 1")
        
        if db_version < 2:
            self._migrate_v2(cursor)
            cursor.execute("PRAGMA user_version = 2")

        self.connection.commit()

    def _migrate_v1(self, cursor):
        """Migrations for version 1 of the database."""
        # Fix table renames from old schema
        table_rename_map = {
            "TUNIDADE": "UNIDADE", "TITEM": "ITEM", "TFORNECEDOR": "FORNECEDOR",
            "TENTRADANOTA": "ENTRADANOTA", "TCOMPOSICAO": "COMPOSICAO",
            "TORDEMPRODUCAO": "ORDEMPRODUCAO", "TORDEMPRODUCAO_ITENS": "ORDEMPRODUCAO_ITENS",
            "TMOVIMENTO": "MOVIMENTO", "TENTRADANOTA_ITENS": "ENTRADANOTA_ITENS"
        }
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        for old_name, new_name in table_rename_map.items():
            if old_name in tables and new_name not in tables:
                cursor.execute(f"ALTER TABLE {old_name} RENAME TO {new_name}")

        # Fix supplier table columns
        cursor.execute("PRAGMA table_info(FORNECEDOR)")
        supplier_columns = {col[1] for col in cursor.fetchall()}
        if 'NOME' in supplier_columns and 'RAZAO_SOCIAL' not in supplier_columns:
            cursor.execute('ALTER TABLE FORNECEDOR RENAME COLUMN NOME TO RAZAO_SOCIAL')
        address_columns = ['LOGRADOURO', 'NUMERO', 'COMPLEMENTO', 'BAIRRO', 'CIDADE', 'UF', 'CEP']
        for col in address_columns:
            if col not in supplier_columns:
                cursor.execute(f'ALTER TABLE FORNECEDOR ADD COLUMN {col} TEXT')

        # Fix entry items table
        cursor.execute("PRAGMA table_info(ENTRADANOTA_ITENS)")
        entry_items_columns = {col[1] for col in cursor.fetchall()}
        if 'ID_FORNECEDOR' not in entry_items_columns:
            cursor.execute('ALTER TABLE ENTRADANOTA_ITENS ADD COLUMN ID_FORNECEDOR INTEGER REFERENCES FORNECEDOR(ID)')
            cursor.execute("""
                UPDATE ENTRADANOTA_ITENS SET ID_FORNECEDOR = (
                    SELECT ID_FORNECEDOR FROM ENTRADANOTA WHERE ENTRADANOTA.ID = ENTRADANOTA_ITENS.ID_ENTRADA)
            """)
        
        # Non-destructive migration for ENTRADANOTA
        self._migrate_entradanota_table(cursor)
        # Non-destructive migration for ITEM
        self._migrate_item_table(cursor)

    def _migrate_v2(self, cursor):
        """Migrations for version 2 of the database."""
        # Recriar a tabela ORDEMPRODUCAO para atualizar a restrição CHECK e adicionar colunas
        temp_table = "ORDEMPRODUCAO_temp_migration"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(f"ALTER TABLE ORDEMPRODUCAO RENAME TO {temp_table}")

        # Recriar a tabela com a nova estrutura
        self._create_tables()

        # Copiar os dados da tabela temporária para a nova tabela
        cursor.execute(f"""
            INSERT INTO ORDEMPRODUCAO (ID, NUMERO, DATA_CRIACAO, DATA_PREVISTA, STATUS)
            SELECT ID, NUMERO, DATA_CRIACAO, DATA_PREVISTA,
                   CASE
                       WHEN STATUS = 'Planejada' THEN 'Em Andamento'
                       WHEN STATUS = 'Concluída' THEN 'Concluída'
                       ELSE STATUS
                   END
            FROM {temp_table}
        """)
        cursor.execute(f"DROP TABLE {temp_table}")

    def _column_exists(self, cursor, table_name, column_name):
        cursor.execute(f"PRAGMA table_info({table_name})")
        return any(column[1] == column_name for column in cursor.fetchall())

    def _migrate_entradanota_table(self, cursor):
        if self._column_exists(cursor, 'ENTRADANOTA', 'ID_FORNECEDOR'):
            temp_table = "ENTRADANOTA_temp_migration"
            cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
            cursor.execute(f"ALTER TABLE ENTRADANOTA RENAME TO {temp_table}")
            
            # Recreate with correct schema
            self._create_tables() 
            
            # Copy data
            cursor.execute(f"""
                INSERT INTO ENTRADANOTA (ID, DATA_ENTRADA, DATA_DIGITACAO, NUMERO_NOTA, VALOR_TOTAL, OBSERVACAO, STATUS)
                SELECT ID, DATA_ENTRADA, DATA_DIGITACAO, NUMERO_NOTA, VALOR_TOTAL, OBSERVACAO, STATUS FROM {temp_table}
            """)
            cursor.execute(f"DROP TABLE {temp_table}")

    def _migrate_item_table(self, cursor):
        # This migration is to remove the UNIQUE constraint from CODIGO_INTERNO.
        # It's complex to check for a constraint directly, so we rebuild the table.
        temp_table = "ITEM_temp_migration"
        cursor.execute(f"DROP TABLE IF EXISTS {temp_table}")
        cursor.execute(f"ALTER TABLE ITEM RENAME TO {temp_table}")

        # Recreate with correct schema
        self._create_tables()

        # Copy data
        cursor.execute(f"""
            INSERT INTO ITEM (ID, CODIGO_INTERNO, DESCRICAO, TIPO_ITEM, ID_UNIDADE, ID_FORNECEDOR_PADRAO, SALDO_ESTOQUE, CUSTO_MEDIO)
            SELECT ID, CODIGO_INTERNO, DESCRICAO, TIPO_ITEM, ID_UNIDADE, ID_FORNECEDOR_PADRAO, SALDO_ESTOQUE, CUSTO_MEDIO FROM {temp_table}
        """)
        cursor.execute(f"DROP TABLE {temp_table}")

def get_db_manager():
    return DatabaseManager()
