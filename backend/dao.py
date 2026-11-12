"""
dao.py - Classes DAO (Data Access Object): únicas classes que falam com o banco.

Apostila 4º Bimestre, Cap. 2.3 (padrão DAO) e Cap. 5.3 (TarefaDAO).
Apostila 2º Bimestre, Cap. 1 (classe abstrata com ABC/@abstractmethod).

- Sempre usamos '?' nos comandos SQL (evita SQL Injection).
- Cada DAO manipula objetos das classes de models.py.
"""
from abc import ABC, abstractmethod

from database import conectar, normalizar  # noqa: F401  (normalizar é usado no SQL)
from excecoes import NaoEncontradoError
from models import Categoria, Produto, MovimentacaoEstoque

COLUNAS_CATEGORIA = "id_categoria, nome, descricao"
COLUNAS_PRODUTO = ("id_produto, nome, marca, descricao, preco, "
                   "quantidade_atual, estoque_minimo, data_validade, id_categoria")
COLUNAS_MOVIMENTACAO = "id_movimentacao, tipo, quantidade, data_hora, observacao, id_produto"


class BaseDAO(ABC):
    """Classe abstrata: define o contrato que todo DAO do sistema deve cumprir."""

    def __init__(self, caminho_banco=None):
        self.caminho_banco = caminho_banco

    def _conectar(self):
        return conectar(self.caminho_banco)

    @abstractmethod
    def buscar_todos(self):
        pass

    @abstractmethod
    def buscar_por_id(self, id_registro):
        pass


# ---------------------------------------------------------------- Categoria

class CategoriaDAO(BaseDAO):

    def inserir(self, categoria):
        """Cadastra uma categoria e devolve o id gerado.
        Se o objeto já tiver id (usado só pelo seed), o id é preservado."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            if categoria.id_categoria is None:
                cursor.execute(
                    "INSERT INTO categoria (nome, descricao) VALUES (?, ?)",
                    (categoria.nome, categoria.descricao),
                )
            else:
                cursor.execute(
                    "INSERT INTO categoria (id_categoria, nome, descricao) VALUES (?, ?, ?)",
                    (categoria.id_categoria, categoria.nome, categoria.descricao),
                )
            conexao.commit()
            return cursor.lastrowid

    def buscar_todos(self):
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(f"SELECT {COLUNAS_CATEGORIA} FROM categoria ORDER BY id_categoria")
            return [Categoria(*linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, id_categoria):
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT {COLUNAS_CATEGORIA} FROM categoria WHERE id_categoria=?",
                (id_categoria,),
            )
            linha = cursor.fetchone()
            return Categoria(*linha) if linha else None

    def atualizar(self, id_categoria, categoria):
        """Devolve True se alguma linha foi alterada, False se o id não existe."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE categoria SET nome=?, descricao=? WHERE id_categoria=?",
                (categoria.nome, categoria.descricao, id_categoria),
            )
            conexao.commit()
            return cursor.rowcount > 0

    def remover(self, id_categoria):
        """Falha (IntegrityError) se ainda houver produtos nesta categoria."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM categoria WHERE id_categoria=?", (id_categoria,))
            conexao.commit()
            return cursor.rowcount > 0


# ------------------------------------------------------------------ Produto

class ProdutoDAO(BaseDAO):

    def inserir(self, produto):
        """Cadastra um produto e devolve o id gerado.
        Se já nasce com estoque, registra a movimentação 'Estoque inicial'
        na mesma transação, para o histórico sempre bater com a quantidade."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            if produto.id_produto is None:
                cursor.execute(
                    "INSERT INTO produto (nome, marca, descricao, preco, quantidade_atual, "
                    "estoque_minimo, data_validade, id_categoria) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (produto.nome, produto.marca, produto.descricao, produto.preco,
                     produto.quantidade_atual, produto.estoque_minimo,
                     produto.data_validade, produto.id_categoria),
                )
            else:
                cursor.execute(
                    "INSERT INTO produto (id_produto, nome, marca, descricao, preco, quantidade_atual, "
                    "estoque_minimo, data_validade, id_categoria) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (produto.id_produto, produto.nome, produto.marca, produto.descricao,
                     produto.preco, produto.quantidade_atual, produto.estoque_minimo,
                     produto.data_validade, produto.id_categoria),
                )
            id_gerado = cursor.lastrowid
            if produto.quantidade_atual > 0:
                cursor.execute(
                    "INSERT INTO movimentacao_estoque (tipo, quantidade, observacao, id_produto) "
                    "VALUES ('entrada', ?, 'Estoque inicial', ?)",
                    (produto.quantidade_atual, id_gerado),
                )
            conexao.commit()
            return id_gerado

    def buscar_todos(self, busca=None, id_categoria=None, marca=None):
        """Lista produtos. Os filtros são opcionais e podem ser combinados.
        A busca ignora acentos e maiúsculas e procura em nome, marca e categoria."""
        # O texto do SQL só junta trechos fixos; os VALORES entram sempre via '?'.
        sql = ("SELECT " + ", ".join("p." + c.strip() for c in COLUNAS_PRODUTO.split(",")) +
               " FROM produto p JOIN categoria c ON c.id_categoria = p.id_categoria WHERE 1=1")
        parametros = []
        if busca:
            sql += " AND normalizar(p.nome || ' ' || IFNULL(p.marca, '') || ' ' || c.nome) LIKE ?"
            parametros.append("%" + normalizar(busca) + "%")
        if id_categoria is not None:
            sql += " AND p.id_categoria = ?"
            parametros.append(id_categoria)
        if marca:
            sql += " AND p.marca = ?"
            parametros.append(marca)
        sql += " ORDER BY p.id_produto"
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(sql, parametros)
            return [Produto(*linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, id_produto):
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT {COLUNAS_PRODUTO} FROM produto WHERE id_produto=?", (id_produto,)
            )
            linha = cursor.fetchone()
            return Produto(*linha) if linha else None

    def buscar_estoque_baixo(self):
        """Produtos com quantidade_atual <= estoque_minimo (Caso de Uso: Consultar Estoque Baixo)."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT {COLUNAS_PRODUTO} FROM produto "
                "WHERE quantidade_atual <= estoque_minimo ORDER BY quantidade_atual, id_produto"
            )
            return [Produto(*linha) for linha in cursor.fetchall()]

    def atualizar(self, id_produto, produto):
        """Edita os dados do produto. A quantidade NÃO é alterada aqui:
        ela só muda por movimentações de entrada/saída (MovimentacaoDAO)."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                "UPDATE produto SET nome=?, marca=?, descricao=?, preco=?, "
                "estoque_minimo=?, data_validade=?, id_categoria=? WHERE id_produto=?",
                (produto.nome, produto.marca, produto.descricao, produto.preco,
                 produto.estoque_minimo, produto.data_validade, produto.id_categoria,
                 id_produto),
            )
            conexao.commit()
            return cursor.rowcount > 0

    def remover(self, id_produto):
        """Falha (IntegrityError) se o produto já tiver movimentações no histórico."""
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute("DELETE FROM produto WHERE id_produto=?", (id_produto,))
            conexao.commit()
            return cursor.rowcount > 0


