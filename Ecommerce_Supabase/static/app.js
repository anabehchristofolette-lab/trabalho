const formulario = document.getElementById("formulario");
const mensagem = document.getElementById("mensagem");
const mensagemLista = document.getElementById("mensagem-lista");
const lista = document.getElementById("lista-produtos");
const campoCategoria = document.getElementById("categoria");
const botaoCadastrar = document.getElementById("botao-cadastrar");
const formularioCliente = document.getElementById("formulario-cliente");
const mensagemCliente = document.getElementById("mensagem-cliente");
const clienteSelect = document.getElementById("cliente-select");
const formularioCarrinho = document.getElementById("formulario-carrinho");
const mensagemCarrinho = document.getElementById("mensagem-carrinho");
const produtoCarrinho = document.getElementById("produto-carrinho");
const listaCarrinho = document.getElementById("lista-carrinho");
const totalCarrinho = document.getElementById("total-carrinho");

function mostrarMensagem(texto, sucesso, alvo = mensagem) {
  alvo.textContent = texto;
  alvo.className = `mensagem ${sucesso ? "sucesso" : "erro"}`;
}

function formatarDinheiro(valor) {
  return Number(valor).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

async function carregarCategorias() {
  try {
    const resposta = await fetch("/api/categorias");
    const dados = await resposta.json();
    if (!resposta.ok) {
      mostrarMensagem(dados.mensagem, false);
      return;
    }

    campoCategoria.replaceChildren();
    const opcaoPadrao = document.createElement("option");
    opcaoPadrao.value = "";
    opcaoPadrao.textContent = "Selecione uma categoria";
    campoCategoria.appendChild(opcaoPadrao);

    for (const categoria of dados) {
      const opcao = document.createElement("option");
      opcao.value = categoria.categoria_id;
      opcao.textContent = categoria.nome;
      campoCategoria.appendChild(opcao);
    }

    if (dados.length === 0) {
      mostrarMensagem("Cadastre as categorias executando o SQL da aula.", false);
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível carregar as categorias. Confira o servidor.", false);
  }
}

async function carregarProdutos() {
  mensagemLista.textContent = "Consultando produtos...";
  try {
    const resposta = await fetch("/api/produtos");
    const produtos = await resposta.json();
    if (!resposta.ok) {
      mensagemLista.textContent = produtos.mensagem;
      return;
    }

    lista.replaceChildren();
    produtoCarrinho.replaceChildren();

    const opcaoPadrao = document.createElement("option");
    opcaoPadrao.value = "";
    opcaoPadrao.textContent = "Selecione um produto";
    produtoCarrinho.appendChild(opcaoPadrao);

    for (const produto of produtos) {
      const linha = document.createElement("tr");
      const valores = [
        produto.nome,
        produto.categorias ? produto.categorias.nome : "Sem categoria",
        formatarDinheiro(produto.preco),
        produto.estoque,
      ];

      for (const valor of valores) {
        const celula = document.createElement("td");
        celula.textContent = valor;
        linha.appendChild(celula);
      }
      lista.appendChild(linha);

      const opcao = document.createElement("option");
      opcao.value = produto.produto_id;
      opcao.textContent = `${produto.nome} · ${formatarDinheiro(produto.preco)}`;
      produtoCarrinho.appendChild(opcao);
    }

    mensagemLista.textContent = produtos.length === 0 ? "Nenhum produto cadastrado." : "Lista atualizada.";
  } catch (erro) {
    mensagemLista.textContent = "Não foi possível atualizar a lista. Confira o servidor.";
  }
}

async function carregarClientes() {
  try {
    const resposta = await fetch("/api/clientes");
    const dados = await resposta.json();

    if (!resposta.ok) {
      mostrarMensagem(dados.mensagem, false, mensagemCliente);
      return;
    }

    clienteSelect.replaceChildren();
    const opcaoPadrao = document.createElement("option");
    opcaoPadrao.value = "";
    opcaoPadrao.textContent = "Selecione um cliente";
    clienteSelect.appendChild(opcaoPadrao);

    for (const cliente of dados) {
      const opcao = document.createElement("option");
      opcao.value = cliente.cliente_id;
      opcao.textContent = `${cliente.nome} · ${cliente.email}`;
      clienteSelect.appendChild(opcao);
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível carregar os clientes. Confira o servidor.", false, mensagemCliente);
  }
}

async function carregarCarrinho() {
  const clienteId = Number(clienteSelect.value);

  if (!clienteId) {
    listaCarrinho.replaceChildren();
    totalCarrinho.textContent = "R$ 0,00";
    return;
  }

  try {
    const resposta = await fetch(`/api/carrinho?cliente_id=${clienteId}`);
    const dados = await resposta.json();

    if (!resposta.ok) {
      mostrarMensagem(dados.mensagem, false, mensagemCarrinho);
      return;
    }

    listaCarrinho.replaceChildren();
    if (!dados.itens || dados.itens.length === 0) {
      const linhaVazia = document.createElement("tr");
      const celula = document.createElement("td");
      celula.colSpan = 5;
      celula.textContent = "Nenhum item adicionado ao carrinho.";
      linhaVazia.appendChild(celula);
      listaCarrinho.appendChild(linhaVazia);
    } else {
      for (const item of dados.itens) {
        const linha = document.createElement("tr");

        const colunaProduto = document.createElement("td");
        colunaProduto.textContent = item.nome;

        const colunaQtd = document.createElement("td");
        colunaQtd.textContent = item.quantidade;

        const colunaPreco = document.createElement("td");
        colunaPreco.textContent = formatarDinheiro(item.preco_unitario);

        const colunaSubtotal = document.createElement("td");
        colunaSubtotal.textContent = formatarDinheiro(item.subtotal);

        const colunaAcao = document.createElement("td");
        const botaoRemover = document.createElement("button");
        botaoRemover.type = "button";
        botaoRemover.className = "secundario pequeno";
        botaoRemover.textContent = "Remover";
        botaoRemover.dataset.remover = item.carrinho_id;
        colunaAcao.appendChild(botaoRemover);

        linha.append(colunaProduto, colunaQtd, colunaPreco, colunaSubtotal, colunaAcao);
        listaCarrinho.appendChild(linha);
      }
    }

    totalCarrinho.textContent = formatarDinheiro(dados.total || 0);
    mensagemCarrinho.textContent = "Carrinho atualizado.";
    mensagemCarrinho.className = "mensagem sucesso";
  } catch (erro) {
    mostrarMensagem("Não foi possível carregar o carrinho. Confira o servidor.", false, mensagemCarrinho);
  }
}

async function cadastrarProduto(evento) {
  evento.preventDefault();
  botaoCadastrar.disabled = true;
  mostrarMensagem("Enviando dados...", true);

  const produto = {
    nome: document.getElementById("nome").value,
    categoria_id: campoCategoria.value,
    preco: document.getElementById("preco").value,
    estoque: document.getElementById("estoque").value,
  };

  try {
    const resposta = await fetch("/api/produtos", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(produto),
    });
    const dados = await resposta.json();
    mostrarMensagem(dados.mensagem, resposta.ok);
    if (resposta.ok) {
      formulario.reset();
      await carregarProdutos();
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível confirmar o cadastro. Atualize a lista antes de reenviar.", false);
  } finally {
    botaoCadastrar.disabled = false;
  }
}

async function cadastrarCliente(evento) {
  evento.preventDefault();

  const cliente = {
    nome: document.getElementById("nome-cliente").value,
    email: document.getElementById("email-cliente").value,
    telefone: document.getElementById("telefone-cliente").value,
  };

  try {
    const resposta = await fetch("/api/clientes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(cliente),
    });
    const dados = await resposta.json();
    mostrarMensagem(dados.mensagem, resposta.ok, mensagemCliente);

    if (resposta.ok) {
      formularioCliente.reset();
      await carregarClientes();
      if (dados.cliente && dados.cliente.cliente_id) {
        clienteSelect.value = String(dados.cliente.cliente_id);
        await carregarCarrinho();
      }
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível cadastrar o cliente. Tente novamente.", false, mensagemCliente);
  }
}

async function adicionarAoCarrinho(evento) {
  evento.preventDefault();

  const clienteId = Number(clienteSelect.value);
  const produtoId = Number(produtoCarrinho.value);
  const quantidade = Number(document.getElementById("quantidade-carrinho").value);

  if (!clienteId) {
    mostrarMensagem("Selecione um cliente antes de adicionar produtos.", false, mensagemCarrinho);
    return;
  }

  if (!produtoId) {
    mostrarMensagem("Selecione um produto do catálogo.", false, mensagemCarrinho);
    return;
  }

  if (!Number.isFinite(quantidade) || quantidade <= 0) {
    mostrarMensagem("A quantidade deve ser maior que zero.", false, mensagemCarrinho);
    return;
  }

  try {
    const resposta = await fetch("/api/carrinho", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cliente_id: clienteId, produto_id: produtoId, quantidade }),
    });
    const dados = await resposta.json();
    mostrarMensagem(dados.mensagem, resposta.ok, mensagemCarrinho);

    if (resposta.ok) {
      formularioCarrinho.reset();
      document.getElementById("quantidade-carrinho").value = 1;
      await carregarCarrinho();
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível adicionar o item ao carrinho.", false, mensagemCarrinho);
  }
}

async function removerItemCarrinho(evento) {
  const botao = evento.target.closest("button[data-remover]");
  if (!botao) {
    return;
  }

  const carrinhoId = botao.dataset.remover;
  try {
    const resposta = await fetch(`/api/carrinho/${carrinhoId}`, { method: "DELETE" });
    const dados = await resposta.json();
    mostrarMensagem(dados.mensagem, resposta.ok, mensagemCarrinho);

    if (resposta.ok) {
      await carregarCarrinho();
    }
  } catch (erro) {
    mostrarMensagem("Não foi possível remover o item do carrinho.", false, mensagemCarrinho);
  }
}

formulario.addEventListener("submit", cadastrarProduto);
document.getElementById("botao-atualizar").addEventListener("click", carregarProdutos);
formularioCliente.addEventListener("submit", cadastrarCliente);
formularioCarrinho.addEventListener("submit", adicionarAoCarrinho);
listaCarrinho.addEventListener("click", removerItemCarrinho);
clienteSelect.addEventListener("change", carregarCarrinho);

carregarCategorias();
carregarProdutos();
carregarClientes();a