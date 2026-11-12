"""
testar_api.py - Teste automático de toda a API (não precisa do servidor ligado).

Usa um banco TEMPORÁRIO, então não mexe no seu makeup_stock.db.
Uso:  python testar_api.py
"""
import os
import tempfile

# Banco temporário: precisa ser definido ANTES de importar o app.
pasta_temporaria = tempfile.mkdtemp()
os.environ["MAKEUP_DB"] = os.path.join(pasta_temporaria, "teste.db")

from app import app          # noqa: E402
import seed                  # noqa: E402

cliente = app.test_client()
total = 0


def verificar(descricao, condicao):
    global total
    total += 1
    print(("[OK]    " if condicao else "[FALHOU]"), descricao)
    if not condicao:
        raise SystemExit(f"\nTeste falhou: {descricao}")


# ---- 1. Banco e seed
qtd_cat, qtd_prod = seed.carregar()
verificar(f"seed carregou {qtd_cat} categorias e {qtd_prod} produtos", (qtd_cat, qtd_prod) == (10, 51))

r = cliente.get("/")
verificar("GET / responde 200", r.status_code == 200)

# ---- 2. Categorias
r = cliente.get("/categorias")
verificar("GET /categorias lista 10", r.status_code == 200 and len(r.json) == 10)

r = cliente.post("/categorias", json={"nome": "Pincéis", "descricao": "Acessórios"})
verificar("POST /categorias cria (201)", r.status_code == 201)
id_cat = r.json["id"]

r = cliente.post("/categorias", json={"nome": "Pincéis"})
verificar("categoria duplicada é bloqueada (409)", r.status_code == 409)

r = cliente.post("/categorias", json={"nome": "   "})
verificar("categoria sem nome é recusada (400)", r.status_code == 400)

r = cliente.put(f"/categorias/{id_cat}", json={"descricao": "Pincéis e esponjas"})
verificar("PUT /categorias/<id> edita (200)", r.status_code == 200)
verificar("edição foi gravada", cliente.get(f"/categorias/{id_cat}").json["descricao"] == "Pincéis e esponjas")

r = cliente.delete(f"/categorias/{id_cat}")
verificar("DELETE /categorias/<id> remove categoria vazia", r.status_code == 200)
verificar("categoria removida some (404)", cliente.get(f"/categorias/{id_cat}").status_code == 404)

r = cliente.delete("/categorias/1")
verificar("categoria com produtos não pode ser excluída (409)", r.status_code == 409)

# ---- 3. Produtos: cadastro e consulta
r = cliente.get("/produtos")
verificar("GET /produtos lista 51", r.status_code == 200 and len(r.json) == 51)

r = cliente.get("/produtos/1")
verificar("GET /produtos/1 devolve La Prairie", r.status_code == 200 and r.json["marca"] == "La Prairie")
verificar("GET /produtos/9999 devolve 404", cliente.get("/produtos/9999").status_code == 404)

novo = {"nome": "Batom Teste", "marca": "Marca X", "descricao": "Produto de teste",
        "preco": 99.9, "quantidade_atual": 10, "estoque_minimo": 5,
        "data_validade": "2028-12-31", "id_categoria": 5}
r = cliente.post("/produtos", json=novo)
verificar("POST /produtos cria (201)", r.status_code == 201)
id_prod = r.json["id"]
verificar("novo produto recebeu id depois dos 51", id_prod == 52)

r = cliente.get(f"/produtos/{id_prod}/movimentacoes")
verificar("produto novo com estoque gerou 'Estoque inicial'",
          len(r.json) == 1 and r.json[0]["observacao"] == "Estoque inicial")

for descricao, mudanca in [
    ("preço negativo", {"preco": -5}),
    ("nome vazio", {"nome": ""}),
    ("quantidade com texto", {"quantidade_atual": "abc"}),
    ("data em formato errado", {"data_validade": "31/12/2028"}),
]:
    r = cliente.post("/produtos", json={**novo, **mudanca})
    verificar(f"POST /produtos recusa {descricao} (400)", r.status_code == 400)

r = cliente.post("/produtos", json={**novo, "id_categoria": 999})
verificar("POST /produtos recusa categoria inexistente (409)", r.status_code == 409)

