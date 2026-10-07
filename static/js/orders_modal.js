let originalOrderValues = {};

let newOrderBaskets = [];
let viewOrderBaskets = [];

let newOrderDeliveryDetails = {
	"address_id": null,
	"address_txt": null,
	"delivery_fee": 0.00
}

let viewOrderDeliveryDetails = {
	"address_id": null,
	"address_txt": null,
	"delivery_fee": 0.00
}

let pendingOrderBasket = null;
let pendingOrderMode = null;
let pendingOrderIndex = null;

let defaultStatus = 'PENDING';

let newOrderPriceManuallySet = false;
let viewOrderPriceManuallySet = false;

const availableClients = JSON.parse(
	document.getElementById('newOrder-client').dataset.clients
);

const availableBaskets = JSON.parse(
	document.getElementById('newOrder-baskets').dataset.baskets
);

const availableStatuses = JSON.parse(
	document.getElementById('newOrder-status').dataset.status
);

const availableAddresses = JSON.parse(
	document.getElementById('newOrder-address').dataset.addresses
);
const NEW_ADDRESS_ID = "new";

const newOrderClientSelector = new TomSelect('#newOrder-client', {
	options: availableClients,
	valueField: 'id',
	labelField: 'name',
	searchField: 'name',
	create: false,
	maxItems: 1,
	sortField: [
		{
			field: 'name',
			direction: 'asc'
		}
	]
});

const newOrderBasketSelector = new TomSelect('#newOrder-baskets', {
	options: availableBaskets,
	valueField: 'id',
	labelField: 'name',
	searchField: 'name',
	create: false,
	maxItems: 1,
	sortField: [
		{
			field: 'name',
			direction: 'asc'
		}
	]
});

const newOrderStatusSelector = new TomSelect('#newOrder-status', {
	options: availableStatuses,
	valueField: 'id',
	labelField: 'title',
	searchField: 'title',
	create: false,
	maxItems: 1,
	sortField: [
		{
			field: 'title',
			direction: 'asc'
		}
	]
});

const newOrderAddressSelector = new TomSelect('#newOrder-address', {
	options: [],
	valueField: 'id',
	labelField: 'endereco',
	searchField: 'endereco',
	create: false,
	maxItems: 1,
	onChange: function(value) {
		const isNew = value === NEW_ADDRESS_ID;
		document.getElementById('newOrder-newAddressRow').style.display = isNew ? 'block' : 'none';
		document.getElementById('newOrder-address').value = isNew ? '' : value;
		if (isNew) document.getElementById('newOrder-newAddressText').value = '';
	}
});

function refreshAddressOptions(clientId, mode) {
	const addrSelector = mode === 'new'
		? newOrderAddressSelector
		: viewOrderAddressSelector
	
	addrSelector.clear(true);
	addrSelector.clearOptions();

	addrSelector.addOption({id: NEW_ADDRESS_ID, endereco: 'Novo Endereço'});

	availableAddresses
		.filter(addr => addr.id_cliente === parseInt(clientId, 10))
		.forEach(addr => addrSelector.addOption(addr));
}

let viewOrderClientSelector = null;
let viewOrderBasketSelector = null;
let viewOrderStatusSelector = null;
let viewOrderAddressSelector = null;
const viewOrderForm = document.getElementById('viewOrder-form');

