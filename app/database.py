import sqlite3
import os
import atexit

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
        install_path = os.getenv('MINISIS_INSTALL_PATH', os.path.expanduser('~'))
        return os.path.join(install_path, 'MiniSis', 'OP', 'dados', 'OPMiniSis.db')

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
        # Tabela de Unidades
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TUNIDADE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME TEXT NOT NULL UNIQUE,
            SIGLA TEXT NOT NULL UNIQUE
        )
        ''')
        # Tabela de Itens (Produtos e Insumos)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TITEM (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DESCRICAO TEXT NOT NULL UNIQUE,
            TIPO_ITEM TEXT NOT NULL CHECK(TIPO_ITEM IN ('Insumo', 'Produto', 'Ambos')),
            ID_UNIDADE INTEGER NOT NULL,
            SALDO_ESTOQUE REAL NOT NULL DEFAULT 0,
            CUSTO_MEDIO REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (ID_UNIDADE) REFERENCES TUNIDADE (ID)
        )
        ''')
        # Tabela de Fornecedores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TFORNECEDOR (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME TEXT NOT NULL UNIQUE,
            CNPJ TEXT,
            TELEFONE TEXT,
            EMAIL TEXT
        )
        ''')
        # Tabela de Nota de Entrada (Mestre)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TENTRADANOTA (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_FORNECEDOR INTEGER,
            DATA_ENTRADA TEXT NOT NULL,
            DATA_DIGITACAO TEXT,
            NUMERO_NOTA TEXT,
            VALOR_TOTAL REAL,
            STATUS TEXT NOT NULL CHECK(STATUS IN ('Em Aberto', 'Finalizada')),
            FOREIGN KEY (ID_FORNECEDOR) REFERENCES TFORNECEDOR (ID)
        )
        ''')
        # Tabela de Composição (Ficha Técnica)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TCOMPOSICAO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_PRODUTO INTEGER NOT NULL,
            ID_INSUMO INTEGER NOT NULL,
            QUANTIDADE REAL NOT NULL,
            FOREIGN KEY (ID_PRODUTO) REFERENCES TITEM (ID),
            FOREIGN KEY (ID_INSUMO) REFERENCES TITEM (ID),
            UNIQUE (ID_PRODUTO, ID_INSUMO)
        )
        ''')
        # Tabela de Ordem de Produção (Mestre)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TORDEMPRODUCAO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DATA_CRIACAO TEXT NOT NULL,
            DATA_PREVISTA TEXT,
            STATUS TEXT NOT NULL CHECK(STATUS IN ('Planejada', 'Em Andamento', 'Concluída', 'Cancelada'))
        )
        ''')
        # Tabela de Itens da Ordem de Produção (Detalhe)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TORDEMPRODUCAO_ITENS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ORDEM_PRODUCAO INTEGER NOT NULL,
            ID_PRODUTO INTEGER NOT NULL,
            QUANTIDADE_PRODUZIR REAL NOT NULL,
            FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES TORDEMPRODUCAO (ID),
            FOREIGN KEY (ID_PRODUTO) REFERENCES TITEM (ID),
            UNIQUE (ID_ORDEM_PRODUCAO, ID_PRODUTO)
        )
        ''')
        # Tabela de Movimentação de Estoque
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TMOVIMENTO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ITEM INTEGER NOT NULL,
            TIPO_MOVIMENTO TEXT NOT NULL,
            QUANTIDADE REAL NOT NULL,
            VALOR_UNITARIO REAL,
            ID_ORDEM_PRODUCAO INTEGER,
            DATA_MOVIMENTO TEXT NOT NULL,
            FOREIGN KEY (ID_ITEM) REFERENCES TITEM (ID),
            FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES TORDEMPRODUCAO (ID)
        )
        ''')
        # Tabela de Itens da Nota de Entrada (Detalhe)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS TENTRADANOTA_ITENS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ENTRADA INTEGER NOT NULL,
            ID_INSUMO INTEGER NOT NULL,
            QUANTIDADE REAL NOT NULL,
            VALOR_UNITARIO REAL NOT NULL,
            FOREIGN KEY (ID_ENTRADA) REFERENCES TENTRADANOTA (ID),
            FOREIGN KEY (ID_INSUMO) REFERENCES TITEM (ID),
            UNIQUE (ID_ENTRADA, ID_INSUMO)
        )
        ''')

        self._run_migrations(cursor)

        unidades = [('Grama', 'g'), ('Quilograma', 'kg'), ('Mililitro', 'ml'), ('Litro', 'L'), ('Unidade', 'un')]
        for nome, sigla in unidades:
            cursor.execute("SELECT ID FROM TUNIDADE WHERE NOME = ?", (nome,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO TUNIDADE (NOME, SIGLA) VALUES (?, ?)", (nome, sigla))

        self.connection.commit()

    def _run_migrations(self, cursor):
        cursor.execute("PRAGMA table_info(TENTRADANOTA)")
        columns_info = {column[1]: {'type': column[2], 'pk': column[5]} for column in cursor.fetchall()}

        if 'DATA_DIGITACAO' not in columns_info:
            cursor.execute('ALTER TABLE TENTRADANOTA ADD COLUMN DATA_DIGITACAO TEXT')
            cursor.execute('UPDATE TENTRADANOTA SET DATA_DIGITACAO = DATA_ENTRADA WHERE DATA_DIGITACAO IS NULL')

        if 'FORNECEDOR' in columns_info and columns_info['FORNECEDOR']['type'] == 'TEXT':
            print("Executando migração de Fornecedor...")
            try:
                cursor.execute("SELECT DISTINCT FORNECEDOR FROM TENTRADANOTA WHERE FORNECEDOR IS NOT NULL AND FORNECEDOR != ''")
                old_suppliers = [row[0] for row in cursor.fetchall()]
                for supplier_name in old_suppliers:
                    cursor.execute("INSERT OR IGNORE INTO TFORNECEDOR (NOME) VALUES (?)", (supplier_name,))

                cursor.execute("ALTER TABLE TENTRADANOTA ADD COLUMN ID_FORNECEDOR INTEGER REFERENCES TFORNECEDOR(ID)")

                cursor.execute("SELECT ID, NOME FROM TFORNECEDOR")
                supplier_map = {name: id for id, name in cursor.fetchall()}
                for name, id in supplier_map.items():
                    cursor.execute("UPDATE TENTRADANOTA SET ID_FORNECEDOR = ? WHERE FORNECEDOR = ?", (id, name))

                cursor.execute('''
                    CREATE TABLE TENTRADANOTA_NEW (
                        ID INTEGER PRIMARY KEY AUTOINCREMENT,
                        ID_FORNECEDOR INTEGER,
                        DATA_ENTRADA TEXT NOT NULL,
                        DATA_DIGITACAO TEXT,
                        NUMERO_NOTA TEXT,
                        VALOR_TOTAL REAL,
                        STATUS TEXT NOT NULL,
                        FOREIGN KEY (ID_FORNECEDOR) REFERENCES TFORNECEDOR (ID)
                    )
                ''')

                cursor.execute('''
                    INSERT INTO TENTRADANOTA_NEW (ID, ID_FORNECEDOR, DATA_ENTRADA, DATA_DIGITACAO, NUMERO_NOTA, VALOR_TOTAL, STATUS)
                    SELECT ID, ID_FORNECEDOR, DATA_ENTRADA, DATA_DIGITACAO, NUMERO_NOTA, VALOR_TOTAL, STATUS FROM TENTRADANOTA
                ''')

                cursor.execute("DROP TABLE TENTRADANOTA")
                cursor.execute("ALTER TABLE TENTRADANOTA_NEW RENAME TO TENTRADANOTA")
                print("Migração de Fornecedor concluída com sucesso.")
            except sqlite3.Error as e:
                print(f"Erro durante a migração de fornecedor: {e}")
                self.connection.rollback()
                raise e

def get_db_manager():
    return DatabaseManager()

if __name__ == '__main__':
    db_manager = get_db_manager()
