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

	const [response] = await Promise.all([
		fetch(`/home/${orderId}/items`),
		new Promise(resolve => setTimeout(resolve, 500))
	]);
	
	const data = await response.json();

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