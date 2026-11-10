const botaoMenu = document.querySelector('.menu-botao');
const menu = document.querySelector('#menu');
botaoMenu.addEventListener('click', function () {
    const aberto = botaoMenu.getAttribute('aria-expanded') === 'true';
    botaoMenu.setAttribute('aria-expanded', String(!aberto));
    menu.classList.toggle('aberto', !aberto);
});
document.addEventListener('keydown', function (evento) {
    if (evento.key === 'Escape' && menu.classList.contains('aberto')) {
        menu.classList.remove('aberto');
        botaoMenu.setAttribute('aria-expanded', 'false');
        botaoMenu.focus();
    }
});
function imagemProduto(id) {
    return informacoesProdutos[id].imagem;
}
function prepararFoto(imagem) {
    imagem.referrerPolicy = 'no-referrer';
    imagem.addEventListener('error', function () {
        if (!imagem.getAttribute('data-falhou')) {
            imagem.setAttribute('data-falhou', 'sim');
            imagem.src = 'assets/foto-indisponivel.svg';
            imagem.alt = 'Foto não carregada. Consulte a fonte da foto nos detalhes.';
        }
    });
}
function nomeCategoria(id) {
    const categoria = categorias.find(function (item) { return item.id_categoria === id; });
    return categoria ? categoria.nome : 'Sem categoria';
}
function moeda(valor) {
    if (!Number.isFinite(valor)) return 'Preço a definir';
    return valor.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
}
function elemento(tag, classe, texto) {
    const novo = document.createElement(tag);
    if (classe) novo.className = classe;
    if (texto !== undefined) novo.textContent = texto;
    return novo;
}
function criarCard(produto, naHome) {
    const card = elemento('article', 'produto-card');
    const visual = elemento('div', 'produto-imagem');
    const imagem = elemento('img');
    imagem.src = imagemProduto(produto.id_produto);
    prepararFoto(imagem);
    imagem.alt = produto.nome + ' — ' + produto.marca;
    imagem.width = 320;
    imagem.height = 300;
    imagem.loading = 'lazy';
    visual.append(imagem, elemento('span', 'etiqueta', produto.marca));
    const info = elemento('div', 'produto-info');
    info.append(elemento('p', 'produto-categoria', nomeCategoria(produto.id_categoria)));
    info.append(elemento('h3', '', produto.nome), elemento('p', 'produto-marca', produto.marca));
    const linha = elemento('div', 'produto-linha');
    let situacao = 'Disponível';
    if (!Number.isFinite(produto.quantidade_atual)) situacao = 'Estoque a confirmar';
    else if (produto.quantidade_atual === 0) situacao = 'Sem estoque';
    else if (Number.isFinite(produto.quantidade_atual) && Number.isFinite(produto.estoque_minimo) && produto.quantidade_atual <= produto.estoque_minimo) situacao = 'Estoque baixo';
    if (informacoesProdutos[produto.id_produto].estoquePlanejado) situacao = 'Estoque planejado';
    const estoque = elemento('span', 'estoque', situacao);
    if (Number.isFinite(produto.quantidade_atual) && Number.isFinite(produto.estoque_minimo) && produto.quantidade_atual <= produto.estoque_minimo) estoque.classList.add('baixo');
    linha.append(elemento('span', 'preco', moeda(produto.preco)), estoque);
    info.append(linha);
    if (naHome) {
        const link = elemento('a', 'botao-contorno', 'Ver detalhes ↗');
        link.href = 'produtos.html?produto=' + produto.id_produto;
        link.setAttribute('aria-label', 'Ver detalhes de ' + produto.nome);
        info.append(link);
    } else {
        const botao = elemento('button', 'botao-contorno', 'Ver detalhes ↗');
        botao.type = 'button';
        botao.setAttribute('aria-label', 'Ver detalhes de ' + produto.nome);
        botao.addEventListener('click', function () { mostrarDetalhes(produto.id_produto, botao); });
        info.append(botao);
    }
    card.append(visual, info);
    return card;
}

