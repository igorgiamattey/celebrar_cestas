-- IFPF.dbo.IGOR_CG_CLIENTES definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_CLIENTES;

CREATE TABLE IFPF.dbo.IGOR_CLIENTS (
	client_id int IDENTITY(1,1) NOT NULL,
	client_name varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	client_phone varchar(20) COLLATE Latin1_General_CI_AS NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_CLIENTS PRIMARY KEY (client_id)
);


-- IFPF.dbo.IGOR_CG_ENTREGADORES definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_ENTREGADORES;

CREATE TABLE IFPF.dbo.IGOR_COURIERS (
	courier_id int IDENTITY(1,1) NOT NULL,
	courier_name varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	courier_phone varchar(20) COLLATE Latin1_General_CI_AS NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_COURIERS PRIMARY KEY (courier_id)
);


-- IFPF.dbo.IGOR_CG_ESTOQUE definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_ESTOQUE;

CREATE TABLE IFPF.dbo.IGOR_STORAGE (
	item_id int IDENTITY(1,1) NOT NULL,
	item_name varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	item_unit varchar(10) COLLATE Latin1_General_CI_AS NOT NULL,
	item_qty decimal(10,2) NULL,
	item_min decimal(10,2) NULL,
	item_cost decimal(10,2) NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_STORAGE PRIMARY KEY (item_id)
);
ALTER TABLE IFPF.dbo.IGOR_STORAGE WITH NOCHECK ADD CONSTRAINT CK_IGOR_STORAGE_UNITS CHECK (([item_unit]='ML' OR [item_unit]='L' OR [item_unit]='G' OR [item_unit]='KG' OR [item_unit]='UN'));


-- IFPF.dbo.IGOR_CG_GRUPOS_ITEM definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_GRUPOS_ITEM;

CREATE TABLE IFPF.dbo.IGOR_GROUPS (
	group_id int IDENTITY(1,1) NOT NULL,
	group_name varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	isDeleted bit DEFAULT 0 NULL,
	CONSTRAINT PK_IGOR_GROUP PRIMARY KEY (group_id)
);


-- IFPF.dbo.IGOR_CG_PRODUTOS definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_PRODUTOS;

CREATE TABLE IFPF.dbo.IGOR_BASKETS (
	basket_id int IDENTITY(1,1) NOT NULL,
	basket_name varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	basket_price decimal(10,2) NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_BASKET PRIMARY KEY (basket_id)
);


-- IFPF.dbo.IGOR_CG_USUARIOS definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_USUARIOS;

CREATE TABLE IFPF.dbo.IGOR_USERS (
	user_id int IDENTITY(1,1) NOT NULL,
	username varchar(30) COLLATE Latin1_General_CI_AS NOT NULL,
	user_email varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	hash_pwd varchar(255) COLLATE Latin1_General_CI_AS NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_USER PRIMARY KEY (user_id),
	CONSTRAINT UQ_IGOR_USER_MAIL UNIQUE (user_email),
	CONSTRAINT UQ_IGOR_USER_NAME UNIQUE (username)
);


-- IFPF.dbo.IGOR_CG_CESTA_ESTOQUE definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_CESTA_ESTOQUE;

CREATE TABLE IFPF.dbo.IGOR_BASKET_ITEMS (
	basket_item_id int IDENTITY(1,1) NOT NULL,
	basket_id int NOT NULL,
	item_id int NULL,
	group_id int NULL,
	item_amount decimal(10,2) NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_BASKET_ITEM PRIMARY KEY (basket_item_id),
	CONSTRAINT FK_IGOR_BASKET_ITEM_GROUP FOREIGN KEY (group_id) REFERENCES IFPF.dbo.IGOR_GROUPS(group_id),
	CONSTRAINT FK_IGOR_BASKET_ITEM_ITEM FOREIGN KEY (item_id) REFERENCES IFPF.dbo.IGOR_STORAGE(item_id),
	CONSTRAINT FK_IGOR_BASKET_ITEM_BASKET FOREIGN KEY (basket_id) REFERENCES IFPF.dbo.IGOR_BASKETS(basket_id)
);
ALTER TABLE IFPF.dbo.IGOR_BASKET_ITEMS WITH NOCHECK ADD CONSTRAINT CK_IGOR_BASKET_ITEMS_ITEM_OR_GROUP CHECK (([item_id] IS NOT NULL AND [group_id] IS NULL OR [item_id] IS NULL AND [group_id] IS NOT NULL));


