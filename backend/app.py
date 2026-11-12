"""
app.py - Rotas Flask: a API REST do MakeUp Stock (Opulent Beauty).

Apostila 4º Bimestre, Cap. 3 (Flask, rotas, jsonify) e Cap. 5.4 (app.py).
Mapeamento dos Casos de Uso do diagrama UML -> rotas (veja README_ETAPA2.md).

Para rodar:  python app.py   (servidor em http://127.0.0.1:5000)
"""
import sqlite3

from flask import Flask, jsonify, request

from database import criar_tabelas
from dao import CategoriaDAO, ProdutoDAO, MovimentacaoDAO
from excecoes import ValidacaoError, NaoEncontradoError, EstoqueInsuficienteError
from models import Categoria, Produto, MovimentacaoEstoque

app = Flask(__name__)
app.json.ensure_ascii = False   # mantém acentos no JSON
app.json.sort_keys = False      # mantém a ordem dos campos

criar_tabelas()                 # garante que as tabelas existam ao iniciar

categoria_dao = CategoriaDAO()
produto_dao = ProdutoDAO()
movimentacao_dao = MovimentacaoDAO()


# ------------------------------------------------------------ utilidades

def corpo_json():
    """Lê o corpo JSON da requisição (request.json) ou lança ValidacaoError."""
    dados = request.get_json(silent=True)
    if not isinstance(dados, dict):
        raise ValidacaoError("Envie um corpo JSON válido (objeto) na requisição.")
    return dados


def inteiro_da_url(texto, nome):
    """Converte um parâmetro da URL (?categoria=3) para inteiro."""
    try:
        return int(texto)
    except (TypeError, ValueError):
        raise ValidacaoError(f"O parâmetro '{nome}' deve ser um número inteiro.")


@app.after_request
def liberar_cors(resposta):
    """Permite que o front-end (outra porta/arquivo) chame a API via fetch().
    Será necessário na Etapa 3, quando o JavaScript consumir estas rotas."""
    resposta.headers["Access-Control-Allow-Origin"] = "*"
    resposta.headers["Access-Control-Allow-Headers"] = "Content-Type"
    resposta.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    return resposta


# ------------------------------------------------- tratamento de erros

@app.errorhandler(ValidacaoError)
def erro_validacao(e):
    return jsonify({"erro": str(e)}), 400


@app.errorhandler(NaoEncontradoError)
def erro_nao_encontrado(e):
    return jsonify({"erro": str(e)}), 404


@app.errorhandler(EstoqueInsuficienteError)
def erro_estoque(e):
    return jsonify({"erro": str(e), "disponivel": e.disponivel, "solicitado": e.solicitado}), 409


@app.errorhandler(sqlite3.IntegrityError)
def erro_integridade(e):
    texto = str(e).upper()
    if "UNIQUE" in texto:
        mensagem = "Já existe um registro com esse nome."
    elif "FOREIGN KEY" in texto:
        mensagem = ("Operação bloqueada: o registro está em uso por outros dados "
                    "ou a categoria informada não existe.")
    else:
        mensagem = "Operação viola uma regra do banco de dados."
    return jsonify({"erro": mensagem}), 409


@app.errorhandler(404)
def rota_inexistente(e):
    return jsonify({"erro": "Rota não encontrada."}), 404


@app.errorhandler(405)
def metodo_nao_permitido(e):
    return jsonify({"erro": "Método HTTP não permitido para esta rota."}), 405


# ------------------------------------------------------------------ início

@app.route("/")
def pagina_inicial():
    return jsonify({
        "api": "MakeUp Stock - Opulent Beauty",
        "status": "no ar",
        "rotas": [
            "GET/POST /categorias", "GET/PUT/DELETE /categorias/<id>",
            "GET/POST /produtos  (filtros: ?busca= &categoria= &marca=)",
            "GET /produtos/estoque-baixo",
            "GET/PUT/DELETE /produtos/<id>", "GET /produtos/<id>/movimentacoes",
            "POST /movimentacoes/entrada", "POST /movimentacoes/saida",
            "GET /movimentacoes  (filtro: ?produto=)",
        ],
    })


# --------------------------------------------------------------- categorias

@app.route("/categorias", methods=["GET"])
def listar_categorias():
    return jsonify([c.to_dict() for c in categoria_dao.buscar_todos()])


@app.route("/categorias/<int:id_categoria>", methods=["GET"])
def consultar_categoria(id_categoria):
    categoria = categoria_dao.buscar_por_id(id_categoria)
    if categoria is None:
        raise NaoEncontradoError("Categoria não encontrada.")
    return jsonify(categoria.to_dict())


@app.route("/categorias", methods=["POST"])
def criar_categoria():
    categoria = Categoria.from_dict(corpo_json())
    id_gerado = categoria_dao.inserir(categoria)
    return jsonify({"id": id_gerado, "mensagem": "Categoria criada com sucesso!"}), 201


