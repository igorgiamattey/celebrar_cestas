let originalItemsValues = {};
let groupItems = []

const outMove = "SAIDA"
const inMove = "ENTRADA"

const availableItems = JSON.parse(
	document.getElementById('mngGroup-itemSelect').dataset.items
);

const groupItemSelector = new TomSelect('#mngGroup-itemSelect', {
	options: availableItems,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	sortField: {field: 'title', direction: 'asc'}
});

function openNewItemModal() {
	document.getElementById('newItem-form').reset();
	document.getElementById('newItem-modal').style.display = "flex";
	toggleSaveButton(['newItem-name','newItem-amount','newItem-unit','newItem-minimal','newItem-cost'], 'newItem-saveBtn');
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

	toggleSaveButton(['newItem-name','newItem-amount','newItem-unit','newItem-minimal','newItem-cost'], 'newItem-saveBtn');
}

document.getElementById('mngGroup-groupSelect').addEventListener('change', function() {
	const groupId = this.value;

	if (!groupId) {
		document.getElementById('mngGroup-name').value = "";
		document.getElementById('mngGroup-deleteBtn').style.display = 'none';
		groupItems = [];
		renderGroupItems();
		return;
	}

	fetch(`/estoque/grupos/${groupId}/data`)
		.then(res => res.json())
		.then(data => {
			document.getElementById('mngGroup-name').value = data.group_name;
			document.getElementById('mngGroup-deleteBtn').style.display = 'inline-block';

			groupItems = data.items;
			renderGroupItems();
		})
		.catch(err => console.error('Failed to load group data:', err));
});

function openMissingItemModal() {
	fetch('/estoque/falta')
		.then(res => res.json())
		.then(data => {
			document.getElementById('missItems-desc').value = data.missing_items || "";
			document.getElementById('missItem-modal').style.display = "flex";
		})
		.catch(err => {
			console.error("Failed to fetch missing items: ", err)
		});		
}

function openViewItemModal(id) {
	id = parseInt(id, 10);
	fetch(`/estoque/${id}/data`)
		.then(res => res.json())
		.then(data => {
			document.getElementById('viewItem-id').value = data.id_insumo;
			document.getElementById('viewItem-name').value = data.nome_insumo;
			document.getElementById('viewItem-amount').value = data.qtd_estoque;
			document.getElementById('viewItem-unit').value = data.unidade_medida;
			document.getElementById('viewItem-minimal').value = data.estoque_minimo;
			document.getElementById('viewItem-cost').value = data.custo_unitario;

			originalItemsValues = {
				nome_insumo: data.nome_insumo,
				qtd_estoque: data.qtd_estoque,
				unidade_medida: data.unidade_medida,
				estoque_minimo: data.estoque_minimo,
				custo_unitario: data.custo_unitario,
			}

			resetViewItemModalState();
			document.getElementById('viewItem-modal').style.display = "flex";
			toggleSaveButton(['viewItem-name','viewItem-amount','viewItem-unit','viewItem-minimal','viewItem-cost'], 'viewItem-saveBtn');
		});
}

