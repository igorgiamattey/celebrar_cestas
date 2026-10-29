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

let defaultOrderStatus = 'PENDING';

let newOrderPriceManuallySet = false;
let viewOrderPriceManuallySet = false;

const availableClients = JSON.parse(
	document.getElementById('newOrder-client').dataset.clients
);

const availableBaskets = JSON.parse(
	document.getElementById('newOrder-baskets').dataset.baskets
);

const availableOrderStatuses = JSON.parse(
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
	maxOptions: null,
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
	maxOptions: null,
	sortField: [
		{
			field: 'name',
			direction: 'asc'
		}
	]
});

const newOrderStatusSelector = new TomSelect('#newOrder-status', {
	options: availableOrderStatuses,
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

const newOrderAddressSelector = new TomSelect('#newOrder-address', {
	options: [],
	valueField: 'id',
	labelField: 'address_txt',
	searchField: 'address_txt',
	create: false,
	maxItems: 1,
	maxOptions: null,
	onChange: function(value) {
		const isNew = value === NEW_ADDRESS_ID;
		const addressTxt = document.getElementById('newOrder-newAddressText');

		if (isNew)
			addressTxt.value = '';
		else {
			const address = availableAddresses.find(
				addr => String(addr.id) === String(value)
			);
			addressTxt.value = address ? address.address_txt : '';
		}
	}
});

function refreshAddressOptions(clientId, mode) {
	const addrSelector = mode === 'new'
		? newOrderAddressSelector
		: viewOrderAddressSelector
	
	addrSelector.clear(true);
	addrSelector.clearOptions();

	addrSelector.addOption({id: NEW_ADDRESS_ID, address_txt: 'Novo Endereço'});

	availableAddresses
		.filter(addr => addr.client_id === parseInt(clientId, 10))
		.forEach(addr => addrSelector.addOption(addr));
}

let viewOrderClientSelector = null;
let viewOrderBasketSelector = null;
let viewOrderStatusSelector = null;
let viewOrderAddressSelector = null;
const viewOrderForm = document.getElementById('viewOrder-form');

document.querySelector('#newOrder-isDelivery ~ .switch-slider .switch-icon--off').innerHTML = ICON_TAKE;
document.querySelector('#newOrder-isDelivery ~ .switch-slider .switch-icon--on').innerHTML = ICON_DELIVERY;

if (viewOrderForm) {
	document.querySelector('#viewOrder-isDelivery ~ .switch-slider .switch-icon--off').innerHTML = ICON_TAKE;
	document.querySelector('#viewOrder-isDelivery ~ .switch-slider .switch-icon--on').innerHTML = ICON_DELIVERY;
	
	viewOrderClientSelector = new TomSelect('#viewOrder-client', {
		options: availableClients,
		valueField: 'id',
		labelField: 'name',
		searchField: 'name',
		create: false,
		maxItems: 1,
		maxOptions: null,
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
		maxOptions: null,
		sortField: [
			{
				field: 'name',
				direction: 'asc'
			}
		]
	});

	viewOrderStatusSelector = new TomSelect('#viewOrder-status', {
		options: availableOrderStatuses,
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

	viewOrderAddressSelector = new TomSelect('#viewOrder-address', {
		options: [],
		valueField: 'id',
		labelField: 'address_txt',
		searchField: 'address_txt',
		create: false,
		maxItems: 1,
		maxOptions: null,
		onChange: function(value) {
			const isNew = value === NEW_ADDRESS_ID;
			const addressTxt = document.getElementById('viewOrder-newAddressText');

			if (isNew)
				addressTxt.value = '';
			else {
				const address = availableAddresses.find(
					addr => String(addr.id) === String(value)
				);
				addressTxt.value = address ? address.address_txt : '';
			}
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

	newOrderClientSelector.clear();
	newOrderBasketSelector.clear();
	newOrderStatusSelector.setValue(defaultOrderStatus);
	newOrderStatusSelector.disable();

	document.getElementById('newOrder-newAddressText').value = '';
	document.getElementById('newOrder-deliveryFee').value = '';

	newOrderDeliveryDetails = {
		address_id: null,
		address_txt: null,
		delivery_fee: 0.00
	};

	newOrderAddressSelector.clear(true);

	newOrderBaskets = [];
	newOrderPriceManuallySet = false;

	toggleSwitch('newOrder-client', 'newOrder-isDelivery');
	getDeliveryState(document.getElementById('newOrder-isDelivery'), 'new');
	updateOrderTotal('new');
	saveButton('new');
	renderOrderBaskets('new');
	document.getElementById('newOrder-modal').style.display = "flex";
}

function openViewOrderModal(id) {
	id = parseInt(id, 10);
	fetchJson(`/order_data/${id}`)
		.then(data => {
			document.getElementById('viewOrder-id').value = data.order_id;
			viewOrderClientSelector.setValue(data.client_id);
			
			const allowedStatuses = [...data.allowed_status];
			viewOrderStatusSelector.clear(true);
			viewOrderStatusSelector.clearOptions();
			availableOrderStatuses
				.filter(status => allowedStatuses.includes(status.id))
				.forEach(status => {viewOrderStatusSelector.addOption(status)});
			viewOrderStatusSelector.setValue(data.order_status);
			
			document.getElementById('viewOrder-date').value = data.order_date;
			document.getElementById('viewOrder-deliveryDate').value = data.delivery_date;
			document.getElementById('viewOrder-obs').value = data.obs;
			document.getElementById('viewOrder-orderPrice').value = data.order_subtotal;

			document.getElementById('viewOrder-deliveryFee').value = data.delivery_fee;

			const isDeliveryElement = document.getElementById('viewOrder-isDelivery');
			isDeliveryElement.checked = Boolean(data.isDelivery);
			getDeliveryState(isDeliveryElement, 'view')
			updateOrderTotal('view');

			const savedAddr = availableAddresses.find(
				addr => String(addr.id) === String(data.address_id)
			);
			
			if (data.isDelivery && data.address_id != null){
				viewOrderAddressSelector.setValue(data.address_id);
				document.getElementById('viewOrder-newAddressText').value = savedAddr ? savedAddr.address_txt : '';
			}

			viewOrderDeliveryDetails = {
				address_id: data.address_id,
				address_txt: savedAddr ? savedAddr.address_txt : null,
				delivery_fee: data.delivery_fee
			};

			viewOrderBaskets = data.order_items || [];
			viewOrderPriceManuallySet = false;

			originalOrderValues = {
				client_id: data.client_id,
				order_status: data.order_status,
				order_date: data.order_date,
				delivery_date: data.delivery_date,
				obs: data.obs,
				order_subtotal: data.order_subtotal,
				isDelivery: Boolean(data.isDelivery),
				address_id: data.address_id,
				delivery_id: data.delivery_id,
				delivery_fee: data.delivery_fee,
				order_items: structuredClone(order_itemsiewOrderBaskets)
			};

			resetViewOrderModalState();
			renderOrderBaskets('view');

			document.getElementById('viewOrder-modal').style.display = "flex";
			saveButton('view');
		})
		.catch(handleError);
}

function saveNewOrder() {
	document.getElementById('newOrder-items').value = JSON.stringify(serialiseOrderBaskets('new'));
	document.getElementById('newOrder-deliveryDetails').value = JSON.stringify(newOrderDeliveryDetails);

	submitModal('newOrder-form', 'Pedido criado com sucesso!');
}

async function updateOrder() {
	if (originalOrderValues.delivery_id != null) {
		const newDate = document.getElementById('viewOrder-deliveryDate').value;
		const dateChanged = newDate !== (originalOrderValues.delivery_date ?? '');
		const noLongerDelivery = !document.getElementById('viewOrder-isDelivery').checked;

		const confirmed = await openConfirm('Alterar pedido?',
			`Este pedido faz parte da entrega #${originalOrderValues.delivery_id}. ` +
			`Alterar a data ou mudar a forma de entrega vai removê-lo. Continuar?`);

		if ((dateChanged || noLongerDelivery) && !confirmed)
			return;
	}

	document.getElementById('viewOrder-items').value = JSON.stringify(serialiseOrderBaskets('view'));
	document.getElementById('viewOrder-deliveryDetails').value = JSON.stringify(viewOrderDeliveryDetails);
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
	if (status === "DELIVERED" || status === "CANCELLED")
		return;
	const isDeliveryElement = document.getElementById('viewOrder-isDelivery');
	
	document.getElementById('viewOrder-deliveryDate').disabled = false;
	viewOrderStatusSelector.enable();

	isDeliveryElement.disabled = false;
	updateDetailsBtnIcon();
	
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
	viewOrderClientSelector.setValue(originalOrderValues.client_id);
	viewOrderStatusSelector.setValue(originalOrderValues.order_status);
	document.getElementById('viewOrder-date').value = originalOrderValues.order_date;
	document.getElementById('viewOrder-deliveryDate').value = originalOrderValues.delivery_date;
	document.getElementById('viewOrder-obs').value = originalOrderValues.obs;
	document.getElementById('viewOrder-orderPrice').value = originalOrderValues.order_subtotal;

	viewOrderBaskets = structuredClone(originalOrderValues.order_items);
	renderOrderBaskets('view');
	viewOrderBasketSelector.clear();
	document.getElementById('viewOrder-basketQty').value = '';

	const isDeliveryElement = document.getElementById('viewOrder-isDelivery');
	isDeliveryElement.checked = originalOrderValues.isDelivery;
	document.getElementById('viewOrder-deliveryFee').value = originalOrderValues.delivery_fee;
	document.getElementById('viewOrder-newAddressText').value = '';
	getDeliveryState(isDeliveryElement, 'view');

	if (originalOrderValues.isDelivery && originalOrderValues.address_id !== null)
		viewOrderAddressSelector.setValue(originalOrderValues.address_id, true);

	const savedAddr = availableAddresses.find(
		addr => String(addr.id) === String(originalOrderValues.address_id)
	);

	viewOrderDeliveryDetails = {
		address_id: originalOrderValues.address_id,
		address_txt: savedAddr ? savedAddr.address_txt : null,
		delivery_fee: originalOrderValues.delivery_fee
	};

	viewOrderPriceManuallySet = false;

	updateOrderTotal('view');
	resetViewOrderModalState();
}

function resetViewOrderModalState() {
	const status = viewOrderStatusSelector.getValue();
	document.getElementById('viewOrder-editBtn').style.display = 'inline-block';
	if (status === "DELIVERED" || status === "CANCELLED")
		document.getElementById('viewOrder-editBtn').style.display = 'none';

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
	
	document.getElementById('viewOrder-saveBtn').style.display = 'none';
	document.getElementById('viewOrder-cancelBtn').style.display = 'none';

	document.getElementById('viewOrder-isDelivery').disabled = true;

	renderOrderBaskets('view');
	updateDetailsBtnIcon();
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
		showSnackbar('Selecione uma cesta.', 'warning');
		return;
	}

	if (!quantity || quantity <= 0) {
		showSnackbar('Informe uma quantidade válida', 'warning');
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
		showSnackbar('Essa cesta já foi adicionada ao pedido.', 'error');
		return;
	}

	let composition;
	try {
		composition = await fetchJson(`/basket_composition/${selectedBasket.id}`)
	}
	catch (err) {
		handleError(err);
		return;
	}

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

		const btn = document.getElementById('basketComposition-btn');
		btn.style.display = 'inline-block';
		btn.textContent = 'Adicionar';

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
	updateOrderTotal(mode);
}

const toNumber = v => parseFloat(String(v).replace(',', '.')) || 0;
function updateOrderTotal(mode) {
	const totalLabel = document.getElementById(`${mode}Order-totalPrice`);
	const deliveryFee = toNumber(document.getElementById(`${mode}Order-deliveryFee`).value);
	const orderPrice = toNumber(document.getElementById(`${mode}Order-orderPrice`).value);

	totalLabel.value = (deliveryFee + orderPrice).toFixed(2);
}

function cancelBasketComposition() {
	pendingOrderBasket = null;
	pendingOrderIndex = null;
	pendingOrderMode = null;
	closeModal('basketComposition-modal');
}

function cancelDeliveryDetails(mode) {
	const details = mode === 'new'
		? newOrderDeliveryDetails
		: viewOrderDeliveryDetails

	const selector = mode === 'new'
		? newOrderAddressSelector
		: viewOrderAddressSelector

	const confirmed = details.address_id != null || details.address_txt;

	if (!confirmed) {
		const checkbox = document.getElementById(`${mode}Order-isDelivery`);
		checkbox.checked = false;
		getDeliveryState(checkbox, mode);
	}

	else {
		document.getElementById(`${mode}Order-deliveryFee`).value = details.delivery_fee;
			
		if (details.address_id != null) {
			selector.setValue(details.address_id, true);
			document.getElementById(`${mode}Order-newAddressText`).value = details.address_txt || '';
		}

		else {
			selector.setValue(NEW_ADDRESS_ID, true);
			document.getElementById(`${mode}Order-newAddressText`).value = details.address_txt;
		}

		updateOrderTotal(mode);
	}

	closeModal(`${mode}-deliveryOrder-modal`);
}

function getDeliveryState(checkbox, mode) {
	const delivery = checkbox.checked;
	const clients = document.getElementById(`${mode}Order-client`)
	const editButton = document.getElementById(`${mode}Order-editDetailsBtn`);
	const label = document.getElementById(checkbox.id + 'Label');

	if (label)
		label.textContent = delivery ? 'Entrega' : 'Retirada';

	editButton.parentElement.style.display = delivery ? '' : 'none';

	if (delivery) {
		refreshAddressOptions(clients.value, mode);
		updateOrderTotal(mode);
	}
	else {
		const empty = {
			address_id: null,
			address_txt: null,
			delivery_fee: 0
		}

		document.getElementById(`${mode}Order-deliveryFee`).value = '';
		document.getElementById(`${mode}Order-newAddressText`).value = '';
		updateOrderTotal(mode);

		if (mode === 'new')
			newOrderDeliveryDetails = empty;
		else
			viewOrderDeliveryDetails = empty;
		closeModal(`${mode}-deliveryOrder-modal`);
	}
}

function updateDetailsBtnIcon() {
	const editButton = document.getElementById('viewOrder-editDetailsBtn');
	const editable = !document.getElementById('viewOrder-isDelivery').disabled;
	editButton.innerHTML = editable ? ICON_PENCIL : ICON_EYE;
}

function toggleDeliveryModal(checkbox, mode) {
	getDeliveryState(checkbox, mode);
	
	if (checkbox.checked)
		openEditDetailsModal(mode)
}

function openEditDetailsModal(mode) {
	if (mode === 'view') {
		const editable = !document.getElementById('viewOrder-isDelivery').disabled;

		viewOrderAddressSelector[editable ? 'enable' : 'disable']();
		document.getElementById('viewOrder-deliveryFee').disabled = !editable;
		document.getElementById('viewOrder-newAddressText').disabled = !editable;
		document.getElementById('view-deliveryDetails-btn').style.display = editable ? '' : 'none';
	}
	document.getElementById(`${mode}-deliveryOrder-modal`).style.display = 'flex';
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

	const addressTxt = newAddressText.value.trim();

	if (!selector.getValue()) {
		showSnackbar('Selecione um endereço.', 'warning');
		return;
	}

	if (!addressTxt) {
		showSnackbar('Informe um endereço válido.', 'warning');
		return;
	}
		
	if (selector.getValue() === NEW_ADDRESS_ID)
		details.address_id = null;

	else
		details.address_id = selector.getValue();

	details.address_txt = addressTxt;

	details['delivery_fee'] = deliveryFee.value.trim() || "0";
	closeModal(`${mode}-deliveryOrder-modal`);
}

function onClientChange(mode) {
	const checkbox = document.getElementById(`${mode}Order-isDelivery`);
	checkbox.checked = false;
	getDeliveryState(checkbox, mode);
}