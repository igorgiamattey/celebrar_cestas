const searchBar = document.getElementById('catalogue-search-bar');

const handleSearch = createSearch({
	input: '#catalogue-search-bar',
	url: '/search_basket',
	body: '#catalogueTableBody',
	pageUrl: '/catalogo',
	label: 'Nenhuma cesta correspondente à pesquisa: '
});
