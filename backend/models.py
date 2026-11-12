"""
models.py - Classes do domínio (o que o Diagrama de Classes UML descreve).

Apostila 1º Bimestre (Cap. 6: encapsulamento, @property),
Apostila 3º Bimestre (do diagrama UML ao código) e
Apostila 4º Bimestre (Cap. 5.2: models.py com to_dict()).

Regra do padrão DAO: estas classes NÃO conhecem SQL nem Flask.
As operações cadastrar/editar/excluir/listar do UML ficam nos DAOs (dao.py).
"""
from datetime import datetime

from excecoes import ValidacaoError, EstoqueInsuficienteError

TIPOS_MOVIMENTACAO = ("entrada", "saida")


# ---------- funções auxiliares de validação ----------

def _texto(valor, campo, maximo, obrigatorio=False):
    """Valida um texto: remove espaços, confere tamanho e obrigatoriedade."""
    if valor is None or (isinstance(valor, str) and not valor.strip()):
        if obrigatorio:
            raise ValidacaoError(f"O campo '{campo}' é obrigatório.")
        return None
    if not isinstance(valor, str):
        raise ValidacaoError(f"O campo '{campo}' deve ser um texto.")
    valor = valor.strip()
    if len(valor) > maximo:
        raise ValidacaoError(f"O campo '{campo}' aceita no máximo {maximo} caracteres.")
    return valor


def _inteiro(valor, campo, minimo=0):
    """Valida um número inteiro maior ou igual a 'minimo'."""
    if isinstance(valor, float) and valor.is_integer():
        valor = int(valor)
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValidacaoError(f"O campo '{campo}' deve ser um número inteiro.")
    if valor < minimo:
        raise ValidacaoError(f"O campo '{campo}' deve ser maior ou igual a {minimo}.")
    return valor


# ---------- Categoria ----------

class Categoria:
    def __init__(self, id_categoria, nome, descricao=None):
        self.id_categoria = id_categoria
        self.nome = nome            # usa o setter (validação)
        self.descricao = descricao  # usa o setter (validação)

    @property
    def nome(self):
        return self.__nome

    @nome.setter
    def nome(self, valor):
        self.__nome = _texto(valor, "nome", 80, obrigatorio=True)

    @property
    def descricao(self):
        return self.__descricao

    @descricao.setter
    def descricao(self, valor):
        self.__descricao = _texto(valor, "descricao", 250)

    def to_dict(self):
        return {
            "id_categoria": self.id_categoria,
            "nome": self.nome,
            "descricao": self.descricao,
        }

    @classmethod
    def from_dict(cls, dados, id_categoria=None):
        return cls(id_categoria, dados.get("nome"), dados.get("descricao"))


# ---------- Produto ----------

