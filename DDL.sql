-- IFPF.dbo.IGOR_CG_CLIENTES definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_CLIENTES;

CREATE TABLE IFPF.dbo.IGOR_CG_CLIENTES (
	id_cliente int IDENTITY(1,1) NOT NULL,
	nome_razao varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	telefone varchar(20) COLLATE Latin1_General_CI_AS NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_CG_CLIENTE PRIMARY KEY (id_cliente)
);


-- IFPF.dbo.IGOR_CG_ESTOQUE definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_ESTOQUE;

CREATE TABLE IFPF.dbo.IGOR_CG_ESTOQUE (
	id_insumo int IDENTITY(1,1) NOT NULL,
	nome_insumo varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	unidade_medida varchar(10) COLLATE Latin1_General_CI_AS NOT NULL,
	qtd_estoque decimal(10,2) NULL,
	estoque_minimo decimal(10,2) NULL,
	custo_unitario decimal(10,2) NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_CG_ESTOQUE PRIMARY KEY (id_insumo)
);


-- IFPF.dbo.IGOR_CG_GRUPOS_ITEM definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_GRUPOS_ITEM;

CREATE TABLE IFPF.dbo.IGOR_CG_GRUPOS_ITEM (
	id_grupo int IDENTITY(1,1) NOT NULL,
	nome_grupo varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	isDeleted bit DEFAULT 0 NULL,
	CONSTRAINT PK__IGOR_CG___8B68D6886934CCC7 PRIMARY KEY (id_grupo)
);


-- IFPF.dbo.IGOR_CG_LANCAMENTOS_FIN definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_LANCAMENTOS_FIN;

CREATE TABLE IFPF.dbo.IGOR_CG_LANCAMENTOS_FIN (
	id_lancamento int IDENTITY(1,1) NOT NULL,
	id_pedido int NULL,
	tipo varchar(10) COLLATE Latin1_General_CI_AS NULL,
	descricao varchar(150) COLLATE Latin1_General_CI_AS NOT NULL,
	valor decimal(10,2) NOT NULL,
	data_vencimento date NOT NULL,
	data_pagamento date NULL,
	status varchar(20) COLLATE Latin1_General_CI_AS NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_CG_LANCAMENTOS PRIMARY KEY (id_lancamento)
);


-- IFPF.dbo.IGOR_CG_PEDIDOS definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_PEDIDOS;

CREATE TABLE IFPF.dbo.IGOR_CG_PEDIDOS (
	id_pedido int IDENTITY(1,1) NOT NULL,
	id_cliente int NOT NULL,
	data_pedido date NOT NULL,
	data_entrega date NULL,
	status_pedido varchar(30) COLLATE Latin1_General_CI_AS NULL,
	valor_total decimal(10,2) NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	observacao text COLLATE Latin1_General_CI_AS NULL,
	itens_pedido text COLLATE Latin1_General_CI_AS NOT NULL,
	CONSTRAINT PK_IGOR_CG_PEDIDO PRIMARY KEY (id_pedido)
);


-- IFPF.dbo.IGOR_CG_PRODUTOS definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_PRODUTOS;

CREATE TABLE IFPF.dbo.IGOR_CG_PRODUTOS (
	id_produto int IDENTITY(1,1) NOT NULL,
	nome_cesta varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	preco_venda decimal(10,2) NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_CG_PRODUTO PRIMARY KEY (id_produto)
);


-- IFPF.dbo.IGOR_CG_CESTAS_PEDIDO definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_CESTAS_PEDIDO;

CREATE TABLE IFPF.dbo.IGOR_CG_CESTAS_PEDIDO (
	id_cestas_pedido int IDENTITY(1,1) NOT NULL,
	id_produto int NOT NULL,
	id_pedido int NOT NULL,
	quantidade int NOT NULL,
	isDeleted bit DEFAULT 0 NULL,
	CONSTRAINT PK__IGOR_CG___5F3D07189D13BDCB PRIMARY KEY (id_cestas_pedido),
	CONSTRAINT FK_BasketOrders_Basket FOREIGN KEY (id_produto) REFERENCES IFPF.dbo.IGOR_CG_PRODUTOS(id_produto),
	CONSTRAINT FK_BasketOrders_Orders FOREIGN KEY (id_pedido) REFERENCES IFPF.dbo.IGOR_CG_PEDIDOS(id_pedido)
);


-- IFPF.dbo.IGOR_CG_CESTA_ESTOQUE definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_CESTA_ESTOQUE;

CREATE TABLE IFPF.dbo.IGOR_CG_CESTA_ESTOQUE (
	id_produto int NOT NULL,
	id_insumo int NULL,
	quantidade_utilizada decimal(10,2) NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	id_cesta_insumo int IDENTITY(1,1) NOT NULL,
	id_grupo int NULL,
	CONSTRAINT PK_IGOR_CG_CESTA_ESTOQUE PRIMARY KEY (id_cesta_insumo),
	CONSTRAINT FK_BasketItems_Group FOREIGN KEY (id_grupo) REFERENCES IFPF.dbo.IGOR_CG_GRUPOS_ITEM(id_grupo)
);
ALTER TABLE IFPF.dbo.IGOR_CG_CESTA_ESTOQUE WITH NOCHECK ADD CONSTRAINT CK_BasketItems_ItemOrGroup CHECK (([id_insumo] IS NOT NULL AND [id_grupo] IS NULL OR [id_insumo] IS NULL AND [id_grupo] IS NOT NULL));


-- IFPF.dbo.IGOR_CG_MEMBROS_GRUPO definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_MEMBROS_GRUPO;

CREATE TABLE IFPF.dbo.IGOR_CG_MEMBROS_GRUPO (
	id_grupo int NOT NULL,
	id_insumo int NOT NULL,
	isDeleted bit DEFAULT 0 NULL,
	qtd_item_grupo decimal(38,0) DEFAULT 1.0 NOT NULL,
	CONSTRAINT PK_GroupMembers PRIMARY KEY (id_grupo,id_insumo),
	CONSTRAINT FK_GroupMembers_Group FOREIGN KEY (id_grupo) REFERENCES IFPF.dbo.IGOR_CG_GRUPOS_ITEM(id_grupo),
	CONSTRAINT FK_GroupMembers_Item FOREIGN KEY (id_insumo) REFERENCES IFPF.dbo.IGOR_CG_ESTOQUE(id_insumo)
);


-- IFPF.dbo.IGOR_CG_MOVIMENTACOES_ESTOQUE definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_MOVIMENTACOES_ESTOQUE;

CREATE TABLE IFPF.dbo.IGOR_CG_MOVIMENTACOES_ESTOQUE (
	id_movimentacao int IDENTITY(1,1) NOT NULL,
	id_insumo int NOT NULL,
	tipo_movimentacao varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	quantidade decimal(10,2) NOT NULL,
	data_movimentacao datetime DEFAULT getdate() NOT NULL,
	observacao varchar(255) COLLATE Latin1_General_CI_AS NULL,
	CONSTRAINT PK__IGOR_CG___A7C9B9D3D9317882 PRIMARY KEY (id_movimentacao),
	CONSTRAINT FK_MOV_ESTOQUE_ITEM FOREIGN KEY (id_insumo) REFERENCES IFPF.dbo.IGOR_CG_ESTOQUE(id_insumo)
);