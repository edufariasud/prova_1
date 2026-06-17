import os
import sys
import time
from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.exc import OperationalError
from pydantic import BaseModel, ConfigDict, field_validator

# 1. Configuração da Conexão com o Banco de Dados PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:senha_secreta_dev@localhost:5432/ecom_dev")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. Modelo de Dados do SQLAlchemy (ORM)
class Produto(Base):
    __tablename__ = "produtos"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, nullable=False)
    preco = Column(Float, nullable=False)
    estoque = Column(Integer, default=0, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)

# Tenta criar as tabelas no banco de dados na inicialização (apenas no ambiente real, não no pytest)
if "pytest" not in sys.modules:
    tentativas = 12
    for loop in range(tentativas):
        try:
            Base.metadata.create_all(bind=engine)
            break
        except OperationalError as erro:
            if loop == tentativas - 1:
                raise erro
            time.sleep(2)

# 3. Esquemas de Dados Pydantic
class ProdutoEntrada(BaseModel):
    nome: str
    preco: float
    estoque: int = 0
    ativo: bool = True

    @field_validator("nome")
    @classmethod
    def validar_nome(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("O nome do produto não pode ser vazio.")
        return v.strip()

    @field_validator("preco")
    @classmethod
    def validar_preco(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("O preço do produto deve ser maior que zero.")
        return v

class ProdutoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    preco: float
    estoque: int
    ativo: bool

# 4. Dependency Injection para Sessão do Banco
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 5. Inicialização da API FastAPI
app = FastAPI(title="API E-commerce de Produtos")

# 6. Rotas da API (Endpoints)
@app.get("/produtos", response_model=list[ProdutoSaida], status_code=200)
def listar_produtos(db: Session = Depends(get_db)):
    """Busca e retorna a listagem de todos os produtos cadastrados."""
    return db.query(Produto).all()

@app.post("/produtos", response_model=ProdutoSaida, status_code=201)
def criar_produto(corpo: ProdutoEntrada, db: Session = Depends(get_db)):
    """Gera o cadastro de um novo produto no catálogo."""
    novo_produto = Produto(
        nome=corpo.nome,
        preco=corpo.preco,
        estoque=corpo.estoque,
        ativo=corpo.ativo
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return novo_produto

@app.get("/produtos/{id}", response_model=ProdutoSaida, status_code=200)
def obter_produto(id: int, db: Session = Depends(get_db)):
    """Busca um produto específico utilizando o id como chave de pesquisa."""
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não localizado.")
    return produto

@app.delete("/produtos/{id}", status_code=204)
def remover_produto(id: int, db: Session = Depends(get_db)):
    """Exclui permanentemente um produto através do seu id."""
    produto = db.query(Produto).filter(Produto.id == id).first()
    if not produto:
        raise HTTPException(status_code=404, detail="Produto não localizado.")
    db.delete(produto)
    db.commit()