@app.route("/categorias/<int:id_categoria>", methods=["PUT"])
def atualizar_categoria(id_categoria):
    existente = categoria_dao.buscar_por_id(id_categoria)
    if existente is None:
        raise NaoEncontradoError("Categoria não encontrada.")
    dados = {**existente.to_dict(), **corpo_json()}   # campos não enviados são mantidos
    categoria = Categoria.from_dict(dados, id_categoria)
    categoria_dao.atualizar(id_categoria, categoria)
    return jsonify({"mensagem": "Categoria atualizada!"})


@app.route("/categorias/<int:id_categoria>", methods=["DELETE"])
def remover_categoria(id_categoria):
    if not categoria_dao.remover(id_categoria):
        raise NaoEncontradoError("Categoria não encontrada.")
    return jsonify({"mensagem": "Categoria removida!"})


# ----------------------------------------------------------------- produtos

@app.route("/produtos", methods=["GET"])
def listar_produtos():
    id_categoria = request.args.get("categoria")
    if id_categoria in (None, "", "todas"):
        id_categoria = None
    else:
        id_categoria = inteiro_da_url(id_categoria, "categoria")
    marca = request.args.get("marca")
    if marca == "todas":
        marca = None
    produtos = produto_dao.buscar_todos(request.args.get("busca"), id_categoria, marca)
    return jsonify([p.to_dict() for p in produtos])


# Atenção: esta rota fixa precisa vir ANTES de /produtos/<int:id_produto> por clareza
@app.route("/produtos/estoque-baixo", methods=["GET"])
def listar_estoque_baixo():
    return jsonify([p.to_dict() for p in produto_dao.buscar_estoque_baixo()])


@app.route("/produtos/<int:id_produto>", methods=["GET"])
def consultar_produto(id_produto):
    produto = produto_dao.buscar_por_id(id_produto)
    if produto is None:
        raise NaoEncontradoError("Produto não encontrado.")
    return jsonify(produto.to_dict())


@app.route("/produtos", methods=["POST"])
def criar_produto():
    produto = Produto.from_dict(corpo_json())
    id_gerado = produto_dao.inserir(produto)
    return jsonify({"id": id_gerado, "mensagem": "Produto criado com sucesso!"}), 201


@app.route("/produtos/<int:id_produto>", methods=["PUT"])
def atualizar_produto(id_produto):
    existente = produto_dao.buscar_por_id(id_produto)
    if existente is None:
        raise NaoEncontradoError("Produto não encontrado.")
    dados = {**existente.to_dict(), **corpo_json()}
    dados["quantidade_atual"] = existente.quantidade_atual   # estoque só muda por movimentação
    produto = Produto.from_dict(dados, id_produto)
    produto_dao.atualizar(id_produto, produto)
    return jsonify({"mensagem": "Produto atualizado!"})


@app.route("/produtos/<int:id_produto>", methods=["DELETE"])
def remover_produto(id_produto):
    if not produto_dao.remover(id_produto):
        raise NaoEncontradoError("Produto não encontrado.")
    return jsonify({"mensagem": "Produto removido!"})


@app.route("/produtos/<int:id_produto>/movimentacoes", methods=["GET"])
def historico_do_produto(id_produto):
    if produto_dao.buscar_por_id(id_produto) is None:
        raise NaoEncontradoError("Produto não encontrado.")
    return jsonify([m.to_dict() for m in movimentacao_dao.buscar_por_produto(id_produto)])


# ------------------------------------------------------------ movimentações

def registrar_movimentacao(tipo):
    """Lógica comum às rotas de entrada e saída de estoque."""
    dados = corpo_json()
    movimentacao = MovimentacaoEstoque(
        None, tipo, dados.get("quantidade"), None,
        dados.get("observacao"), dados.get("id_produto"),
    )
    gravada, produto = movimentacao_dao.registrar(movimentacao)
    return jsonify({
        "mensagem": ("Entrada" if tipo == "entrada" else "Saída") + " registrada com sucesso!",
        "movimentacao": gravada.to_dict(),
        "produto": produto.to_dict(),
    }), 201


@app.route("/movimentacoes/entrada", methods=["POST"])
def registrar_entrada():
    return registrar_movimentacao("entrada")


@app.route("/movimentacoes/saida", methods=["POST"])
def registrar_saida():
    return registrar_movimentacao("saida")


@app.route("/movimentacoes", methods=["GET"])
def listar_movimentacoes():
    id_produto = request.args.get("produto")
    if id_produto not in (None, ""):
        id_produto = inteiro_da_url(id_produto, "produto")
    else:
        id_produto = None
    return jsonify([m.to_dict() for m in movimentacao_dao.buscar_todos(id_produto)])


if __name__ == "__main__":
    app.run(debug=True)