if (viewOrderForm) {
	viewOrderClientSelector = new TomSelect('#viewOrder-client', {
		options: availableClients,
		valueField: 'id',
		labelField: 'name',
		searchField: 'name',
		create: false,
		maxItems: 1,
		sortField: [
			{
				field: 'name',
				direction: 'asc'
			}
		]
	});

	viewOrderBasketSelector = new TomSelect('#viewOrder-baskets', {
		options: availableBaskets,
		valueField: 'id',
		labelField: 'name',
		searchField: 'name',
		create: false,
		maxItems: 1,
		sortField: [
			{
				field: 'name',
				direction: 'asc'
			}
		]
	});

	viewOrderStatusSelector = new TomSelect('#viewOrder-status', {
		options: availableStatuses,
		valueField: 'id',
		labelField: 'title',
		searchField: 'title',
		create: false,
		maxItems: 1,
		sortField: [
			{
				field: 'title',
				direction: 'asc'
			}
		]
	});

	viewOrderAddressSelector = new TomSelect('#viewOrder-address', {
		options: [],
		valueField: 'id',
		labelField: 'endereco',
		searchField: 'endereco',
		create: false,
		maxItems: 1,
		onChange: function(value) {
			const isNew = value === NEW_ADDRESS_ID;
			document.getElementById('viewOrder-newAddressRow').style.display = isNew ? 'block' : 'none';
			document.getElementById('viewOrder-address').value = isNew ? '' : value;
			if (isNew) document.getElementById('viewOrder-newAddressText').value = '';
		}
	});

	viewOrderClientSelector.disable();
	viewOrderBasketSelector.disable();
	viewOrderStatusSelector.disable();

	document.getElementById('viewOrder-orderPrice').addEventListener('input', (e) => {
		viewOrderPriceManuallySet = e.target.value.trim() !== '';
		if (!viewOrderPriceManuallySet)
			updateSuggestedTotal('view');
	});
}

document.getElementById('newOrder-orderPrice').addEventListener('input', (e) => {
	newOrderPriceManuallySet = e.target.value.trim() !== '';
	if (!newOrderPriceManuallySet)
		updateSuggestedTotal('new');
});

function saveButton(mode) {
	mode === 'new'
		? toggleSaveButton(
			['newOrder-client', 'newOrder-orderPrice', 'newOrder-date'],
			'newOrder-saveBtn',
			[newOrderBaskets]
		)
		: toggleSaveButton(
			['viewOrder-client', 'viewOrder-orderPrice', 'viewOrder-date'],
			'viewOrder-saveBtn',
			[viewOrderBaskets]
		)
}

function openNewOrderModal() {
	document.getElementById('newOrder-form').reset();
	toggleDeliveryModal(document.getElementById('newOrder-isDelivery'), 'new');

	newOrderClientSelector.clear();
	newOrderBasketSelector.clear();
	newOrderStatusSelector.setValue(defaultStatus);
	newOrderStatusSelector.disable();

	document.getElementById('newOrder-newAddressText').value = '';
	document.getElementById('newOrder-deliveryFee').value = '';

	newOrderBaskets = [];
	newOrderPriceManuallySet = false;
	saveButton('new');
	toggleSwitch('newOrder-client', 'newOrder-isDelivery');
	renderOrderBaskets('new');
	document.getElementById('newOrder-modal').style.display = "flex";
}

function openViewOrderModal(id) {
	id = parseInt(id, 10);
	fetch(`/pedidos/${id}/data`)
		.then(res => res.json())
		.then(data => {
			document.getElementById('viewOrder-id').value = data.id_pedido;
			viewOrderClientSelector.setValue(data.id_cliente);
			
			const allowedStatuses = [...data.allowed_status];
			viewOrderStatusSelector.clear(true);
			viewOrderStatusSelector.clearOptions();
			availableStatuses
				.filter(status => allowedStatuses.includes(status.id))
				.forEach(status => {viewOrderStatusSelector.addOption(status)});
			viewOrderStatusSelector.setValue(data.status_pedido);
			
			document.getElementById('viewOrder-date').value = data.data_pedido;
			document.getElementById('viewOrder-deliveryDate').value = data.data_entrega;
			document.getElementById('viewOrder-obs').value = data.observacao;
			document.getElementById('viewOrder-orderPrice').value = data.valor_pedido;

			viewOrderBaskets = data.itens_pedido || [];
			viewOrderPriceManuallySet = false;

			originalOrderValues = {
				id_cliente: data.id_cliente,
				status_pedido: data.status_pedido,
				data_pedido: data.data_pedido,
				data_entrega: data.data_entrega,
				observacao: data.observacao,
				valor_pedido: data.valor_pedido,
				itens_pedido: structuredClone(viewOrderBaskets)
			};

			const openOrder = data.status_pedido !== "DELIVERED" && data.status_pedido !== "CANCELLED"

			if (!openOrder)
				document.getElementById('viewOrder-modalActions').style.display = 'none'
			

			resetViewOrderModalState();
			renderOrderBaskets('view');

			document.getElementById('viewOrder-modal').style.display = "flex";
			saveButton('view');
		});
}

