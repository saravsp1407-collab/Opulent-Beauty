"""
seed.py - Carrega no banco os 10 categorias e 51 produtos que já existem
no seu site (script/dados.js), mantendo os MESMOS ids (as fotos do site
dependem deles). Este script apenas LÊ o dados.js; não altera nada nele.

Uso (dentro da pasta backend):
    python seed.py             -> carrega os dados se o banco estiver vazio
    python seed.py --recriar   -> apaga o banco e carrega tudo de novo
"""
import json
import os
import sys

import database
from database import criar_tabelas
from dao import CategoriaDAO, ProdutoDAO
from models import Categoria, Produto

ARQUIVO_DADOS = os.path.join(database.PASTA_BACKEND, "..", "script", "dados.js")


def ler_lista_js(texto, nome):
    """dados.js escreve 'const nome = [ ... ];' em formato igual ao JSON."""
    marcador = f"const {nome} = "
    inicio = texto.index(marcador) + len(marcador)
    lista, _ = json.JSONDecoder().raw_decode(texto[inicio:])
    return lista


def carregar(caminho_dados=ARQUIVO_DADOS):
    with open(caminho_dados, "r", encoding="utf-8") as arquivo:
        texto = arquivo.read()
    categorias = ler_lista_js(texto, "categorias")
    produtos = ler_lista_js(texto, "produtos")

    categoria_dao = CategoriaDAO()
    produto_dao = ProdutoDAO()
    for item in categorias:
        categoria_dao.inserir(Categoria(item["id_categoria"], item["nome"], item["descricao"]))
    for item in produtos:
        produto_dao.inserir(Produto.from_dict(item, item["id_produto"]))
    return len(categorias), len(produtos)


if __name__ == "__main__":
    if "--recriar" in sys.argv and os.path.exists(database.CAMINHO_BANCO):
        os.remove(database.CAMINHO_BANCO)
        print("Banco antigo apagado.")

    criar_tabelas()
    if CategoriaDAO().buscar_todos():
        print("O banco já tem dados. Use 'python seed.py --recriar' para recomeçar do zero.")
    else:
        qtd_categorias, qtd_produtos = carregar()
        print(f"Pronto! {qtd_categorias} categorias e {qtd_produtos} produtos carregados em:")
        print(database.CAMINHO_BANCO)
