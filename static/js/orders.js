const searchBar = document.getElementById('orders-search-bar');
const checkbox = document.getElementById('orders-checkbox');

const handleSearch = createSearch({
	input: '#orders-search-bar',
	url: '/search_order',
	body: '#ordersTableBody',
	pageUrl: '/pedidos',
	label: 'Nenhum pedido correspondente à pesquisa: ',
	getFilters: () => {
		const params = new URLSearchParams();

		if (checkbox.checked)
			params.set('openonly', 'true');

		return params;
	}
});
checkbox.addEventListener('change', handleSearch)