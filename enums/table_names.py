from enum import Enum

class Table(Enum):
	Clients = "CELEBRAR_CLIENTS"
	Couriers = "CELEBRAR_COURIERS"
	Items = "CELEBRAR_STORAGE"
	Groups = "CELEBRAR_GROUPS"
	Baskets = "CELEBRAR_BASKETS"
	Basket_Items = "CELEBRAR_BASKET_ITEMS"
	Addresses = "CELEBRAR_ADDRESSES"
	Deliveries = "CELEBRAR_DELIVERIES"
	Groups_Items = "CELEBRAR_GROUP_MEMBERS"
	Stock_Transactions = "CELEBRAR_STORAGE_MOVES"
	Orders = "CELEBRAR_ORDERS"
	Basket_Order = "CELEBRAR_ORDER_ITEMS"
	Financial = "CELEBRAR_FINANCIAL_PAYMENTS"