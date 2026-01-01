# app/database/db.py
import sqlite3
import os
import atexit
import platform

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
        # Path for the database file as specified by the user
        return "Gestão de Produção/Dados/DADOS.DB"

    def initialize_database(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

        self.connection = sqlite3.connect(self.db_path)
        self.connection.row_factory = sqlite3.Row
        self._create_tables()
        print(f"Banco de dados inicializado em: {self.db_path}")


    def get_connection(self):
        if self.connection is None:
            raise Exception("A conexão com o banco de dados não foi inicializada.")
        return self.connection

    def close_connection(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            print("Conexão com o banco de dados fechada.")

    def _create_tables(self):
        cursor = self.connection.cursor()

        cursor.execute('''
        CREATE TABLE IF NOT EXISTS UNIDADE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME TEXT NOT NULL UNIQUE,
            SIGLA TEXT NOT NULL UNIQUE
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ITEM (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            CODIGO_INTERNO TEXT UNIQUE,
            DESCRICAO TEXT NOT NULL UNIQUE,
            TIPO_ITEM TEXT NOT NULL CHECK(TIPO_ITEM IN ('Insumo', 'Produto', 'Ambos')),
            ID_UNIDADE INTEGER NOT NULL,
            ID_FORNECEDOR_PADRAO INTEGER,
            SALDO_ESTOQUE REAL NOT NULL DEFAULT 0,
            CUSTO_MEDIO REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (ID_UNIDADE) REFERENCES UNIDADE (ID) ON DELETE RESTRICT,
            FOREIGN KEY (ID_FORNECEDOR_PADRAO) REFERENCES FORNECEDOR (ID) ON DELETE RESTRICT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS FORNECEDOR (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            RAZAO_SOCIAL TEXT NOT NULL UNIQUE,
            NOME_FANTASIA TEXT,
            CNPJ TEXT UNIQUE,
            STATUS TEXT NOT NULL DEFAULT 'Ativo',
            TELEFONE TEXT,
            EMAIL TEXT,
            LOGRADOURO TEXT,
            NUMERO TEXT,
            COMPLEMENTO TEXT,
            BAIRRO TEXT,
            CIDADE TEXT,
            UF TEXT,
            CEP TEXT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ENTRADANOTA (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_FORNECEDOR INTEGER,
            DATA TEXT NOT NULL,
            DATA_ENTRADA TEXT NOT NULL,
            DATA_DIGITACAO TEXT,
            NUMERO_NOTA TEXT UNIQUE,
            VALOR_TOTAL REAL,
            OBSERVACAO TEXT,
            STATUS TEXT NOT NULL CHECK(STATUS IN ('Em Aberto', 'Finalizada')),
            FOREIGN KEY (ID_FORNECEDOR) REFERENCES FORNECEDOR (ID) ON DELETE RESTRICT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS COMPOSICAO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_PRODUTO INTEGER NOT NULL,
            ID_INSUMO INTEGER NOT NULL,
            QUANTIDADE REAL NOT NULL,
            FOREIGN KEY (ID_PRODUTO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
            FOREIGN KEY (ID_INSUMO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
            UNIQUE (ID_PRODUTO, ID_INSUMO)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ORDEMPRODUCAO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NUMERO TEXT,
            DATA_CRIACAO TEXT NOT NULL,
            DATA_PREVISTA TEXT,
            STATUS TEXT NOT NULL CHECK(STATUS IN ('Planejada', 'Em Andamento', 'Concluída', 'Cancelada'))
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ORDEMPRODUCAO_ITENS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ORDEM_PRODUCAO INTEGER NOT NULL,
            ID_PRODUTO INTEGER NOT NULL,
            QUANTIDADE_PRODUZIR REAL NOT NULL,
            FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES ORDEMPRODUCAO (ID) ON DELETE RESTRICT,
            FOREIGN KEY (ID_PRODUTO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
            UNIQUE (ID_ORDEM_PRODUCAO, ID_PRODUTO)
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS MOVIMENTO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ITEM INTEGER NOT NULL,
            TIPO_MOVIMENTO TEXT NOT NULL,
            QUANTIDADE REAL NOT NULL,
            VALOR_UNITARIO REAL,
            ID_ORDEM_PRODUCAO INTEGER,
            DATA_MOVIMENTO TEXT NOT NULL,
            FOREIGN KEY (ID_ITEM) REFERENCES ITEM (ID) ON DELETE RESTRICT,
            FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES ORDEMPRODUCAO (ID) ON DELETE RESTRICT
        )
        ''')
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS ENTRADANOTA_ITENS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ENTRADA INTEGER NOT NULL,
            ID_INSUMO INTEGER NOT NULL,
            QUANTIDADE REAL NOT NULL,
            VALOR_UNITARIO REAL NOT NULL,
            FOREIGN KEY (ID_ENTRADA) REFERENCES ENTRADANOTA (ID) ON DELETE RESTRICT,
            FOREIGN KEY (ID_INSUMO) REFERENCES ITEM (ID) ON DELETE RESTRICT,
            UNIQUE (ID_ENTRADA, ID_INSUMO)
        )
        ''')

        unidades = [('Grama', 'g'), ('Quilograma', 'kg'), ('Mililitro', 'ml'), ('Litro', 'L'), ('Unidade', 'un')]
        for nome, sigla in unidades:
            cursor.execute("SELECT ID FROM UNIDADE WHERE NOME = ?", (nome,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO UNIDADE (NOME, SIGLA) VALUES (?, ?)", (nome, sigla))

        self._run_migrations(cursor)

        self.connection.commit()

    def _run_migrations(self, cursor):
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

        # Continue with other migrations
        cursor.execute("PRAGMA table_info(ENTRADANOTA)")
        columns_info = {column[1]: {'type': column[2], 'pk': column[5]} for column in cursor.fetchall()}

        if 'DATA_DIGITACAO' not in columns_info:
            cursor.execute('ALTER TABLE ENTRADANOTA ADD COLUMN DATA_DIGITACAO TEXT')
            cursor.execute('UPDATE ENTRADANOTA SET DATA_DIGITACAO = DATA_ENTRADA WHERE DATA_DIGITACAO IS NULL')

        cursor.execute("PRAGMA table_info(FORNECEDOR)")
        supplier_columns = {col[1]: col for col in cursor.fetchall()}

        if 'NOME' in supplier_columns and 'RAZAO_SOCIAL' not in supplier_columns:
            cursor.execute('ALTER TABLE FORNECEDOR RENAME COLUMN NOME TO RAZAO_SOCIAL')

        address_columns = ['LOGRADOURO', 'NUMERO', 'COMPLEMENTO', 'BAIRRO', 'CIDADE', 'UF', 'CEP']
        for col in address_columns:
            if col not in supplier_columns:
                cursor.execute(f'ALTER TABLE FORNECEDOR ADD COLUMN {col} TEXT')

def get_db_manager():
    return DatabaseManager()
