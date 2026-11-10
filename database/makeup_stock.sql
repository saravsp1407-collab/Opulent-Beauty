CREATE DATABASE IF NOT EXISTS makeup_stock;

USE makeup_stock;
CREATE TABLE IF NOT EXISTS categoria (
    id_categoria INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(80) NOT NULL UNIQUE,
    descricao VARCHAR(250)
);
CREATE TABLE IF NOT EXISTS produto (
    id_produto INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(120) NOT NULL,
    marca VARCHAR(80),
    descricao VARCHAR(250),
    preco DECIMAL(10,2) NOT NULL,
    quantidade_atual INT NOT NULL DEFAULT 0,
    estoque_minimo INT NOT NULL DEFAULT 0,
    data_validade DATE,
    id_categoria INT NOT NULL,

    CONSTRAINT chk_preco
        CHECK (preco >= 0),

    CONSTRAINT chk_quantidade
        CHECK (quantidade_atual >= 0),

    CONSTRAINT chk_estoque_minimo
        CHECK (estoque_minimo >= 0),

    FOREIGN KEY (id_categoria)
        REFERENCES categoria(id_categoria)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
CREATE TABLE IF NOT EXISTS movimentacao_estoque (
    id_movimentacao INT AUTO_INCREMENT PRIMARY KEY,
    tipo VARCHAR(10) NOT NULL,
    quantidade INT NOT NULL,
    data_hora DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    observacao VARCHAR(250),
    id_produto INT NOT NULL,

    CONSTRAINT chk_tipo
        CHECK (tipo IN ('entrada', 'saida')),

    CONSTRAINT chk_mov_quantidade
        CHECK (quantidade > 0),

    FOREIGN KEY (id_produto)
        REFERENCES produto(id_produto)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
);
CREATE INDEX idx_produto_categoria
ON produto(id_categoria);

CREATE INDEX idx_movimentacao_produto
ON movimentacao_estoque(id_produto);

CREATE INDEX idx_movimentacao_data
ON movimentacao_estoque(data_hora);