function saveNewOrder() {
	document.getElementById('newOrder-items').value = JSON.stringify(serialiseOrderBaskets('new'));
	document.getElementById('newOrder-deliveryDetails').value = JSON.stringify(newOrderDeliveryDetails);

	submitModal('newOrder-form');
}

function updateOrder() {
	document.getElementById('viewOrder-items').value = JSON.stringify(serialiseOrderBaskets('view'));
	
	submitModal('viewOrder-form');
}

function openBasketComposition(mode, index, editable) {
	const baskets = mode === 'new'
		? newOrderBaskets
		: viewOrderBaskets;

	const basket = baskets[index];

	if (!basket || basket.groups.length === 0)
		return;

	pendingOrderBasket = structuredClone(basket);
	pendingOrderMode = mode;
	pendingOrderIndex = index;

	renderOrderBasketChoices(editable);

	document.getElementById('basketComposition-modal').style.display = 'flex';
	document.getElementById('basketComposition-list').scrollTop = 0;
	
	if (mode === 'view' && !editable)
		document.getElementById('basketComposition-btn').style.display = 'none';
	if (mode === 'view' && editable) {
		document.getElementById('basketComposition-btn').style.display = 'inline-block';
		document.getElementById('basketComposition-btn').textContent = 'Salvar';
	}
	if (mode === 'new') {
		document.getElementById('basketComposition-btn').style.display = 'inline-block';
		document.getElementById('basketComposition-btn').textContent = 'Adicionar';
	}
}

function enableEditOrder() {
	const status = viewOrderStatusSelector.getValue();
	
	const openOrder = status !== "DELIVERED" && status !== "CANCELLED"

	if (openOrder){
		document.getElementById('viewOrder-deliveryDate').disabled = false;
		viewOrderStatusSelector.enable();
	}
		
	if (status === "PENDING"){
		viewOrderClientSelector.enable();
		document.getElementById('viewOrder-date').disabled = false;
		document.getElementById('viewOrder-orderPrice').disabled = false;
		document.getElementById('viewOrder-obs').disabled = false;

		document.getElementById('viewOrder-addBasketRow').style.display = 'flex';
		document.getElementById('viewOrder-addBasketLbl').style.display = 'flex';
		viewOrderBasketSelector.enable()
		document.getElementById('viewOrder-basketQty').disabled = false;
	}

	document.getElementById('viewOrder-editBtn').style.display = 'none';
	document.getElementById('viewOrder-saveBtn').style.display = 'inline-block';
	document.getElementById('viewOrder-cancelBtn').style.display = 'inline-block';

	renderOrderBaskets('view');

	saveButton('view');
}

function cancelEditOrder() {
	viewOrderClientSelector.setValue(originalOrderValues.id_cliente);
	viewOrderStatusSelector.setValue(originalOrderValues.status_pedido);
	document.getElementById('viewOrder-date').value = originalOrderValues.data_pedido;
	document.getElementById('viewOrder-deliveryDate').value = originalOrderValues.data_entrega;
	document.getElementById('viewOrder-obs').value = originalOrderValues.observacao;
	document.getElementById('viewOrder-orderPrice').value = originalOrderValues.valor_pedido;

	viewOrderBaskets = structuredClone(originalOrderValues.itens_pedido);
	renderOrderBaskets('view');
	viewOrderBasketSelector.clear();
	document.getElementById('viewOrder-basketQty').value = '';

	resetViewOrderModalState();
}