-- IFPF.dbo.IGOR_CG_ENDERECOS_CLIENTES definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_ENDERECOS_CLIENTES;

CREATE TABLE IFPF.dbo.IGOR_ADDRESSES (
	address_id int IDENTITY(1,1) NOT NULL,
	client_id int NOT NULL,
	address_txt varchar(200) COLLATE Latin1_General_CI_AS NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_ADDRESS PRIMARY KEY (address_id),
	CONSTRAINT FK_IGOR_ADDRESS_CLIENT FOREIGN KEY (client_id) REFERENCES IFPF.dbo.IGOR_CLIENTS(client_id)
);


-- IFPF.dbo.IGOR_CG_ENTREGAS definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_ENTREGAS;

CREATE TABLE IFPF.dbo.IGOR_DELIVERIES (
	delivery_id int IDENTITY(1,1) NOT NULL,
	courier_id int NULL,
	delivery_date date NOT NULL,
	delivery_status varchar(30) COLLATE Latin1_General_CI_AS NOT NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_DELIVERY PRIMARY KEY (delivery_id),
	CONSTRAINT FK_IGOR_DELIVERY_COURIER FOREIGN KEY (courier_id) REFERENCES IFPF.dbo.IGOR_COURIERS(courier_id)
);
ALTER TABLE IFPF.dbo.IGOR_DELIVERIES WITH NOCHECK ADD CONSTRAINT CK_IGOR_DELIVERIES_STATUS CHECK (([delivery_status]='DELIVERED' OR [delivery_status]='TRANSIT' OR [delivery_status]='PENDING' OR [delivery_status]='CANCELLED'));


-- IFPF.dbo.IGOR_CG_MEMBROS_GRUPO definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_MEMBROS_GRUPO;

CREATE TABLE IFPF.dbo.IGOR_GROUP_MEMBERS (
	group_id int NOT NULL,
	item_id int NOT NULL,
	group_item_qty decimal(10,2) NOT NULL,
	isDeleted bit DEFAULT 0 NULL,
	CONSTRAINT PK_IGOR_GROUP_MEMBER PRIMARY KEY (group_id,item_id),
	CONSTRAINT FK_IGOR_GROUP_MEMBER_GROUP FOREIGN KEY (group_id) REFERENCES IFPF.dbo.IGOR_GROUPS(group_id),
	CONSTRAINT FK_IGOR_GROUP_MEMBER_ITEM FOREIGN KEY (item_id) REFERENCES IFPF.dbo.IGOR_STORAGE(item_id)
);


-- IFPF.dbo.IGOR_CG_MOVIMENTACOES_ESTOQUE definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_MOVIMENTACOES_ESTOQUE;

CREATE TABLE IFPF.dbo.IGOR_STORAGE_MOVES (
	move_id int IDENTITY(1,1) NOT NULL,
	item_id int NOT NULL,
	move_type varchar(20) COLLATE Latin1_General_CI_AS NOT NULL,
	amount decimal(10,2) NOT NULL,
	move_date datetime DEFAULT getdate() NOT NULL,
	obs varchar(255) COLLATE Latin1_General_CI_AS NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_STORAGE_MOVE PRIMARY KEY (move_id),
	CONSTRAINT FK_IGOR_STORAGE_MOVE_ITEM FOREIGN KEY (item_id) REFERENCES IFPF.dbo.IGOR_STORAGE(item_id)
);
ALTER TABLE IFPF.dbo.IGOR_STORAGE_MOVES WITH NOCHECK ADD CONSTRAINT CK_IGOR_STORAGE_MOVES_TYPES CHECK (([move_type]='INCREASE_ORDER' OR [move_type]='DECREASE_ORDER' OR [move_type]='INCREASE' OR [move_type]='DECREASE'));


-- IFPF.dbo.IGOR_CG_PEDIDOS definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_PEDIDOS;

