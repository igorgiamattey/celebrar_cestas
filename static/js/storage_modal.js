// === GLOBAL VARIABLES ===
let originalItemValues = {};
let groupItems = [];

// === TOMSELECT DATA ===
const availableItems = JSON.parse(
	document.getElementById('mngGroup-itemSelect').dataset.items
);

// === TOMSELECT DEFINITIONS ===
const mngGroupsGroupSelector = new TomSelect('#mngGroup-groupSelect', {
	allowEmptyOption: true, 
	create: false,
	maxOptions: null,
	sortField: '$order'
});

const groupItemSelector = new TomSelect('#mngGroup-itemSelect', {
	options: availableItems,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	maxOptions: null,
	sortField: [
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

// === HELPERS ===
function toggleSaveStorageButton(mode, area='item') {
	let fields = [];
	if (area === 'item') {
		fields = [
			`${mode}Item-name`,
			`${mode}Item-amount`,
			`${mode}Item-unit`,
			`${mode}Item-minimal`,
			`${mode}Item-cost`
		];
	}
	else if (area === 'move' && mode === 'new') {
		fields = [
			'newMove-type',
			'newMove-quantity'
		];
	}
	else
		return;
	area = area.charAt(0).toUpperCase() + area.slice(1);

	const button = `${mode}${area}-saveBtn`;
	
	toggleSaveButton(
			fields,
			button
	)
}

// === MISSING ITEM ===
function toggleMissingButton() {
	fetchJson('/missing_items')
		.then(data => {
			const list = data.missing_items;
			const button = document.getElementById('missItem-btn');
			button.disabled = list.length === 0;
			button.title = (list.length === 0) ? "Nenhum item está faltando ou próximo de acabar" : "";
		})
		.catch(err => {
			console.error("Failed to fetch missing items: ", err);
			showSnackbar('Não foi possível carregar os itens faltantes.', 'error');
		});		
}

// === CRUD ===
async function saveMove() {
	const id = document.getElementById('stockMovements-modal').dataset.id;

	const moveType = document.getElementById('newMove-type').value;
	const moveQtyInput = document.getElementById('newMove-quantity').value;
	const moveObs = document.getElementById('newMove-obs').value;

	const csrfToken = document.querySelector('input[name="csrf_token"]').value;
	const moveQty = normaliseComma(moveQtyInput);
	
	try {
		await fetchJson(`/new_movement/${id}`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				'X-CSRFToken': csrfToken
			},
			body: JSON.stringify({
				type: moveType,
				quantity: moveQty,
				obs: moveObs
			})
		});
	}
	catch (err) {
		handleError(err);
		return;
	}

	queueSnackbar('Movimentação registrada!', 'success');
	window.location.reload()
}

async function deleteItem() {
	const id = document.getElementById('viewItem-id').value;
	
	const confirmed = await openConfirm('Excluir item?', 'Tem certeza que deseja excluir este item?');
	
	if (confirmed) {
		const csrfToken = document.querySelector('input[name="csrf_token"]').value;
		fetch(`/delete_item/${id}`, { method: 'POST', headers: {'X-CSRFToken': csrfToken} })
			.then(res => handleResponse(res, 'Item excluído com sucesso!'))
			.catch(handleError);
	}
}

function saveNewItem() {
	const amount = document.getElementById('newItem-amount').value;
	const minimal = document.getElementById('newItem-minimal').value;
	document.getElementById('newItem-amount').value = normaliseComma(amount);
	document.getElementById('newItem-minimal').value = normaliseComma(minimal);
	
	submitModal('newItem-form', 'Item criado com sucesso!');
}

function updateItem() {
	const amount = document.getElementById('viewItem-amount').value;
	const minimal = document.getElementById('viewItem-minimal').value;
	document.getElementById('viewItem-amount').value = normaliseComma(amount);
	document.getElementById('viewItem-minimal').value = normaliseComma(minimal);
	
	const itemName = document.getElementById('viewItem-name').value;
	
	submitModal('viewItem-form', `Item "${itemName}" atualizado com sucesso`);
}

// === OPEN MODAL ===
function fillItemViewModal(data) {
	document.getElementById('viewItem-id').value = data.item_id;
	document.getElementById('viewItem-name').value = data.item_name;
	document.getElementById('viewItem-amount').value = data.item_qty;
	document.getElementById('viewItem-unit').value = data.item_unit;
	document.getElementById('viewItem-minimal').value = data.item_min;
	document.getElementById('viewItem-cost').value = data.item_cost;
}

function openNewItemModal() {
	document.getElementById('newItem-form').reset();
	document.getElementById('newItem-modal').style.display = "flex";
	toggleSaveStorageButton('new');
}

function openViewItemModal(id) {
	id = parseInt(id, 10);
	fetchJson(`/item_data/${id}`)
		.then(data => {
			originalItemValues = {
				item_id: data.item_id,
				item_name: data.item_name,
				item_qty: data.item_qty,
				item_unit: data.item_unit,
				item_min: data.item_min,
				item_cost: data.item_cost,
			}

			fillItemViewModal(data);
			resetViewItemModalState();
			document.getElementById('viewItem-modal').style.display = "flex";

			toggleSaveStorageButton('view');
		})
		.catch(handleError);
}

function openManageGroupsModal() {
	document.getElementById('mngGroup-groupSelect').value = "";
	document.getElementById('mngGroup-name').value = "";
	document.getElementById('mngGroup-itemQty').value = "";
	document.getElementById('mngGroup-deleteBtn').style.display = "none";

	groupItems = [];
	renderGroupItems();
	groupItemSelector.clear();

	document.getElementById('mngGroup-modal').style.display = "flex";
}

function openMissingItemModal() {
	fetchJson('/missing_items')
		.then(data => {
			document.getElementById('missItems-desc').value = data.missing_items || "";
			document.getElementById('missItem-modal').style.display = "flex";
		})
		.catch(err => {
			console.error("Failed to fetch missing items: ", err);
			showSnackbar('Não foi possível carregar os itens faltantes.', 'error');
		});		
}

async function openMoveModal(id) {
	document.getElementById('stockMovements-modal').dataset.id = id;
	
	resetNewMoveModalState()
	document.getElementById('stockMovements-modal').style.display = "flex";
	
	const content = document.getElementById('stockMovements-content');
	content.innerHTML = `
		<div class="dots">
			<div class="dot"></div>
			<div class="dot"></div>
			<div class="dot"></div>
		</div>
	`;
	
	let movements;
	try {
		movements = await fetchJson(`/item_movements/${id}`);
	}
	catch (err) {
		content.innerHTML = '';
		handleError(err);
		return;
	}

	if (movements.length === 0)
		content.innerHTML = '<p class="no-movements">Nenhuma movimentação registrada.</p>'
	else {
		content.innerHTML = `
			<div class="table-scroll">
				<table class="moves-table">
					<thead>
						<tr>
							<th>Tipo</th>
							<th>Qtd.</th>
							<th>Data</th>
							<th>Observação</th>
						</tr>
					</thead>
					<tbody></tbody>
				</table>
			</div>
		`;

		const tbody = content.querySelector('tbody');

		movements.forEach(move => {
			const row = document.createElement('tr');
			
			const type = document.createElement('td');
			type.textContent = move.type_value;

			const quantity = document.createElement('td');
			quantity.textContent = move.quantity;

			const date = document.createElement('td');
			date.textContent = move.date;

			const obs = document.createElement('td');
			obs.textContent = move.observation ?? '';
			obs.title = move.observation ?? '';

			row.append(type, quantity, date, obs);
			tbody.appendChild(row);
		})
	}
}

// === EDIT VIEW MODAL ===
function enableEditItem() {
	document.getElementById('viewItem-name').disabled = false;
	document.getElementById('viewItem-unit').disabled = false;
	document.getElementById('viewItem-minimal').disabled = false;
	document.getElementById('viewItem-cost').disabled = false;

	document.getElementById('viewItem-editBtn').style.display = 'none';
	document.getElementById('viewItem-saveBtn').style.display = 'inline-block';
	document.getElementById('viewItem-cancelBtn').style.display = 'inline-block';

	toggleSaveStorageButton('view');
}

function cancelEditItem() {
	fillItemViewModal(originalItemValues);
	resetViewItemModalState();
	toggleSaveStorageButton('view');
}

function enableAddMove() {
	document.getElementById('newMove-form').style.display = 'inline-block';
	document.getElementById('newMove-btn').style.display = 'none';
}

function cancelAddMove() {
	resetNewMoveModalState()
}

function resetViewItemModalState() {
	document.getElementById('viewItem-name').disabled = true;
	document.getElementById('viewItem-amount').disabled = true;
	document.getElementById('viewItem-unit').disabled = true;
	document.getElementById('viewItem-minimal').disabled = true;
	document.getElementById('viewItem-cost').disabled = true;

	document.getElementById('viewItem-editBtn').style.display = 'inline-block';
	document.getElementById('viewItem-saveBtn').style.display = 'none';
	document.getElementById('viewItem-cancelBtn').style.display = 'none';
}

function resetNewMoveModalState() {
	document.getElementById('newMove-type').value = "";
	document.getElementById('newMove-quantity').value = "";
	document.getElementById('newMove-obs').value = "";

	document.getElementById('newMove-form').style.display = 'none';
	document.getElementById('newMove-btn').style.display = 'inline-block';
	toggleSaveStorageButton('new', 'move');
}

// === GROUPS ===
document.getElementById('mngGroup-groupSelect').addEventListener('change', function() {
	const groupId = this.value;

	if (!groupId) {
		document.getElementById('mngGroup-name').value = "";
		document.getElementById('mngGroup-deleteBtn').style.display = 'none';
		groupItems = [];
		renderGroupItems();
		return;
	}

	fetchJson(`/group_data/${groupId}`)
		.then(data => {
			document.getElementById('mngGroup-name').value = data.group_name;
			document.getElementById('mngGroup-deleteBtn').style.display = 'inline-block';

			groupItems = data.items;
			renderGroupItems();
		})
		.catch(err => {
			console.error('Failed to load group data:', err);
			showSnackbar('Não foi possível carregar os dados do grupo.', 'error');
		});
});

function addItemToGroup() {
	const qtyInput = document.getElementById('mngGroup-itemQty');
	const itemId = groupItemSelector.getValue();
	const quantity = normaliseComma(qtyInput.value);

	if (!itemId) {
		showSnackbar('Selecione um item.', 'warning');
		return;
	}

	if (!quantity || quantity <= 0) {
		showSnackbar('Informe uma quantidade válida', 'warning');
		return;
	}

	const selectedItem = groupItemSelector.options[itemId];

	const existingItem = groupItems.find(existing => existing.item_id === parseInt(itemId));
	if (existingItem) {
		showSnackbar('Esse item já está no grupo.', 'error');
		return;
	}

	groupItems.push({
		item_id: parseInt(itemId),
		item_name: selectedItem.title,
		item_qty: quantity,
		unit: selectedItem.unit
	});

	renderGroupItems();
	groupItemSelector.clear();
	qtyInput.value = '';
}

function removeItemFromGroup(index) {
	groupItems.splice(index, 1);
	renderGroupItems();
}

function renderGroupItems() {
	const container = document.getElementById('mngGroup-itemList');
	container.innerHTML = '';

	groupItems.forEach((item, index) => {
		const row = document.createElement('div');
		row.className = 'basket-item-row';

		row.innerHTML = `
			<span class="basket-item-name"></span>
			<span class="basket-item-quantity"></span>
			<button type="button" class="btn-remove-item">&times;</button>
		`;

		row.querySelector('.basket-item-name').textContent = item.item_name;
		row.querySelector('.basket-item-quantity').textContent = `${item.item_qty} ${item.unit}`;
		row.querySelector('.btn-remove-item').onclick = () => removeItemFromGroup(index);

		container.appendChild(row);
	});
}

function saveGroup() {
	const groupId = document.getElementById('mngGroup-groupSelect').value;
	const groupName = document.getElementById('mngGroup-name').value.trim();

	if (!groupName) {
		showSnackbar('Informe um nome para o grupo.', 'warning');
		return;
	}

	if (groupItems.length < 2) {
		showSnackbar('Um grupo precisa de pelo menos 2 itens.', 'warning');
		return;
	}

	const formData = new FormData();
	if (groupId) formData.append('group_id', groupId);

	formData.append('group_name', groupName);
	formData.append('items', JSON.stringify(groupItems.map(i => [i.item_id, i.item_qty])));

	const csrfToken = document.querySelector('input[name="csrf_token"]').value;
	fetch('/save_group', {
		method: 'POST',
		headers: {'X-CSRFToken': csrfToken},
		body: formData
	})
	.then(res => handleResponse(res, 'Grupo salvo com sucesso!'))
	.catch(handleError);
}

async function deleteGroup() {
	const groupId = document.getElementById('mngGroup-groupSelect').value;
	if (!groupId) return;

	const confirmed = await openConfirm('Excluir grupo?', 'Tem certeza que deseja excluir este grupo?');
	
	if (confirmed) {
		const csrfToken = document.querySelector('input[name="csrf_token"]').value;	
		fetch(`/delete_group/${groupId}`, {method: 'POST', headers: {'X-CSRFToken': csrfToken}})
			.then(res => handleResponse(res, 'Grupo excluído com sucesso!'))
			.catch(handleError);
	}
}