const destaques = document.querySelector('#destaques');
if (destaques) {
    produtos.filter(function (produto) { return [1, 12, 23].includes(produto.id_produto); }).forEach(function (produto) { destaques.append(criarCard(produto, true)); });
}

const lista = document.querySelector('#lista-produtos');
const painelDetalhes = document.querySelector('#detalhes');
let ultimoBotaoDetalhes = null;

function mostrarDetalhes(id, origem) {
    const produto = produtos.find(function (item) { return item.id_produto === id; });
    if (!produto || !painelDetalhes) return;
    ultimoBotaoDetalhes = origem;
    const conteudo = document.querySelector('#detalhes-conteudo');
    conteudo.replaceChildren();
    const grade = elemento('div', 'detalhes-grade');
    const imagem = elemento('img');
    imagem.src = imagemProduto(id);
    prepararFoto(imagem);
    imagem.alt = produto.nome + ' — ' + produto.marca;
    imagem.width = 320;
    imagem.height = 300;
    const texto = elemento('div');
    const titulo = elemento('h2', '', produto.nome);
    titulo.id = 'detalhes-titulo';
    const informacoes = informacoesProdutos[id];
    texto.append(titulo, elemento('p', '', informacoes.descricaoCompleta || produto.descricao));
    const dados = elemento('dl', 'dados-detalhes');
    const campos = [
        ['Código', produto.id_produto], ['Marca', produto.marca],
        ['Categoria', nomeCategoria(produto.id_categoria)], ['Preço', moeda(produto.preco)],
        [informacoes.estoquePlanejado ? 'Quantidade planejada' : 'Quantidade atual', Number.isFinite(produto.quantidade_atual) ? produto.quantidade_atual + ' unidades' : 'A confirmar'],
        [informacoes.estoquePlanejado ? 'Estoque mínimo planejado' : 'Estoque mínimo', Number.isFinite(produto.estoque_minimo) ? produto.estoque_minimo + ' unidades' : 'A confirmar'],
        ['Validade informada', produto.data_validade ? produto.data_validade.split('-').reverse().join('/') : (informacoes.validadeMesAno || 'Consultar embalagem do lote')]
    ];
    campos.forEach(function (campo) {
        const grupo = elemento('div');
        grupo.append(elemento('dt', '', campo[0]), elemento('dd', '', campo[1]));
        dados.append(grupo);
    });
    texto.append(dados);
    if (informacoes.referenciaPreco) texto.append(elemento('p', 'nota-dados', informacoes.referenciaPreco));
    texto.append(elemento('h3', '', 'Validade e conservação'));
    texto.append(elemento('p', 'nota-validade', informacoes.prazoInformado));
    texto.append(elemento('p', 'nota-dados', informacoes.observacaoFoto));
    texto.append(elemento('p', 'nota-dados', informacoes.origemDescricao));
    const fonte = elemento('a', 'link-seta', 'Fonte da foto e referência do produto ↗');
    fonte.href = informacoes.fonte;
    fonte.target = '_blank';
    fonte.rel = 'noopener noreferrer';
    texto.append(fonte);
    grade.append(imagem, texto);
    conteudo.append(grade);
    painelDetalhes.hidden = false;
    painelDetalhes.focus({ preventScroll: true });
    painelDetalhes.scrollIntoView({ block: 'start' });
}