r = cliente.post("/produtos", data="isso nao e json", content_type="application/json")
verificar("POST /produtos recusa corpo inválido (400)", r.status_code == 400)

# ---- 4. Busca e filtros
r = cliente.get("/produtos?busca=dior")
verificar("busca 'dior' acha produtos da Dior", len(r.json) > 0 and all("dior" in p["marca"].lower() for p in r.json))
r = cliente.get("/produtos?busca=mascara")
verificar("busca sem acento 'mascara' acha 'Máscaras de cílios'", len(r.json) > 0)
r = cliente.get("/produtos?categoria=5")
verificar("filtro por categoria funciona", len(r.json) > 0 and all(p["id_categoria"] == 5 for p in r.json))
r = cliente.get("/produtos?marca=NARS")
verificar("filtro por marca funciona", len(r.json) > 0 and all(p["marca"] == "NARS" for p in r.json))
r = cliente.get("/produtos?categoria=abc")
verificar("categoria não numérica dá 400", r.status_code == 400)

# ---- 5. Edição e exclusão de produto
r = cliente.put(f"/produtos/{id_prod}", json={"preco": 120, "quantidade_atual": 9999})
verificar("PUT /produtos/<id> edita (200)", r.status_code == 200)
p = cliente.get(f"/produtos/{id_prod}").json
verificar("preço foi alterado", p["preco"] == 120)
verificar("PUT não altera quantidade (só movimentação altera)", p["quantidade_atual"] == 10)

# ---- 6. Movimentações
r = cliente.post("/movimentacoes/entrada", json={"id_produto": id_prod, "quantidade": 5, "observacao": "Reposição"})
verificar("entrada registrada (201)", r.status_code == 201)
verificar("estoque subiu para 15", r.json["produto"]["quantidade_atual"] == 15)

r = cliente.post("/movimentacoes/saida", json={"id_produto": id_prod, "quantidade": 12})
verificar("saída registrada (201) e estoque caiu para 3", r.status_code == 201 and r.json["produto"]["quantidade_atual"] == 3)
verificar("produto aparece com estoque_baixo=true", r.json["produto"]["estoque_baixo"] is True)

r = cliente.post("/movimentacoes/saida", json={"id_produto": id_prod, "quantidade": 50})
verificar("saída maior que o estoque é bloqueada (409)", r.status_code == 409)
verificar("estoque continuou 3 após a falha", cliente.get(f"/produtos/{id_prod}").json["quantidade_atual"] == 3)

r = cliente.post("/movimentacoes/entrada", json={"id_produto": id_prod, "quantidade": 0})
verificar("quantidade 0 é recusada (400)", r.status_code == 400)
r = cliente.post("/movimentacoes/entrada", json={"id_produto": 9999, "quantidade": 1})
verificar("movimentar produto inexistente dá 404", r.status_code == 404)

r = cliente.get("/produtos/estoque-baixo")
verificar("GET /produtos/estoque-baixo inclui o produto de teste", any(p["id_produto"] == id_prod for p in r.json))

r = cliente.get(f"/produtos/{id_prod}/movimentacoes")
verificar("histórico do produto tem 3 movimentações", len(r.json) == 3)
verificar("histórico vem da mais recente para a mais antiga", r.json[0]["tipo"] == "saida")
r = cliente.get(f"/movimentacoes?produto={id_prod}")
verificar("GET /movimentacoes?produto= filtra", len(r.json) == 3)
verificar("GET /movimentacoes lista tudo", len(cliente.get("/movimentacoes").json) > 3)

# ---- 7. Exclusão com histórico
r = cliente.delete(f"/produtos/{id_prod}")
verificar("produto com histórico não pode ser excluído (409)", r.status_code == 409)

# ---- 8. Extras
r = cliente.get("/rota-que-nao-existe")
verificar("rota inexistente devolve JSON 404", r.status_code == 404 and "erro" in r.json)
r = cliente.get("/produtos", headers={"Origin": "http://127.0.0.1:5500"})
verificar("CORS liberado para o front-end", r.headers.get("Access-Control-Allow-Origin") == "*")

print(f"\nTudo certo! {total} verificações passaram.")
