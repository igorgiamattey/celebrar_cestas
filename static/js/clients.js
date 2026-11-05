const searchBar = document.getElementById('clients-search-bar');

const handleSearch = createSearch({
	input: '#clients-search-bar',
	url: '/search_client',
	body: '#clientsTableBody',
	pageUrl: '/clientes',
	label: 'Nenhum cliente correspondente à pesquisa: '
});
