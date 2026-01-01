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
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        return os.path.join(project_root, 'Gestão de produção', 'dados', 'dados.db')

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
        CREATE TABLE IF NOT EXISTS T_UNIDADE (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME TEXT NOT NULL UNIQUE,
            SIGLA TEXT NOT NULL UNIQUE
        )
        ''')
        # Tabela de Itens (Produtos e Insumos)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_ITEM (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DESCRICAO TEXT NOT NULL UNIQUE,
            TIPO_ITEM TEXT NOT NULL CHECK(TIPO_ITEM IN ('Insumo', 'Produto', 'Ambos')),
            ID_UNIDADE INTEGER NOT NULL,
            SALDO_ESTOQUE REAL NOT NULL DEFAULT 0,
            CUSTO_MEDIO REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (ID_UNIDADE) REFERENCES T_UNIDADE (ID)
        )
        ''')
        # Tabela de Composição (Ficha Técnica)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_COMPOSICAO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_PRODUTO INTEGER NOT NULL,
            ID_INSUMO INTEGER NOT NULL,
            QUANTIDADE REAL NOT NULL,
            FOREIGN KEY (ID_PRODUTO) REFERENCES T_ITEM (ID),
            FOREIGN KEY (ID_INSUMO) REFERENCES T_ITEM (ID),
            UNIQUE (ID_PRODUTO, ID_INSUMO)
        )
        ''')
        # Tabela de Ordem de Produção (Mestre)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_ORDEM_PRODUCAO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DATA_CRIACAO TEXT NOT NULL,
            DATA_PREVISTA TEXT,
            STATUS TEXT NOT NULL CHECK(STATUS IN ('Planejada', 'Em Andamento', 'Concluída', 'Cancelada'))
        )
        ''')
        # Tabela de Itens da Ordem de Produção (Detalhe)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_ORDEM_PRODUCAO_ITENS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ORDEM_PRODUCAO INTEGER NOT NULL,
            ID_PRODUTO INTEGER NOT NULL,
            QUANTIDADE_PRODUZIR REAL NOT NULL,
            FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES T_ORDEM_PRODUCAO (ID),
            FOREIGN KEY (ID_PRODUTO) REFERENCES T_ITEM (ID),
            UNIQUE (ID_ORDEM_PRODUCAO, ID_PRODUTO)
        )
        ''')
        # Tabela de Movimentação de Estoque
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_MOVIMENTO (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ITEM INTEGER NOT NULL,
            TIPO_MOVIMENTO TEXT NOT NULL,
            QUANTIDADE REAL NOT NULL,
            VALOR_UNITARIO REAL,
            ID_ORDEM_PRODUCAO INTEGER,
            DATA_MOVIMENTO TEXT NOT NULL,
            FOREIGN KEY (ID_ITEM) REFERENCES T_ITEM (ID),
            FOREIGN KEY (ID_ORDEM_PRODUCAO) REFERENCES T_ORDEM_PRODUCAO (ID)
        )
        ''')
        # Tabela de Nota de Entrada (Mestre)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_ENTRADA_NOTA (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            DATA_ENTRADA TEXT NOT NULL,
            FORNECEDOR TEXT,
            NUMERO_NOTA TEXT,
            VALOR_TOTAL REAL,
            STATUS TEXT NOT NULL CHECK(STATUS IN ('Em Aberto', 'Finalizada'))
        )
        ''')
        # Tabela de Itens da Nota de Entrada (Detalhe)
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_ENTRADA_NOTA_ITENS (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            ID_ENTRADA INTEGER NOT NULL,
            ID_INSUMO INTEGER NOT NULL,
            QUANTIDADE REAL NOT NULL,
            VALOR_UNITARIO REAL NOT NULL,
            FOREIGN KEY (ID_ENTRADA) REFERENCES T_ENTRADA_NOTA (ID),
            FOREIGN KEY (ID_INSUMO) REFERENCES T_ITEM (ID),
            UNIQUE (ID_ENTRADA, ID_INSUMO)
        )
        ''')
        # Tabela de Fornecedores
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS T_FORNECEDOR (
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            NOME_RAZAO_SOCIAL TEXT NOT NULL,
            CPF_CNPJ TEXT NOT NULL UNIQUE,
            TIPO_PESSOA TEXT NOT NULL CHECK(TIPO_PESSOA IN ('Física', 'Jurídica')),
            TELEFONE TEXT,
            EMAIL TEXT,
            CEP TEXT,
            ENDERECO TEXT,
            NUMERO TEXT,
            COMPLEMENTO TEXT,
            BAIRRO TEXT,
            CIDADE TEXT,
            ESTADO TEXT
        )
        ''')

        # Inserção de unidades padrão (com nomes de coluna em maiúsculas)
        unidades = [('Grama', 'g'), ('Quilograma', 'kg'), ('Mililitro', 'ml'), ('Litro', 'L'), ('Unidade', 'un')]
        for nome, sigla in unidades:
            cursor.execute("SELECT ID FROM T_UNIDADE WHERE NOME = ?", (nome,))
            if cursor.fetchone() is None:
                cursor.execute("INSERT INTO T_UNIDADE (NOME, SIGLA) VALUES (?, ?)", (nome, sigla))

        self.connection.commit()

def get_db_manager():
    return DatabaseManager()

if __name__ == '__main__':
    db_manager = get_db_manager()