async function openMoveModal(id) {
	document.getElementById('stockMovements-modal').dataset.id = id;
	
	resetNewMoveModalState()
	toggleSaveButton(['newMove-type','newMove-quantity'], 'newMove-saveBtn')
	document.getElementById('stockMovements-modal').style.display = "flex";
	
	const content = document.getElementById('stockMovements-content');
	content.innerHTML = `
		<div class="dots">
			<div class="dot"></div>
			<div class="dot"></div>
			<div class="dot"></div>
		</div>
	`;
	const response = await fetch(`/estoque/${id}/movimentacoes`);

	if (!response.ok)
		return;

	const movements = await response.json();

	if (movements.length === 0)
		content.innerHTML = '<p class="no-movements">Nenhuma movimentação registrada.</p>'
	else {
		content.innerHTML = `
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

function enableEditItem() {
	document.getElementById('viewItem-name').disabled = false;
	document.getElementById('viewItem-unit').disabled = false;
	document.getElementById('viewItem-minimal').disabled = false;
	document.getElementById('viewItem-cost').disabled = false;

	document.getElementById('viewItem-editBtn').style.display = 'none';
	document.getElementById('viewItem-saveBtn').style.display = 'inline-block';
	document.getElementById('viewItem-cancelBtn').style.display = 'inline-block';

	toggleSaveButton(['viewItem-name','viewItem-amount','viewItem-unit','viewItem-minimal','viewItem-cost'], 'viewItem-saveBtn');
}

function cancelEditItem() {
	document.getElementById('viewItem-name').value = originalItemsValues.nome_insumo;
	document.getElementById('viewItem-amount').value = originalItemsValues.qtd_estoque;
	document.getElementById('viewItem-unit').value = originalItemsValues.unidade_medida;
	document.getElementById('viewItem-minimal').value = originalItemsValues.estoque_minimo;
	document.getElementById('viewItem-cost').value = originalItemsValues.custo_unitario;

	resetViewItemModalState();
}

function enableAddMove() {
	document.getElementById('newMove-form').style.display = 'inline-block';
	document.getElementById('newMove-btn').style.display = 'none';
}

function cancelAddMove() {
	resetNewMoveModalState()
}

async function saveMove() {
	const id = document.getElementById('stockMovements-modal').dataset.id;

	move_type = document.getElementById('newMove-type').value;
	move_qty = document.getElementById('newMove-quantity').value;
	move_obs = document.getElementById('newMove-obs').value;

	const response = await fetch(`/estoque/${id}/nova_movimentacao`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json'
		},
		body: JSON.stringify({
			type: move_type,
			quantity: move_qty,
			obs: move_obs
		})
	});

	const data = await response.json();

	if (!response.ok) {
		alert(data.error);
		return;
	}

	window.location.reload()

}

function deleteItem() {
	const id = document.getElementById('viewItem-id').value;
	if (confirm('Tem certeza que deseja excluir este item?')) {
		fetch(`/estoque/${id}/delete`, { method: 'POST' })
			.then(handleResponse)
			.catch(handleError);
	}
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
}

function toggleMissingButton() {
	fetch('/estoque/falta')
		.then(res => res.json())
		.then(data => {
			list = data.missing_items;
			button = document.getElementById('missItem-btn');
			button.disabled = list.length === 0;
			button.title = (list.length === 0) ? "Nenhum item está faltando ou próximo de acabar" : "";
		})
		.catch(err => {
			console.error("Failed to fetch missing items: ", err)
		});		
}

function addItemToGroup() {
	const qtyInput = document.getElementById('mngGroup-itemQty');
	const itemId = groupItemSelector.getValue();
	const quantity = parseFloat(qtyInput.value);

	if (!itemId) {
		alert('Selecione um item.');
		return;
	}

	if (!quantity || quantity <= 0) {
		alert('Informe uma quantidade válida');
		return;
	}

	const selectedItem = groupItemSelector.options[itemId];

	const existingItem = groupItems.find(existing => existing.item_id === parseInt(itemId));
	if (existingItem) {
		alert('Esse item já está no grupo.');
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
		alert('Informe um nome para o grupo.');
		return;
	}

	if (groupItems.length < 2) {
		alert('Um grupo precisa de pelo menos 2 itens.');
		return;
	}

	const formData = new FormData();
	if (groupId) formData.append('group_id', groupId);

	formData.append('group_name', groupName);
	formData.append('items', JSON.stringify(groupItems.map(i => [i.item_id, i.item_qty])));

	fetch('/estoque/grupos/save', {
		method: 'POST',
		body: formData
	})
	.then(handleResponse)
	.catch(handleError);
}

function deleteGroup() {
	const groupId = document.getElementById('mngGroup-groupSelect').value;
	if (!groupId) return;
	
	if (confirm('Tem certeza que deseja excluir este grupo?')) {
		fetch(`/estoque/grupos/${groupId}/delete`, {method: 'POST'})
			.then(handleResponse)
			.catch(handleError);
	}
}