from enum import Enum

class Table(Enum):
	Basket_Order = "IGOR_CG_CESTAS_PEDIDO"
	Basket_Items = "IGOR_CG_CESTA_ESTOQUE"
	Clients = "IGOR_CG_CLIENTES"
	Items = "IGOR_CG_ESTOQUE"
	Groups = "IGOR_CG_GRUPOS_ITEM"
	Financial = "IGOR_CG_LANCAMENTOS_FIN"
	Groups_Items = "IGOR_CG_MEMBROS_GRUPO"
	Orders = "IGOR_CG_PEDIDOS"
	Baskets = "IGOR_CG_PRODUTOS"
	Addresses = "IGOR_CG_ENDERECOS_CLIENTES"
	Couriers = "IGOR_CG_ENTREGADORES"
	Deliveries = "IGOR_CG_ENTREGAS"
	Stock_Transactions = "IGOR_CG_MOVIMENTACOES_ESTOQUE"