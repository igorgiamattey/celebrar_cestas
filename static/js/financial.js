let searchTimeout;
const filterInput = monthFilter;

function handleSearch() {
	clearTimeout(searchTimeout);

	const query = document.getElementById('financial-search-bar').value;
	const chosenMonth = filterInput.getValue();
	const monthId = chosenMonth === '' ? null : Number(chosenMonth)

	const params = new URLSearchParams();

	if (query)
		params.set('search', query);

	if (monthId)
		params.set('month', monthId);

	history.replaceState({}, '', `/financeiro${params.toString() ? `?${params.toString()}` : ''}`)

	searchTimeout = setTimeout(() => {
		fetchText(`/financeiro/search?search=${encodeURIComponent(query)}&month=${chosenMonth}`)
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
			})
			.catch(handleError);
	}, 300);
}

const calendar_icon = document.getElementById('calendar-icon')
if (calendar_icon) {
	calendar_icon.innerHTML = ICON_CALENDAR;
	filterInput.control.appendChild(calendar_icon)
}