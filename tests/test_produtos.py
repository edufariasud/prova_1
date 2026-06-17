import pytest
from conftest import SessaoTeste
from main import Produto

# 1. Listar produtos quando o banco está vazio
def test_listar_produtos_banco_vazio(client):
    resposta = client.get("/produtos")
    assert resposta.status_code == 200
    assert resposta.json() == []


# 2. Criar produto e verificar persistência direta no banco
def test_criar_produto_persistência_direta(client):
    payload = {"nome": "Teclado Mecânico", "preco": 250.00, "estoque": 10, "ativo": True}
    resposta = client.post("/produtos", json=payload)
    assert resposta.status_code == 201
    
    id_gerado = resposta.json()["id"]
    
    # Faz uma query direta no banco de dados de teste para confirmar a persistência
    db = SessaoTeste()
    prod_banco = db.query(Produto).filter(Produto.id == id_gerado).first()
    db.close()
    
    assert prod_banco is not None
    assert prod_banco.nome == "Teclado Mecânico"
    assert prod_banco.preco == 250.00
    assert prod_banco.estoque == 10
    assert prod_banco.ativo is True


# 3. Criar produto e verificar que aparece na listagem
def test_criar_produto_aparece_na_lista(client):
    payload = {"nome": "Mouse Gamer", "preco": 120.00, "estoque": 5}
    resposta_post = client.post("/produtos", json=payload)
    assert resposta_post.status_code == 201
    
    resposta_get = client.get("/produtos")
    assert resposta_get.status_code == 200
    
    lista = resposta_get.json()
    assert len(lista) == 1
    assert lista[0]["nome"] == "Mouse Gamer"


# 4. Buscar produto por id — caso de sucesso
def test_buscar_produto_por_id_sucesso(client, produto_existente):
    resposta = client.get(f"/produtos/{produto_existente.id}")
    assert resposta.status_code == 200
    
    dados = resposta.json()
    assert dados["id"] == produto_existente.id
    assert dados["nome"] == "Produto Inicial"
    assert dados["preco"] == 89.90


# 5. Buscar produto com id inexistente — deve retornar 404
def test_buscar_produto_id_inexistente(client):
    resposta = client.get("/produtos/99999")
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Produto não localizado."


# 6. Deletar produto — deve retornar 204
def test_deletar_produto_sucesso(client, produto_existente):
    resposta = client.delete(f"/produtos/{produto_existente.id}")
    assert resposta.status_code == 204


# 7. Deletar produto e confirmar remoção com GET subsequente
def test_deletar_produto_e_confirmar_remocao(client, produto_existente):
    id_produto = produto_existente.id
    
    # Exclui o item
    resposta_delete = client.delete(f"/produtos/{id_produto}")
    assert resposta_delete.status_code == 204
    
    # Valida que não existe mais via GET
    resposta_get = client.get(f"/produtos/{id_produto}")
    assert resposta_get.status_code == 404


# 8. Deletar produto inexistente — deve retornar 404
def test_deletar_produto_inexistente(client):
    resposta = client.delete("/produtos/99999")
    assert resposta.status_code == 404
    assert resposta.json()["detail"] == "Produto não localizado."


# 9. Teste parametrizado cobrindo payloads inválidos (status 422)
@pytest.mark.parametrize(
    "payload",
    [
        {"nome": "", "preco": 100.0, "estoque": 5},          # Nome vazio
        {"nome": "   ", "preco": 100.0, "estoque": 5},        # Nome apenas com espaços
        {"nome": "Produto Teste", "preco": 0.0, "estoque": 5}, # Preço igual a zero
        {"nome": "Produto Teste", "preco": -10.0, "estoque": 5} # Preço negativo
    ]
)
def test_criar_produto_payload_invalido(client, payload):
    resposta = client.post("/produtos", json=payload)
    assert resposta.status_code == 422


# 10. Validação do isolamento de banco entre execuções de testes
# Estes dois testes abaixo verificam se o estado de um teste não contamina o outro.
def test_verificar_isolamento_parte_1(client):
    payload = {"nome": "Produto Isolado", "preco": 50.00, "estoque": 10}
    resposta = client.post("/produtos", json=payload)
    assert resposta.status_code == 201
    
    # O banco deve ter exatamente 1 produto
    resposta_lista = client.get("/produtos")
    assert len(resposta_lista.json()) == 1


def test_verificar_isolamento_parte_2(client):
    # Por conta do teardown que limpa o banco de dados no conftest,
    # este teste inicia com o banco vazio, provando o isolamento.
    resposta_lista = client.get("/produtos")
    assert len(resposta_lista.json()) == 0