function resetViewOrderModalState() {
	viewOrderClientSelector.disable();
	document.getElementById('viewOrder-date').disabled = true;
	document.getElementById('viewOrder-deliveryDate').disabled = true;
	document.getElementById('viewOrder-orderPrice').disabled = true;
	viewOrderStatusSelector.disable();
	document.getElementById('viewOrder-obs').disabled = true;

	document.getElementById('viewOrder-addBasketRow').style.display = 'none';
	document.getElementById('viewOrder-addBasketLbl').style.display = 'none';
	viewOrderBasketSelector.disable()
	document.getElementById('viewOrder-basketQty').disabled = true;
	
	document.getElementById('viewOrder-editBtn').style.display = 'inline-block';
	document.getElementById('viewOrder-saveBtn').style.display = 'none';
	document.getElementById('viewOrder-cancelBtn').style.display = 'none';

	renderOrderBaskets('view');
}

function updateOrderDeliveryDate(mode) {
	const order_date_id = mode === 'new'
		? "newOrder-date" : "viewOrder-date";

	const delivery_date_id = mode === 'new'
		? "newOrder-deliveryDate" : "viewOrder-deliveryDate";

	const orderDate = document.getElementById(order_date_id);
	const deliveryDate = document.getElementById(delivery_date_id);

	deliveryDate.min = orderDate.value;

	if (deliveryDate.value && deliveryDate.value < orderDate.value)
		deliveryDate.value = "";

}

async function addBasketToOrder(mode) {
	const qtyInput = document.getElementById(`${mode}Order-basketQty`);

	const selector = mode === 'new'
		? newOrderBasketSelector
		: viewOrderBasketSelector;

	const basketId = selector.getValue();
	const quantity = parseInt(qtyInput.value);

	if (!basketId) {
		alert('Selecione uma cesta.');
		return;
	}

	if (!quantity || quantity <= 0) {
		alert('Informe uma quantidade válida');
		return;
	}

	const selectedBasket = selector.options[basketId];

	const baskets = mode === 'new'
		? newOrderBaskets
		: viewOrderBaskets;

	const existingBasket = baskets.find(
		existing => existing.basket_id === Number(selectedBasket.id)
	);

	if (existingBasket) {
		alert('Essa cesta já foi adicionada ao pedido.');
		return;
	}

	const composition = await fetch(`/pedidos/basket_comp/${selectedBasket.id}`)
		.then(res => res.json());

	const basket = {
		basket_id: Number(selectedBasket.id),
		basket_name: selectedBasket.name,
		basket_price: selectedBasket.price,
		quantity: quantity,
		groups: composition.groups.map(g => ({
			group_id: g.group_id,
			group_name: g.group_name,
			quantity: g.quantity,
			options: g.options,
			selected: Array.from({length: quantity}, () => 
				Array.from({length: g.quantity}, () =>
					g.options.length ? g.options[0].item_id : null
				)
			)
		}))
	};

	if (basket.groups.length > 0) {
		pendingOrderBasket = basket;
		pendingOrderMode = mode;
		pendingOrderIndex = null;

		renderOrderBasketChoices(true);
		document.getElementById('basketComposition-modal').style.display = 'flex';
		document.getElementById('basketComposition-list').scrollTop = 0;

		return;
	}

	baskets.unshift(basket);

	renderOrderBaskets(mode);
	updateSuggestedTotal(mode);

	saveButton(mode);

	selector.clear();
	qtyInput.value = '';
}

function removeBasketFromOrder(mode, index) {
	const items = mode === 'new'
		? newOrderBaskets
		: viewOrderBaskets;

	items.splice(index, 1);

	renderOrderBaskets(mode);
	updateSuggestedTotal(mode);
}

