let searchTimeout;

function handleSearch() {
	clearTimeout(searchTimeout);
	const query = document.getElementById('financial-search-bar').value;

	history.replaceState({}, '', `/financeiro${query ? `?search=${encodeURIComponent(query)}` : ''}`)

	searchTimeout = setTimeout(() => {
		fetch(`/financeiro/search?search=${encodeURIComponent(query)}`)
			.then(res => res.text())
			.then(html => {
				const tableBody = document.getElementById('financialTableBody');

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

					cell.append('Nenhum lançamento correspondente à pesquisa: ', queryStyle);

					row.appendChild(cell);
					tableBody.appendChild(row);
				}
			});
	}, 300);
}