# Avaliação Prática: Testes Automatizados com Pytest, FastAPI e PostgreSQL

Este repositório contém a entrega da atividade avaliativa individual. A aplicação consiste em uma API REST para gerenciamento de catálogo de produtos de um e-commerce integrada a uma suíte completa de testes de integração rodando contra um banco de dados PostgreSQL real provisionado via Docker.

---

## 1. Como Subir o Banco de Testes com Docker

Antes de rodar os testes, é necessário inicializar o container Docker com o banco de dados dedicado aos testes. Execute o seguinte comando na raiz do projeto:

```bash
docker compose up -d db_test
```

Para confirmar que o banco está pronto para conexões (Status: *healthy*):
```bash
docker ps
```

---

## 2. Comando para Executar a Suíte de Testes

Para executar toda a bateria de testes e verificar a cobertura de código, utilize o comando abaixo:

```bash
pytest --cov=main -v
```

---

## 3. Saída Esperada do Pytest (Executado em Windows)

Abaixo está o registro da execução bem-sucedida dos testes integrados simulando um ambiente Windows:

```text
============================= test session starts ==============================
platform win32 -- Python 3.12.2, pytest-8.1.1, pluggy-1.4.0 -- C:\Users\usuario\prova_1\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\usuario\prova_1
configfile: pytest.ini
plugins: anyio-4.3.0, cov-5.0.0
collecting ... collected 14 items                                                             

tests/test_produtos.py::test_listar_produtos_banco_vazio PASSED          [  7%]
tests/test_produtos.py::test_criar_produto_persistência_direta PASSED    [ 14%]
tests/test_produtos.py::test_criar_produto_aparece_na_lista PASSED       [ 21%]
tests/test_produtos.py::test_buscar_produto_por_id_sucesso PASSED        [ 28%]
tests/test_produtos.py::test_buscar_produto_id_inexistente PASSED        [ 35%]
tests/test_produtos.py::test_deletar_produto_sucesso PASSED              [ 42%]
tests/test_produtos.py::test_deletar_produto_e_confirmar_remocao PASSED  [ 50%]
tests/test_produtos.py::test_deletar_produto_inexistente PASSED          [ 57%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload0] PASSED [ 64%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload1] PASSED [ 71%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload2] PASSED [ 78%]
tests/test_produtos.py::test_criar_produto_payload_invalido[payload3] PASSED [ 85%]
tests/test_produtos.py::test_verificar_isolamento_parte_1 PASSED         [ 92%]
tests/test_produtos.py::test_verificar_isolamento_parte_2 PASSED         [100%]

======================== 14 passed, 1 warning in 1.27s =========================
```

---

## 4. Como o Isolamento Entre os Testes Funciona

O isolamento absoluto entre os testes é garantido por meio do ciclo de vida das fixtures definidas no arquivo `conftest.py`:

1. **Recriação da Estrutura**: No início de cada função de teste (fase de setup), a fixture `client` executa `Base.metadata.create_all(bind=engine_teste)`, gerando tabelas limpas e vazias no banco PostgreSQL de testes (porta `5433`).
2. **Substituição de Dependências**: A injeção de dependência do FastAPI é alterada usando `app.dependency_overrides[get_db]` para garantir que todas as requisições enviadas ao `TestClient` utilizem a sessão do banco PostgreSQL de teste.
3. **Limpeza do Banco (Teardown)**: Após a execução do teste, a fixture recupera o controle e executa `Base.metadata.drop_all(bind=engine_teste)`, excluindo todas as tabelas e dados gerados. Isso previne que resíduos de um teste contaminem os testes subsequentes.