function renderOrderBaskets(mode) {
	const container = document.getElementById(`${mode}Order-basketList`);
	
	const baskets = mode === 'new'
		? newOrderBaskets
		: viewOrderBaskets;
	
	const isEditable = mode === 'new'
		|| !document.getElementById('viewOrder-basketQty').disabled;
	
	container.innerHTML = '';
		
	baskets.forEach((basket, index) => {
		const row = document.createElement('div');
		row.className = 'order-items-row';

		const hasGroups = basket.groups.length > 0;
		
		row.innerHTML = `
			<span class="order-items-name"></span>

			<span class="order-items-quantity"></span>

			<div class="order-items-actions">
				${hasGroups ? `
				<button
					type="button"
					class="btn-view-composition"
				>
					${mode === 'view'
						? (isEditable ? ICON_PENCIL : ICON_EYE)
						: ''
					}
				</button>
				`: ''}
				
				${isEditable ? `
				<button
					type="button"
					class="btn-remove-item"
				>
					&times;
				</button>
				` : ''}
			</div>
		`;

		row.querySelector('.order-items-name').textContent = basket.basket_name;
		row.querySelector('.order-items-quantity').textContent = `${basket.quantity} un`;

		if (hasGroups) {
			row.querySelector('.btn-view-composition').onclick = () => openBasketComposition(mode, index, isEditable);
		}

		if (isEditable) {
			row.querySelector('.btn-remove-item').onclick = () => removeBasketFromOrder(mode, index);
		}

		container.appendChild(row);
	});
}

function serialiseOrderBaskets(mode) {
	const baskets = mode === 'new'
		? newOrderBaskets
		: viewOrderBaskets;

	return baskets.map(basket => ({
		basket_id: basket.basket_id,
		quantity: basket.quantity,
		choices: basket.groups.map(g => ({
			group_id: g.group_id,
			item_id: g.selected.flat()
		}))
	}));
}

function renderOrderBasketChoices(editable) {
	const list = document.getElementById('basketComposition-list');

	list.innerHTML = '';

	for (let unitIndex = 0; unitIndex < pendingOrderBasket.quantity; unitIndex++) {
		const unit = document.createElement('div');
		unit.className = 'order-composition-unit';

		if (pendingOrderBasket.quantity > 1) {
			const title = document.createElement('h4')
			title.className = 'order-composition-unit-title';
			title.textContent = `${pendingOrderBasket.basket_name} #${unitIndex + 1}`;
			unit.appendChild(title);
		}

		pendingOrderBasket.groups.forEach((group, groupIndex) => {
			const groupDiv = document.createElement('div');
			groupDiv.className = 'order-composition-group';

			const label = document.createElement('label');
			label.textContent = `${group.group_name}: `;

			groupDiv.appendChild(label);

			group.selected[unitIndex].forEach((selectedId, slotIndex) => {
				if (!editable) {
					const chosen = group.options.find(
						o => o.item_id === selectedId
					);

					const selected = document.createElement('span');
					selected.className = 'order-composition-readonly';
					selected.textContent = chosen ? chosen.item_name : '---';
					
					groupDiv.appendChild(selected);
					
					return;
				}

				const select = document.createElement('select');
				select.className = 'order-composition-choice';

				select.onchange = function () {
					updateOrderBasketChoice(
						groupIndex, unitIndex, slotIndex, this.value
					);
				};

				group.options.forEach(option => {
					const optionElement = document.createElement('option');

					optionElement.value = option.item_id;
					optionElement.textContent = option.item_name;
					optionElement.selected = option.item_id === selectedId;

					select.appendChild(optionElement);
				});

				groupDiv.appendChild(select);
			});

			unit.appendChild(groupDiv);
		});

		list.appendChild(unit);
	}
}

function updateOrderBasketChoice(groupIndex, unitIndex, slotIndex, value) {
	pendingOrderBasket.groups[groupIndex].selected[unitIndex][slotIndex] = parseInt(value);
}