CREATE TABLE IFPF.dbo.IGOR_ORDERS (
	order_id int IDENTITY(1,1) NOT NULL,
	client_id int NOT NULL,
	order_date date NOT NULL,
	delivery_date date NULL,
	order_status varchar(30) COLLATE Latin1_General_CI_AS NOT NULL,
	order_subtotal decimal(10,2) NOT NULL,
	order_items varchar(MAX) COLLATE Latin1_General_CI_AS NOT NULL,
	obs varchar(255) COLLATE Latin1_General_CI_AS NULL,
	isDelivery bit DEFAULT 0 NOT NULL,
	delivery_id int NULL,
	address_id int NULL,
	delivery_fee decimal(10,2) DEFAULT 0.00 NOT NULL,
	order_total AS (order_subtotal+delivery_fee) PERSISTED,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_ORDER PRIMARY KEY (order_id),
	CONSTRAINT FK_IGOR_ORDER_CLIENT FOREIGN KEY (client_id) REFERENCES IFPF.dbo.IGOR_CLIENTS(client_id),
	CONSTRAINT FK_IGOR_ORDER_ADDRESS FOREIGN KEY (address_id) REFERENCES IFPF.dbo.IGOR_ADDRESSES(address_id),
	CONSTRAINT FK_IGOR_ORDER_DELIVERY FOREIGN KEY (delivery_id) REFERENCES IFPF.dbo.IGOR_DELIVERIES(delivery_id)
);
ALTER TABLE IFPF.dbo.IGOR_ORDERS WITH NOCHECK ADD CONSTRAINT CK_IGOR_ORDER_DELIVERY_ADDRESS CHECK (([isDelivery]=(0) OR [address_id] IS NOT NULL));
ALTER TABLE IFPF.dbo.IGOR_ORDERS WITH NOCHECK ADD CONSTRAINT CK_IGOR_ORDER_STATUS CHECK (([order_status]='READY' OR [order_status]='PREPARING' OR [order_status]='PENDING' OR [order_status]='DELIVERED' OR [order_status]='CONFIRMED' OR [order_status]='CANCELLED'));


-- IFPF.dbo.IGOR_CG_CESTAS_PEDIDO definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_CESTAS_PEDIDO;

CREATE TABLE IFPF.dbo.IGOR_ORDER_ITEMS (
	order_item_id int IDENTITY(1,1) NOT NULL,
	basket_id int NOT NULL,
	order_id int NOT NULL,
	amount int NOT NULL,
	isDeleted bit DEFAULT 0 NULL,
	CONSTRAINT PK_IGOR_ORDER_ITEM PRIMARY KEY (order_item_id),
	CONSTRAINT FK_IGOR_ORDER_ITEM_BASKET FOREIGN KEY (basket_id) REFERENCES IFPF.dbo.IGOR_BASKETS(basket_id),
	CONSTRAINT FK_IGOR_ORDER_ITEM_ORDER FOREIGN KEY (order_id) REFERENCES IFPF.dbo.IGOR_ORDERS(order_id)
);


-- IFPF.dbo.IGOR_CG_LANCAMENTOS_FIN definition

-- Drop table

-- DROP TABLE IFPF.dbo.IGOR_CG_LANCAMENTOS_FIN;

CREATE TABLE IFPF.dbo.IGOR_FINANCIAL_PAYMENTS (
	payment_id int IDENTITY(1,1) NOT NULL,
	payment_type varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	payment_category varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	payment_value decimal(10,2) NOT NULL,
	payment_status varchar(100) COLLATE Latin1_General_CI_AS NOT NULL,
	payment_date date NULL,
	payment_description varchar(150) COLLATE Latin1_General_CI_AS NOT NULL,
	order_id int NULL,
	supplier varchar(100) COLLATE Latin1_General_CI_AS NULL,
	origin_payment_id int NULL,
	isDeleted bit DEFAULT 0 NOT NULL,
	CONSTRAINT PK_IGOR_FINANCIAL_PAYMENT PRIMARY KEY (payment_id),
	CONSTRAINT FK_IGOR_FINANCIAL_PAYMENT_ORDER FOREIGN KEY (order_id) REFERENCES IFPF.dbo.IGOR_ORDERS(order_id)
);
ALTER TABLE IFPF.dbo.IGOR_FINANCIAL_PAYMENTS WITH NOCHECK ADD CONSTRAINT CK_IGOR_FINANCIAL_PAYMENTS_STATUS CHECK (([payment_status]='CANCELLED' OR [payment_status]='PAID' OR [payment_status]='PENDING'));
ALTER TABLE IFPF.dbo.IGOR_FINANCIAL_PAYMENTS WITH NOCHECK ADD CONSTRAINT CK_IGOR_FINANCIAL_PAYMENTS_TYPE CHECK (([payment_type]='EXPENSE' OR [payment_type]='INCOME'));
ALTER TABLE IFPF.dbo.IGOR_FINANCIAL_PAYMENTS WITH NOCHECK ADD CONSTRAINT CK_IGOR_FINANCIAL_PAYMENTS_CATEGORY CHECK (([payment_category]='REFUND' OR [payment_category]='OTHER' OR [payment_category]='MARKET' OR [payment_category]='ORDER_PAYMENT'));