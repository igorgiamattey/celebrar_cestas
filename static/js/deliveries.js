const searchBar = document.getElementById('deliveries-search-bar');
const checkbox = document.getElementById('deliveries-checkbox');

const handleSearch = createSearch({
	input: '#deliveries-search-bar',
	url: '/search_delivery',
	body: '#deliveriesTableBody',
	pageUrl: '/entregas',
	label: 'Nenhuma entrega correspondente à pesquisa: ',
	getFilters: () => {
		const params = new URLSearchParams();

		if (checkbox.checked)
			params.set('openonly', 'true');

		return params;
	}
});
checkbox.addEventListener('change', handleSearch)