function confirmOrderBasket() {
	if (!pendingOrderBasket)
		return;

	const baskets = pendingOrderMode === 'new'
		? newOrderBaskets
		: viewOrderBaskets

	if (pendingOrderIndex !== null)
		baskets[pendingOrderIndex] = pendingOrderBasket;
	else
		baskets.unshift(pendingOrderBasket);

	renderOrderBaskets(pendingOrderMode);
	updateSuggestedTotal(pendingOrderMode);

	saveButton(pendingOrderMode);

	if (pendingOrderIndex === null) {
		const selector = pendingOrderMode === 'new'
			? newOrderBasketSelector
			: viewOrderBasketSelector;

		const qtyInput = document.getElementById(`${pendingOrderMode}Order-basketQty`);
		selector.clear();
		qtyInput.value = '';
	}

	pendingOrderBasket = null;
	pendingOrderMode = null;
	pendingOrderIndex = null;

	closeModal('basketComposition-modal');
}

function updateSuggestedTotal(mode) {
	if (mode === 'new' && newOrderPriceManuallySet)
		return;
	if (mode === 'view' && viewOrderPriceManuallySet)
		return;

	const baskets = mode === 'new'
		? newOrderBaskets
		: viewOrderBaskets;

	const suggested = baskets.reduce(
		(sum, b) => sum + (b.basket_price * b.quantity), 0
	)

	const input = document.getElementById(`${mode}Order-orderPrice`);
	input.value = suggested > 0 ? suggested.toFixed(2) : '';
}

function updateOrderTotal(mode) {
	const totalLabel = document.getElementById(`${mode}Order-totalPrice`);
	const deliveryFee = parseFloat(document.getElementById(`${mode}Order-deliveryFee`).value) || 0;
	const orderPrice = parseFloat(document.getElementById(`${mode}Order-orderPrice`).value) || 0;

	totalLabel.value = (deliveryFee + orderPrice).toFixed(2);
}

function cancelBasketComposition() {
	pendingOrderBasket = null;
	pendingOrderIndex = null;
	pendingOrderMode = null;
	closeModal('basketComposition-modal');
}

function cancelDeliveryDetails(mode) {
	const checkbox_id = mode === 'new'
		? 'newOrder-isDelivery'
		: 'viewOrder-isDelivery';

	const checkbox = document.getElementById(checkbox_id);
	checkbox.checked = false;
	toggleDeliveryModal(checkbox, mode)
}

function toggleDeliveryModal(checkbox, mode) {
	const delivery = checkbox.checked;
	const clients = document.getElementById(`${mode}Order-client`)
	const editButton = document.getElementById(`${mode}Order-editDetailsBtn`);
	const label = document.getElementById(checkbox.id + 'Label');

	if (label)
		label.textContent = delivery ? 'Entrega' : 'Retirada';
	
	if (delivery) {
		refreshAddressOptions(clients.value, mode);
		updateOrderTotal(mode);
		// document.getElementById('deliveryOrder-modal').style.display = 'flex';
		editButton.parentElement.style.display = '';
	}
	else {
		document.getElementById('deliveryOrder-modal').style.display = 'none';
		editButton.parentElement.style.display = 'none';
	}
}

function openEditDetailsModal(mode) {
	document.getElementById('deliveryOrder-modal').style.display = 'flex';
}

function toggleSwitch(clientSelector, deliverySwitch) {
	const orderSwitch = document.getElementById(deliverySwitch);
	const client = document.getElementById(clientSelector);
	const slider = orderSwitch.nextElementSibling;

	const allow = client.value.trim() !== '';

	orderSwitch.disabled = !allow;
	slider.title = allow ? "" : "Selecione um cliente";
}

function confirmDeliveryDetails(mode) {
	const selector = mode === 'new'
		? newOrderAddressSelector
		: viewOrderAddressSelector;

	const details = mode === 'new'
		? newOrderDeliveryDetails
		: viewOrderDeliveryDetails;

	const newAddressText = document.getElementById(`${mode}Order-newAddressText`);
	const deliveryFee = document.getElementById(`${mode}Order-deliveryFee`);
	

	if (selector.getValue() === NEW_ADDRESS_ID) {
		details["address_id"] = null;
		details["address_txt"] = newAddressText.value;
	}

	else {
		details["address_id"] = selector.getValue();
		details["address_txt"] = null;
	}

	details['delivery_fee'] = deliveryFee.value.trim() || "0";
	closeModal('deliveryOrder-modal');
}