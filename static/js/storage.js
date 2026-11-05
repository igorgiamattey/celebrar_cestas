const searchBar = document.getElementById('storage-search-bar');

const handleSearch = createSearch({
	input: '#storage-search-bar',
	url: '/search_item',
	body: '#storageTableBody',
	pageUrl: '/estoque',
	label: 'Nenhum item correspondente à pesquisa: '
});
