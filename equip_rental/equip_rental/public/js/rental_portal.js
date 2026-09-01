window.rentalPortal = {
	async call(method, args) {
		const response = await fetch(`/api/method/${method}`, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Frappe-CSRF-Token": frappe.csrf_token || "",
			},
			body: JSON.stringify(args || {}),
		});
		const payload = await response.json();
		if (!response.ok) {
			const message = (payload._server_messages &&
				JSON.parse(payload._server_messages).map((m) => JSON.parse(m).message).join("<br>"))
				|| payload.exception || "Request failed";
			throw new Error(message);
		}
		return payload.message;
	},

	notify(message, isError) {
		const box = document.getElementById("rental-alert");
		if (!box) return window.alert(message);
		box.className = `alert ${isError ? "alert-danger" : "alert-success"}`;
		box.innerHTML = message;
		box.style.display = "block";
		box.scrollIntoView({ behavior: "smooth", block: "center" });
	},
};

document.addEventListener("click", async (event) => {
	const button = event.target.closest("[data-rental-action]");
	if (!button) return;
	event.preventDefault();
	const action = button.dataset.rentalAction;

	if (action === "book") {
		const form = button.closest("[data-rental-form]");
		const value = (name) => {
			const field = form.querySelector(`[name="${name}"]`);
			return field ? field.value : null;
		};
		button.disabled = true;
		try {
			const result = await window.rentalPortal.call(
				"equip_rental.api.request_booking", {
					equipment: value("equipment"),
					equipment_category: value("equipment_category"),
					from_date: value("from_date"),
					to_date: value("to_date"),
					qty: value("qty") || 1,
					contact_person: value("contact_person"),
					contact_email: value("contact_email"),
					contact_mobile: value("contact_mobile"),
					site_address: value("site_address"),
					notes: value("notes"),
				});
			window.rentalPortal.notify(result.message);
			form.reset();
		} catch (error) {
			window.rentalPortal.notify(error.message, true);
		} finally {
			button.disabled = false;
		}
	}

	if (action === "off-hire") {
		const contract = button.dataset.contract;
		const date = prompt("Collection date (YYYY-MM-DD)");
		if (!date) return;
		try {
			const result = await window.rentalPortal.call(
				"equip_rental.api.request_off_hire",
				{ rental_contract: contract, requested_date: date });
			window.rentalPortal.notify(`Off-hire request ${result.name} submitted.`);
		} catch (error) {
			window.rentalPortal.notify(error.message, true);
		}
	}
});