if (lista) {
    const busca = document.querySelector('#busca');
    const seletor = document.querySelector('#categoria');
    const seletorMarca = document.querySelector('#marca-filtro');
    const mais = document.querySelector('#carregar-mais');
    let quantidadeVisivel = 12;
    const marcas = [];
    produtos.forEach(function (produto) {
        if (!marcas.includes(produto.marca)) marcas.push(produto.marca);
    });
    marcas.sort().forEach(function (marca) {
        const opcao = elemento('option', '', marca);
        opcao.value = marca;
        seletorMarca.append(opcao);
    });
    categorias.forEach(function (categoria) {
        const opcao = elemento('option', '', categoria.nome);
        opcao.value = categoria.id_categoria;
        seletor.append(opcao);
    });
    function normalizar(texto) {
        return texto.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
    }
    function textoPesquisavel(produto) {
        const categoria = nomeCategoria(produto.id_categoria);
        const singular = categoria === 'Batons' ? 'batom' : '';
        return produto.nome + ' ' + produto.marca + ' ' + categoria + ' ' + singular;
    }
    function filtrar(manterQuantidade) {
        if (manterQuantidade !== true) quantidadeVisivel = 12;
        const termo = normalizar(busca.value);
        const encontrados = produtos.filter(function (produto) {
            const combinaTexto = normalizar(textoPesquisavel(produto)).includes(termo);
            const combinaCategoria = seletor.value === 'todas' || produto.id_categoria === Number(seletor.value);
            const combinaMarca = seletorMarca.value === 'todas' || produto.marca === seletorMarca.value;
            return combinaTexto && combinaCategoria && combinaMarca;
        });
        lista.replaceChildren();
        encontrados.slice(0, quantidadeVisivel).forEach(function (produto) { lista.append(criarCard(produto, false)); });
        const total = encontrados.length;
        mais.hidden = quantidadeVisivel >= total;
        mais.textContent = 'Mostrar mais produtos (' + Math.max(0, total - quantidadeVisivel) + ' restantes)';
        document.querySelector('#contagem').textContent = total === 1 ? '1 produto' : total + ' produtos';
        document.querySelector('#sem-resultados').hidden = total !== 0;
        painelDetalhes.hidden = true;
    }
    function limpar() {
        busca.value = '';
        seletor.value = 'todas';
        seletorMarca.value = 'todas';
        filtrar();
        busca.focus();
    }
    document.querySelector('#form-busca').addEventListener('submit', function (evento) { evento.preventDefault(); filtrar(); });
    busca.addEventListener('input', filtrar);
    seletor.addEventListener('change', filtrar);
    seletorMarca.addEventListener('change', filtrar);
    mais.addEventListener('click', function () {
        quantidadeVisivel += 12;
        filtrar(true);
    });
    document.querySelector('#limpar').addEventListener('click', limpar);
    document.querySelector('#limpar-vazio').addEventListener('click', limpar);
    document.querySelector('#fechar-detalhes').addEventListener('click', function () {
        painelDetalhes.hidden = true;
        if (ultimoBotaoDetalhes && ultimoBotaoDetalhes.isConnected) ultimoBotaoDetalhes.focus();
        else busca.focus();
    });
    const painelSugestoes = document.querySelector('#sugestoes-painel');
    const listaSugestoes = document.querySelector('#sugestoes-lista');
    const statusSugestoes = document.querySelector('#status-sugestoes');
    const controleBusca = document.querySelector('#busca-controle');
    let sugestoesAtuais = [];
    let indiceSugestao = -1;

    function fecharSugestoes() {
        painelSugestoes.hidden = true;
        busca.setAttribute('aria-expanded', 'false');
        busca.removeAttribute('aria-activedescendant');
        indiceSugestao = -1;
    }
    function selecionarSugestao(produto) {
        busca.value = produto.nome;
        filtrar();
        busca.focus();
        fecharSugestoes();
        statusSugestoes.textContent = produto.nome + ' selecionado.';
    }
    function atualizarSugestoes() {
        const termo = normalizar(busca.value);
        const correspondentes = produtos.filter(function (produto) {
            const texto = textoPesquisavel(produto);
            const combinaTexto = normalizar(texto).includes(termo);
            const combinaCategoria = seletor.value === 'todas' || produto.id_categoria === Number(seletor.value);
            const combinaMarca = seletorMarca.value === 'todas' || produto.marca === seletorMarca.value;
            return combinaTexto && combinaCategoria && combinaMarca;
        });
        sugestoesAtuais = correspondentes.slice(0, 6);
        indiceSugestao = -1;
        busca.removeAttribute('aria-activedescendant');
        listaSugestoes.replaceChildren();
        if (sugestoesAtuais.length === 0) {
            fecharSugestoes();
            statusSugestoes.textContent = 'Nenhuma sugestão encontrada. Tente outro nome, marca ou tipo de maquiagem.';
            return;
        }
        document.querySelector('#sugestoes-titulo').textContent = termo ? 'Sugestões para sua busca' : 'Explore alguns produtos';
        sugestoesAtuais.forEach(function (produto, indice) {
            const opcao = elemento('li', 'sugestao');
            opcao.id = 'sugestao-' + produto.id_produto;
            opcao.setAttribute('role', 'option');
            opcao.setAttribute('aria-selected', 'false');
            const foto = elemento('img');
            foto.src = imagemProduto(produto.id_produto);
            foto.alt = '';
            foto.width = 44;
            foto.height = 44;
            prepararFoto(foto);
            const textos = elemento('span', 'sugestao-textos');
            textos.append(elemento('strong', '', produto.nome));
            textos.append(elemento('span', '', produto.marca + ' · ' + nomeCategoria(produto.id_categoria)));
            opcao.append(foto, textos);
            opcao.addEventListener('mousedown', function (evento) { evento.preventDefault(); });
            opcao.addEventListener('click', function () { selecionarSugestao(produto); });
            listaSugestoes.append(opcao);
        });
        painelSugestoes.hidden = false;
        busca.setAttribute('aria-expanded', 'true');
        statusSugestoes.textContent = sugestoesAtuais.length + ' sugestões disponíveis. Use as setas e Enter para escolher.';
    }
    busca.addEventListener('focus', atualizarSugestoes);
    busca.addEventListener('input', atualizarSugestoes);
    busca.addEventListener('keydown', function (evento) {
        if (evento.key === 'Escape') {
            evento.preventDefault(); // Evita que o campo de busca apague o texto e reabra as sugestões.
            fecharSugestoes();
            return;
        }
        if (evento.key === 'Tab') { fecharSugestoes(); return; }
        if (evento.key === 'ArrowDown' || evento.key === 'ArrowUp') {
            evento.preventDefault();
            if (painelSugestoes.hidden) atualizarSugestoes();
            if (sugestoesAtuais.length === 0) return;
            if (evento.key === 'ArrowDown') indiceSugestao = (indiceSugestao + 1) % sugestoesAtuais.length;
            else indiceSugestao = indiceSugestao <= 0 ? sugestoesAtuais.length - 1 : indiceSugestao - 1;
            const opcoes = listaSugestoes.children;
            for (let i = 0; i < opcoes.length; i++) {
                opcoes[i].setAttribute('aria-selected', String(i === indiceSugestao));
            }
            busca.setAttribute('aria-activedescendant', opcoes[indiceSugestao].id);
            opcoes[indiceSugestao].scrollIntoView({ block: 'nearest' });
        }
        if (evento.key === 'Enter' && !painelSugestoes.hidden && indiceSugestao >= 0) {
            evento.preventDefault();
            selecionarSugestao(sugestoesAtuais[indiceSugestao]);
        }
    });
    document.addEventListener('mousedown', function (evento) {
        if (!controleBusca.contains(evento.target)) fecharSugestoes();
    });
    seletor.addEventListener('change', fecharSugestoes);
    seletorMarca.addEventListener('change', fecharSugestoes);
    document.querySelector('#form-busca').addEventListener('submit', fecharSugestoes);
    document.querySelector('#limpar').addEventListener('click', fecharSugestoes);
    document.querySelector('#limpar-vazio').addEventListener('click', fecharSugestoes);

    filtrar();
    const idDaUrl = Number(new URLSearchParams(window.location.search).get('produto'));
    if (idDaUrl) mostrarDetalhes(idDaUrl, null);
}
