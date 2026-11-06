
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request


# =====================================================
# CONFIGURAÇÕES
# =====================================================

load_dotenv()

app = Flask(__name__)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SECRET_KEY = os.getenv("SUPABASE_SECRET_KEY", "")


# =====================================================
# CONEXÃO COM SUPABASE
# =====================================================

def acessar_supabase(metodo, tabela, parametros=None, dados=None):

    if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
        raise RuntimeError("Credenciais do Supabase não configuradas.")

    resposta = requests.request(
        metodo,
        f"{SUPABASE_URL}/rest/v1/{tabela}",
        headers={
            "apikey": SUPABASE_SECRET_KEY,
            "Authorization": f"Bearer {SUPABASE_SECRET_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
        params=parametros,
        json=dados,
        timeout=15,
    )

    resposta.raise_for_status()

    if not resposta.content:
        return []

    return resposta.json()


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================

def normalizar_texto(valor):
    if valor is None:
        return ""

    return str(valor).strip()


def converter_inteiro(valor):
    if isinstance(valor, bool):
        raise ValueError("Valor inteiro inválido.")

    texto = normalizar_texto(valor)

    if not texto:
        raise ValueError("Valor obrigatório.")

    numero = int(texto)

    return numero


def validar_cliente(dados):

    if not isinstance(dados, dict):
        raise ValueError("Envie um objeto JSON válido.")

    nome = normalizar_texto(dados.get("nome"))
    email = normalizar_texto(dados.get("email")).lower()
    telefone = normalizar_texto(dados.get("telefone"))

    if not nome:
        raise ValueError("O campo nome é obrigatório.")

    if len(nome) < 2 or len(nome) > 80:
        raise ValueError("O nome deve ter entre 2 e 80 caracteres.")

    if not email:
        raise ValueError("O campo e-mail é obrigatório.")

    if "@" not in email or "." not in email.split("@")[-1]:
        raise ValueError("Informe um e-mail válido.")

    if telefone and len(telefone) > 20:
        raise ValueError("O telefone deve ter no máximo 20 caracteres.")

    return {
        "nome": nome,
        "email": email,
        "telefone": telefone or None,
    }


# =====================================================
# VERIFICAÇÃO DE CONFIGURAÇÃO
# =====================================================

@app.before_request
def conferir_configuracao():

    if request.path.startswith("/api/"):

        if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
            return jsonify(
                mensagem="Configure as credenciais do Supabase no arquivo .env."
            ), 503


# =====================================================
# PÁGINA INICIAL
# =====================================================

@app.get("/")
def inicio():

    return render_template("index.html")


# =====================================================
# CLIENTES
# =====================================================

@app.get("/api/clientes")
def listar_clientes():

    clientes = acessar_supabase(
        "GET",
        "clientes",
        {
            "select": "cliente_id,nome,email,telefone",
            "order": "nome.asc",
        },
    )

    return jsonify(clientes)


@app.post("/api/clientes")
def cadastrar_cliente():

    dados = request.get_json(silent=True)

    try:
        cliente = validar_cliente(dados)

        resultado = acessar_supabase(
            "POST",
            "clientes",
            dados=cliente,
        )

        item = resultado[0] if resultado else {}

        return jsonify({
            "mensagem": "Cliente cadastrado com sucesso.",
            "cliente": item,
        }), 201

    except ValueError as erro:

        return jsonify(mensagem=str(erro)), 400


# =====================================================
# CATEGORIAS
# =====================================================

@app.get("/api/categorias")
def listar_categorias():

    categorias = acessar_supabase(
        "GET",
        "categorias",
        {
            "select": "categoria_id,nome",
            "order": "nome.asc",
        },
    )

    return jsonify(categorias)


# =====================================================
# PRODUTOS
# =====================================================

@app.get("/api/produtos")
def listar_produtos():

    produtos = acessar_supabase(
        "GET",
        "produtos",
        {
            "select": "produto_id,nome,preco,estoque,categoria_id,categorias(nome)",
            "order": "produto_id.desc",
        },
    )

    return jsonify(produtos)


@app.post("/api/produtos")
def cadastrar_produto():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify(mensagem="Envie um objeto JSON válido."), 400

    campos = ["nome", "preco", "estoque", "categoria_id"]

    for campo in campos:

        valor = dados.get(campo)

        if valor is None or isinstance(valor, bool):
            return jsonify(
                mensagem=f"O campo {campo} é obrigatório."
            ), 400

    nome = normalizar_texto(dados["nome"])
    texto_preco = normalizar_texto(dados["preco"]).replace(",", ".")
    texto_estoque = normalizar_texto(dados["estoque"])
    texto_categoria = normalizar_texto(dados["categoria_id"])

    if len(nome) < 3 or len(nome) > 80:
        return jsonify(
            mensagem="O nome deve ter entre 3 e 80 caracteres."
        ), 400

    try:

        preco = Decimal(texto_preco)
        estoque = converter_inteiro(texto_estoque)
        categoria_id = converter_inteiro(texto_categoria)

    except (InvalidOperation, ValueError):
        return jsonify(
            mensagem="Informe preço, estoque e categoria válidos."
        ), 400

    if not preco.is_finite() or preco <= 0 or preco > Decimal("999999.99"):
        return jsonify(
            mensagem="O preço deve estar entre R$ 0,01 e R$ 999999,99."
        ), 400

    if preco != preco.quantize(Decimal("0.01")):
        return jsonify(
            mensagem="O preço deve ter no máximo duas casas decimais."
        ), 400

    if estoque < 0 or estoque > 1000000:
        return jsonify(
            mensagem="O estoque deve estar entre 0 e 1000000."
        ), 400

    if categoria_id <= 0 or categoria_id > 2147483647:
        return jsonify(
            mensagem="Selecione uma categoria válida."
        ), 400

    categorias = acessar_supabase(
        "GET",
        "categorias",
        {
            "select": "categoria_id",
            "categoria_id": f"eq.{categoria_id}",
        },
    )

    if not categorias:
        return jsonify(
            mensagem="A categoria informada não existe."
        ), 400

    acessar_supabase(
        "POST",
        "produtos",
        dados={
            "nome": nome,
            "preco": str(preco),
            "estoque": estoque,
            "categoria_id": categoria_id,
        },
    )

    return jsonify(
        mensagem="Produto cadastrado com sucesso."
    ), 201


# =====================================================
# CARRINHO
# =====================================================

@app.get("/api/carrinho")
def listar_carrinho():

    cliente_id = request.args.get("cliente_id", type=int)

    if cliente_id is None or cliente_id <= 0:
        return jsonify(
            mensagem="Informe um cliente válido."
        ), 400

    itens = acessar_supabase(
        "GET",
        "carrinho",
        {
            "select": "carrinho_id,cliente_id,produto_id,quantidade,produtos(produto_id,nome,preco)",
            "cliente_id": f"eq.{cliente_id}",
            "order": "carrinho_id.desc",
        },
    )

    itens_formatados = []
    total = Decimal("0.00")

    for item in itens:

        produto = item.get("produtos") or {}

        quantidade = int(item.get("quantidade") or 0)
        preco = Decimal(str(produto.get("preco") or "0"))

        subtotal = preco * quantidade
        total += subtotal

        itens_formatados.append({
            "carrinho_id": item.get("carrinho_id"),
            "cliente_id": item.get("cliente_id"),
            "produto_id": item.get("produto_id"),
            "nome": produto.get("nome") or "Produto",
            "quantidade": quantidade,
            "preco_unitario": float(preco),
            "subtotal": float(subtotal.quantize(Decimal("0.01"))),
        })

    return jsonify({
        "cliente_id": cliente_id,
        "itens": itens_formatados,
        "total": float(total.quantize(Decimal("0.01"))),
    })


@app.post("/api/carrinho")
def adicionar_item_carrinho():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify(
            mensagem="Envie um objeto JSON válido."
        ), 400

    try:

        cliente_id = converter_inteiro(dados.get("cliente_id"))
        produto_id = converter_inteiro(dados.get("produto_id"))
        quantidade = converter_inteiro(dados.get("quantidade"))

    except ValueError:

        return jsonify(
            mensagem="Informe cliente, produto e quantidade válidos."
        ), 400

    if cliente_id <= 0 or produto_id <= 0:
        return jsonify(
            mensagem="Selecione um cliente e produto válidos."
        ), 400

    if quantidade <= 0:
        return jsonify(
            mensagem="A quantidade deve ser maior que zero."
        ), 400

    # Verifica cliente

    clientes = acessar_supabase(
        "GET",
        "clientes",
        {
            "select": "cliente_id",
            "cliente_id": f"eq.{cliente_id}",
        },
    )

    if not clientes:
        return jsonify(
            mensagem="Cliente não encontrado."
        ), 404

    # Verifica produto e estoque

    produtos = acessar_supabase(
        "GET",
        "produtos",
        {
            "select": "produto_id,nome,estoque",
            "produto_id": f"eq.{produto_id}",
        },
    )

    if not produtos:
        return jsonify(
            mensagem="Produto não encontrado."
        ), 404

    produto = produtos[0]
    estoque_disponivel = int(produto.get("estoque") or 0)

    if quantidade > estoque_disponivel:
        return jsonify(
            mensagem=f"Estoque insuficiente. Disponível: {estoque_disponivel} unidades."
        ), 400

    # Verifica se o produto já existe no carrinho

    itens_existentes = acessar_supabase(
        "GET",
        "carrinho",
        {
            "select": "carrinho_id,produto_id",
            "cliente_id": f"eq.{cliente_id}",
            "produto_id": f"eq.{produto_id}",
        },
    )

    if itens_existentes:
        return jsonify(
            mensagem="Este produto já está no carrinho."
        ), 400

    # Adiciona produto

    item = acessar_supabase(
        "POST",
        "carrinho",
        dados={
            "cliente_id": cliente_id,
            "produto_id": produto_id,
            "quantidade": quantidade,
        },
    )

    registro = item[0] if item else {}

    return jsonify({
        "mensagem": "Produto adicionado ao carrinho.",
        "item": registro,
    }), 201


# =====================================================
# REMOVER ITEM DO CARRINHO
# =====================================================

@app.delete("/api/carrinho/<int:carrinho_id>")
def remover_item_carrinho(carrinho_id):

    itens = acessar_supabase(
        "GET",
        "carrinho",
        {
            "select": "carrinho_id",
            "carrinho_id": f"eq.{carrinho_id}",
        },
    )

    if not itens:
        return jsonify(
            mensagem="Item do carrinho não encontrado."
        ), 404

    acessar_supabase(
        "DELETE",
        "carrinho",
        parametros={
            "carrinho_id": f"eq.{carrinho_id}",
        },
    )

    return jsonify(
        mensagem="Item removido do carrinho."
    )


# =====================================================
# TRATAMENTO DE ERROS DO SUPABASE
# =====================================================

@app.errorhandler(requests.exceptions.RequestException)
def tratar_erro_supabase(erro):

    app.logger.exception(
        "Falha na comunicação com Supabase."
    )

    if isinstance(erro, requests.exceptions.HTTPError):

        try:
            detalhe = erro.response.json()
        except (ValueError, AttributeError):
            detalhe = {}

        if isinstance(detalhe, dict):

            codigo = detalhe.get("code")

            if codigo == "23505":
                return jsonify(
                    mensagem="Já existe um registro com esses dados."
                ), 409

            if codigo == "23503":
                return jsonify(
                    mensagem="Existe uma referência inválida no banco de dados."
                ), 400

            if codigo == "23514":
                return jsonify(
                    mensagem="Os dados não atendem às regras do banco."
                ), 400

    return jsonify(
        mensagem="Não foi possível acessar o banco de dados. Tente novamente."
    ), 503


# =====================================================
# TRATAMENTO DE ERROS INTERNOS
# =====================================================

@app.errorhandler(500)
def tratar_erro_inesperado(erro):

    app.logger.exception(
        "Erro interno inesperado: %s",
        erro,
    )

    return jsonify(
        mensagem="Ocorreu uma falha interna."
    ), 500


# =====================================================
# EXECUÇÃO
# =====================================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
    )
