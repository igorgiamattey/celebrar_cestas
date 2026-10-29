let searchTimeout;
const checkbox = document.getElementById('orders-checkbox');

function handleSearch() {
	clearTimeout(searchTimeout);
	
	const query = document.getElementById('orders-search-bar').value;
	const openOnly = checkbox.checked;

	const params = new URLSearchParams();

	if (query)
		params.set('search', query);

	if (openOnly)
		params.set('openonly', 'true');

	history.replaceState({}, '', `/pedidos${params.toString() ? `?${params.toString()}` : ''}`)

	searchTimeout = setTimeout(() => {
		fetchText(`/search_order?search=${encodeURIComponent(query)}&openonly=${openOnly}`)
			.then(html => {
				const tableBody = document.getElementById('ordersTableBody');

				tableBody.innerHTML = html;

				if (!html.trim() && query.trim()) {
					const row = document.createElement('tr');
					row.classList.add('empty-search-row');
					
					const cell = document.createElement('td');
					
					cell.colSpan = tableBody.closest('table').querySelectorAll('thead th').length;
					cell.classList.add('text-center', 'py-4');
					
					const queryStyle = document.createElement('span');
					queryStyle.textContent = query;
					queryStyle.classList.add('search-query');

					cell.append('Nenhum pedido correspondente à pesquisa: ', queryStyle);

					row.appendChild(cell);
					tableBody.appendChild(row);
				}
			})
			.catch(handleError);
	}, 300);
}

checkbox.addEventListener('change', () => {
	handleSearch();
})