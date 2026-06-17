import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app, Base, get_db, Produto

# URL de conexão com o banco do ambiente de testes (porta 5433)
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:senha_secreta_test@localhost:5433/ecom_test"
)

# Cria a engine específica para o banco de teste PostgreSQL
engine_teste = create_engine(TEST_DATABASE_URL)
SessaoTeste = sessionmaker(autocommit=False, autoflush=False, bind=engine_teste)


@pytest.fixture
def client():
    # 1. Cria a estrutura de tabelas no banco Postgres de teste
    Base.metadata.create_all(bind=engine_teste)

    # 2. Define o gerador de conexão substituto para injeção de dependência
    def override_get_db():
        sessao_teste = SessaoTeste()
        try:
            yield sessao_teste
        finally:
            sessao_teste.close()

    # 3. Altera a injeção do FastAPI para usar o banco de teste
    app.dependency_overrides[get_db] = override_get_db

    # 4. Fornece o cliente HTTP de teste
    yield TestClient(app)

    # 5. Limpa a injeção e destrói as tabelas ao encerrar o caso de teste (Teardown)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_teste)


@pytest.fixture
def produto_existente(client):
    """Fixture auxiliar que cadastra previamente um produto válido no banco de teste."""
    sessao_teste = SessaoTeste()
    produto = Produto(
        nome="Produto Inicial",
        preco=89.90,
        estoque=20,
        ativo=True
    )
    sessao_teste.add(produto)
    sessao_teste.commit()
    sessao_teste.refresh(produto)
    sessao_teste.close()
    return produto
