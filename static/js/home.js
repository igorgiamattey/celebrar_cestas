async function openOrderItemsModal(orderId) {
	const list = document.getElementById('orderItems-items')

	document.getElementById('orderItems-list').style.display = 'flex';
	list.innerHTML = `
		<div class="dots">
			<div class="dot"></div>
			<div class="dot"></div>
			<div class="dot"></div>
		</div>
	`;

	let data;

	try {
		[data] = await Promise.all([
			fetchJson(`/home_order_items/${orderId}`),
			new Promise(resolve => setTimeout(resolve, 500))
		]);
	}
	catch (err) {
		document.getElementById('orderItems-list').style.display = 'none';
		handleError(err);
		return;
	}

	list.innerHTML = '';

	data.items.forEach(item => {
		const bullet = document.createTextNode('\u2022');
		const times = document.createTextNode('\u00D7');

		const row = document.createElement('div');
		row.className = 'order-items-list-item';
		row.append(bullet, ` ${item.quantity} `, times, ` ${item.name}`);
		
		list.appendChild(row);
	})
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