class Produto:
    def __init__(self, id_produto, nome, marca, descricao, preco,
                 quantidade_atual, estoque_minimo, data_validade, id_categoria):
        self.id_produto = id_produto
        self.nome = nome
        self.marca = marca
        self.descricao = descricao
        self.preco = preco
        self.quantidade_atual = quantidade_atual
        self.estoque_minimo = estoque_minimo
        self.data_validade = data_validade
        self.id_categoria = id_categoria

    # --- propriedades com validação (encapsulamento) ---

    @property
    def nome(self):
        return self.__nome

    @nome.setter
    def nome(self, valor):
        self.__nome = _texto(valor, "nome", 120, obrigatorio=True)

    @property
    def marca(self):
        return self.__marca

    @marca.setter
    def marca(self, valor):
        self.__marca = _texto(valor, "marca", 80)

    @property
    def descricao(self):
        return self.__descricao

    @descricao.setter
    def descricao(self, valor):
        self.__descricao = _texto(valor, "descricao", 250)

    @property
    def preco(self):
        return self.__preco

    @preco.setter
    def preco(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, (int, float)):
            raise ValidacaoError("O campo 'preco' deve ser um número.")
        if valor < 0:
            raise ValidacaoError("O campo 'preco' não pode ser negativo.")
        self.__preco = round(valor, 2)

    @property
    def quantidade_atual(self):
        return self.__quantidade_atual

    @quantidade_atual.setter
    def quantidade_atual(self, valor):
        self.__quantidade_atual = _inteiro(valor, "quantidade_atual")

    @property
    def estoque_minimo(self):
        return self.__estoque_minimo

    @estoque_minimo.setter
    def estoque_minimo(self, valor):
        self.__estoque_minimo = _inteiro(valor, "estoque_minimo")

    @property
    def data_validade(self):
        return self.__data_validade

    @data_validade.setter
    def data_validade(self, valor):
        if valor is None or valor == "":
            self.__data_validade = None
            return
        try:
            datetime.strptime(valor, "%Y-%m-%d")
        except (TypeError, ValueError):
            raise ValidacaoError("O campo 'data_validade' deve estar no formato AAAA-MM-DD.")
        self.__data_validade = valor

    @property
    def id_categoria(self):
        return self.__id_categoria

    @id_categoria.setter
    def id_categoria(self, valor):
        self.__id_categoria = _inteiro(valor, "id_categoria", minimo=1)

    # --- comportamentos do produto ---

    def esta_em_estoque(self):
        return self.__quantidade_atual > 0

    def esta_com_estoque_baixo(self):
        return self.__quantidade_atual <= self.__estoque_minimo

    def registrar_entrada(self, quantidade):
        """Aumenta o estoque (Caso de Uso: Registrar Entrada de Estoque)."""
        quantidade = _inteiro(quantidade, "quantidade", minimo=1)
        self.__quantidade_atual += quantidade

    def registrar_saida(self, quantidade):
        """Diminui o estoque. Lança EstoqueInsuficienteError se não houver o bastante."""
        quantidade = _inteiro(quantidade, "quantidade", minimo=1)
        if quantidade > self.__quantidade_atual:
            raise EstoqueInsuficienteError(self.__quantidade_atual, quantidade)
        self.__quantidade_atual -= quantidade

    # --- conversão para dicionário (JSON) ---

    def to_dict(self):
        return {
            "id_produto": self.id_produto,
            "nome": self.nome,
            "marca": self.marca,
            "descricao": self.descricao,
            "preco": self.preco,
            "quantidade_atual": self.quantidade_atual,
            "estoque_minimo": self.estoque_minimo,
            "data_validade": self.data_validade,
            "id_categoria": self.id_categoria,
            "estoque_baixo": self.esta_com_estoque_baixo(),
        }

    @classmethod
    def from_dict(cls, dados, id_produto=None):
        return cls(
            id_produto,
            dados.get("nome"),
            dados.get("marca"),
            dados.get("descricao"),
            dados.get("preco"),
            dados.get("quantidade_atual", 0),
            dados.get("estoque_minimo", 0),
            dados.get("data_validade"),
            dados.get("id_categoria"),
        )


# ---------- MovimentacaoEstoque ----------

class MovimentacaoEstoque:
    def __init__(self, id_movimentacao, tipo, quantidade, data_hora, observacao, id_produto):
        self.id_movimentacao = id_movimentacao
        self.tipo = tipo
        self.quantidade = quantidade
        self.data_hora = data_hora   # preenchida pelo banco (CURRENT_TIMESTAMP)
        self.observacao = observacao
        self.id_produto = id_produto

    @property
    def tipo(self):
        return self.__tipo

    @tipo.setter
    def tipo(self, valor):
        if valor not in TIPOS_MOVIMENTACAO:
            raise ValidacaoError("O campo 'tipo' deve ser 'entrada' ou 'saida'.")
        self.__tipo = valor

    @property
    def quantidade(self):
        return self.__quantidade

    @quantidade.setter
    def quantidade(self, valor):
        self.__quantidade = _inteiro(valor, "quantidade", minimo=1)

    @property
    def observacao(self):
        return self.__observacao

    @observacao.setter
    def observacao(self, valor):
        self.__observacao = _texto(valor, "observacao", 250)

    @property
    def id_produto(self):
        return self.__id_produto

    @id_produto.setter
    def id_produto(self, valor):
        self.__id_produto = _inteiro(valor, "id_produto", minimo=1)

    def to_dict(self):
        return {
            "id_movimentacao": self.id_movimentacao,
            "tipo": self.tipo,
            "quantidade": self.quantidade,
            "data_hora": self.data_hora,
            "observacao": self.observacao,
            "id_produto": self.id_produto,
        }
