let searchTimeout;
const checkbox = document.getElementById('deliveries-checkbox');

function handleSearch() {
	clearTimeout(searchTimeout);
	
	const query = document.getElementById('deliveries-search-bar').value;
	const openOnly = checkbox.checked;

	const params = new URLSearchParams();

	if (query)
		params.set('search', query);

	if (openOnly)
		params.set('openonly', 'true');

	history.replaceState({}, '', `/entregas${params.toString() ? `?${params.toString()}` : ''}`)

	searchTimeout = setTimeout(() => {
		fetch(`/entregas/search?search=${encodeURIComponent(query)}&openonly=${openOnly}`)
			.then(res => res.text())
			.then(html => {
				const tableBody = document.getElementById('deliveriesTableBody');

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

					cell.append('Nenhuma entrega correspondente à pesquisa: ', queryStyle);

					row.appendChild(cell);
					tableBody.appendChild(row);
				}
			});
	}, 300);
}

checkbox.addEventListener('change', () => {
	handleSearch();
})