# ------------------------------------------------------ MovimentacaoEstoque

class MovimentacaoDAO(BaseDAO):

    def registrar(self, movimentacao):
        """Registra uma entrada ou saída e atualiza a quantidade do produto.

        Tudo acontece em UMA transação: ou grava a movimentação E atualiza o
        estoque, ou não grava nada (se der erro, o 'with' desfaz tudo).
        Segue o Diagrama de Sequência 'Registrar Entrada de Estoque':
        Produto.registrar_entrada() -> grava a movimentação -> confirma.

        Devolve (movimentacao_gravada, produto_atualizado).
        """
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT {COLUNAS_PRODUTO} FROM produto WHERE id_produto=?",
                (movimentacao.id_produto,),
            )
            linha = cursor.fetchone()
            if linha is None:
                raise NaoEncontradoError("Produto não encontrado.")
            produto = Produto(*linha)

            # Regra de negócio fica na classe Produto (pode lançar EstoqueInsuficienteError)
            if movimentacao.tipo == "entrada":
                produto.registrar_entrada(movimentacao.quantidade)
            else:
                produto.registrar_saida(movimentacao.quantidade)

            cursor.execute(
                "INSERT INTO movimentacao_estoque (tipo, quantidade, observacao, id_produto) "
                "VALUES (?, ?, ?, ?)",
                (movimentacao.tipo, movimentacao.quantidade,
                 movimentacao.observacao, movimentacao.id_produto),
            )
            id_movimentacao = cursor.lastrowid
            cursor.execute(
                "UPDATE produto SET quantidade_atual=? WHERE id_produto=?",
                (produto.quantidade_atual, produto.id_produto),
            )
            cursor.execute(
                f"SELECT {COLUNAS_MOVIMENTACAO} FROM movimentacao_estoque WHERE id_movimentacao=?",
                (id_movimentacao,),
            )
            gravada = MovimentacaoEstoque(*cursor.fetchone())
            conexao.commit()
            return gravada, produto

    def buscar_todos(self, id_produto=None):
        """Histórico de movimentações, da mais recente para a mais antiga.
        Se id_produto for informado, filtra só aquele produto."""
        sql = f"SELECT {COLUNAS_MOVIMENTACAO} FROM movimentacao_estoque"
        parametros = []
        if id_produto is not None:
            sql += " WHERE id_produto=?"
            parametros.append(id_produto)
        sql += " ORDER BY data_hora DESC, id_movimentacao DESC"
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(sql, parametros)
            return [MovimentacaoEstoque(*linha) for linha in cursor.fetchall()]

    def buscar_por_id(self, id_movimentacao):
        with self._conectar() as conexao:
            cursor = conexao.cursor()
            cursor.execute(
                f"SELECT {COLUNAS_MOVIMENTACAO} FROM movimentacao_estoque WHERE id_movimentacao=?",
                (id_movimentacao,),
            )
            linha = cursor.fetchone()
            return MovimentacaoEstoque(*linha) if linha else None

    def buscar_por_produto(self, id_produto):
        return self.buscar_todos(id_produto)
