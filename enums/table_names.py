from enum import Enum

class Table(Enum):
	Clients = "IGOR_CLIENTS"
	Couriers = "IGOR_COURIERS"
	Items = "IGOR_STORAGE"
	Groups = "IGOR_GROUPS"
	Baskets = "IGOR_BASKETS"
	Basket_Items = "IGOR_BASKET_ITEMS"
	Addresses = "IGOR_ADDRESSES"
	Deliveries = "IGOR_DELIVERIES"
	Groups_Items = "IGOR_GROUP_MEMBERS"
	Stock_Transactions = "IGOR_STORAGE_MOVES"
	Orders = "IGOR_ORDERS"
	Basket_Order = "IGOR_ORDER_ITEMS"
	Financial = "IGOR_FINANCIAL_PAYMENTS"