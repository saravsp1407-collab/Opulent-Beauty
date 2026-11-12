"""
database.py - Conexão com o banco de dados SQLite e criação das tabelas.

Apostila 4º Bimestre, Cap. 2 (módulo sqlite3).
As tabelas abaixo são a tradução, para SQLite, do script MySQL
database/makeup_stock.sql (Etapa 1): mesmas tabelas, colunas, chaves
estrangeiras e regras CHECK.
"""
import os
import sqlite3
import unicodedata

PASTA_BACKEND = os.path.dirname(os.path.abspath(__file__))

# Caminho do arquivo do banco. Pode ser trocado pela variável de ambiente
# MAKEUP_DB (usada pelo testar_api.py para não mexer no banco real).
CAMINHO_BANCO = os.environ.get("MAKEUP_DB", os.path.join(PASTA_BACKEND, "makeup_stock.db"))


def normalizar(texto):
    """Remove acentos e põe em minúsculas ('Máscaras' -> 'mascaras')."""
    if texto is None:
        return ""
    sem_acento = unicodedata.normalize("NFD", str(texto))
    sem_acento = "".join(c for c in sem_acento if unicodedata.category(c) != "Mn")
    return sem_acento.lower().strip()


def conectar(caminho_banco=None):
    """Abre uma conexão com o SQLite.

    - PRAGMA foreign_keys = ON: o SQLite só respeita chaves estrangeiras
      se isso for ativado em CADA conexão.
    - create_function: registra 'normalizar' para a busca ignorar acentos.
    """
    conexao = sqlite3.connect(caminho_banco or CAMINHO_BANCO)
    conexao.execute("PRAGMA foreign_keys = ON")
    conexao.create_function("normalizar", 1, normalizar)
    return conexao


def criar_tabelas(caminho_banco=None):
    """Cria as 3 tabelas e os índices, se ainda não existirem."""
    with conectar(caminho_banco) as conexao:
        cursor = conexao.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categoria (
                id_categoria INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL UNIQUE,
                descricao TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS produto (
                id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                marca TEXT,
                descricao TEXT,
                preco REAL NOT NULL CHECK (preco >= 0),
                quantidade_atual INTEGER NOT NULL DEFAULT 0 CHECK (quantidade_atual >= 0),
                estoque_minimo INTEGER NOT NULL DEFAULT 0 CHECK (estoque_minimo >= 0),
                data_validade TEXT,
                id_categoria INTEGER NOT NULL,
                FOREIGN KEY (id_categoria)
                    REFERENCES categoria(id_categoria)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS movimentacao_estoque (
                id_movimentacao INTEGER PRIMARY KEY AUTOINCREMENT,
                tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
                quantidade INTEGER NOT NULL CHECK (quantidade > 0),
                data_hora TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
                observacao TEXT,
                id_produto INTEGER NOT NULL,
                FOREIGN KEY (id_produto)
                    REFERENCES produto(id_produto)
                    ON UPDATE CASCADE
                    ON DELETE RESTRICT
            )
        """)

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_produto_categoria ON produto(id_categoria)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimentacao_produto ON movimentacao_estoque(id_produto)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_movimentacao_data ON movimentacao_estoque(data_hora)")
        conexao.commit()
