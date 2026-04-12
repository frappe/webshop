frappe.ready(function() {
	const checkout = {
		init: function() {
			this.setup_country_picker();
			this.init_phone();
			this.bind_address_selection();
			this.bind_address_actions();
			this.setup_payment_method_toggle();
			this.bind_coupon_logic();
			this.bind_events();
			this.bind_shipping_events();
			this.bind_billing_toggle();
		},

		bind_billing_toggle: function() {
			const me = this;
			$('input[name="billing_address_type"]').on('change', function() {
				const val = $(this).val();
				if (val === 'different') {
					$('#billing-address-section').removeClass('d-none');
					// Focus logic / smooth scroll slightly
					frappe.utils.scroll_to('#billing-address-section');
					
					// Auto select existing billing if new none chosen
					let curBill = $('input[name="customer_address"]:checked').val();
					if(curBill && curBill !== 'new') {
						me.select_billing_address(curBill);
					}
				} else {
					$('#billing-address-section').addClass('d-none');
					// Align billing with shipping immediately in backend
					const shipVal = $('input[name="shipping_address_name"]:checked').val();
					if (shipVal && shipVal !== 'new') {
						me.select_billing_address(shipVal);
					}
				}
			});
		},

		bind_address_selection: function() {
			const me = this;
			$('.address-card-option input[name="shipping_address_name"], .address-card-option input[name="customer_address"]').on('change', function() {
				const val = $(this).val();
				const isShipping = $(this).attr('name') === 'shipping_address_name';
				if (val === 'new') {
					$('#editing-address-name').val('');
					$("#btn-confirm-new-address").html('<i class="fa fa-check-circle mr-1"></i>' + __("Confirm & Save Address"));
					$('.manual-address-form').removeClass('d-none');
					frappe.utils.scroll_to('.manual-address-form');
				} else {
					if (isShipping) {
						me.select_shipping_address(val);
						// Sync to billing if 'Same as shipping' is selected
						if ($('input[name="billing_address_type"]:checked').val() === 'same') {
							me.select_billing_address(val);
						}
					} else {
						me.select_billing_address(val);
					}
					
					const shipVal = $('input[name="shipping_address_name"]:checked').val();
					const billVal = $('input[name="customer_address"]:checked').val();
					if (shipVal !== 'new' && billVal !== 'new') {
						$('.manual-address-form').addClass('d-none');
					}
				}
			});

			$("#btn-confirm-new-address").on("click", (e) => {
				e.preventDefault();
				this.confirm_new_address();
			});
		},

		bind_address_actions: function() {
			const me = this;
			
			// Edit Address
			$('.btn-edit-address').on('click', function(e) {
				e.preventDefault();
				e.stopPropagation();
				
				const btn = $(this);
				const name = btn.data('name');
				
				$('#editing-address-name').val(name);
				$('#checkout-addr-line1').val(btn.data('line1'));
				$('#checkout-city').val(btn.data('city'));
				$('#checkout-state').val(btn.data('state'));
				$('#checkout-pincode').val(btn.data('pincode'));
				
				const country = btn.data('country');
				if (country) {
					$('#checkout-country').val(country);
					$('.selected-country-name').text(country);
				}
				
				$("#btn-confirm-new-address").html('<i class="fa fa-save mr-1"></i>' + __("Update Address"));
				
				$('.manual-address-form').removeClass('d-none');
				frappe.utils.scroll_to('.manual-address-form');
			});
			
			// Delete Address
			$('.btn-delete-address').on('click', function(e) {
				e.preventDefault();
				e.stopPropagation();
				
				const name = $(this).data('name');
				if (confirm(__("Are you sure you want to delete this address?"))) {
					frappe.call({
						method: "webshop.webshop.shopping_cart.cart.delete_existing_address",
						args: { address_name: name },
						callback: (r) => {
							if (r.message && r.message.status === "success") {
								location.reload();
							}
						}
					});
				}
			});
			
			// Set Primary
			$('.btn-set-primary').on('click', function(e) {
				e.preventDefault();
				e.stopPropagation();
				
				const name = $(this).data('name');
				frappe.call({
					method: "webshop.webshop.shopping_cart.cart.set_address_as_primary",
					args: { address_name: name },
					callback: (r) => {
						if (r.message) {
							location.reload();
						}
					}
				});
			});
		},

		confirm_new_address: function() {
			const values = this.get_values();
			const editing_name = $('#editing-address-name').val();
			
			if (!values.address_line1 || !values.city || !values.country) {
				this.show_error(__("Please fill in the required address fields before saving."));
				return;
			}

			const btn = $("#btn-confirm-new-address");
			const original_html = btn.html();
			btn.prop("disabled", true).html('<i class="fa fa-spinner fa-spin mr-1"></i>' + __("Processing..."));

			frappe.call({
				method: editing_name ? 
					"webshop.webshop.shopping_cart.cart.update_existing_address" : 
					"webshop.webshop.shopping_cart.cart.save_new_address_and_update_cart",
				args: {
					address_name: editing_name,
					address_data: {
						address_line1: values.address_line1,
						city: values.city,
						state: values.state,
						country: values.country,
						pincode: values.pincode,
						phone: values.phone === "STAY_LOGGED_IN" ? "" : values.phone
					}
				},
				callback: (r) => {
					if (r.message) {
						location.reload();
					}
				},
				error: () => {
					btn.prop("disabled", false).html(original_html);
				}
			});
		},

		select_shipping_address: function(address_name) {
			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.update_cart_address",
				args: {
					address_type: "shipping",
					address_name: address_name
				},
				callback: (r) => {
					if (r.message) {
						this.update_cart_summary_from_resp(r.message);
					}
				}
			});
		},

		select_billing_address: function(address_name) {
			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.update_cart_address",
				args: {
					address_type: "billing",
					address_name: address_name
				},
				callback: (r) => {
					if (r.message) {
						this.update_cart_summary_from_resp(r.message);
					}
				}
			});
		},

		update_cart_summary: function() {
			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.get_cart_quotation",
				args: { for_checkout: true },
				callback: (r) => {
					if (r.message) {
						this.update_cart_summary_from_resp(r.message);
					}
				}
			});
		},

		update_cart_summary_from_resp: function(data) {
			if (data.taxes_and_totals) {
				$("#checkout-summary-totals").html(data.taxes_and_totals);
			}
		},

		bind_events: function() {
			$("#btn-final-place-order").on("click", () => {
				this.place_order();
			});

			// Receipt file selection feedback
			$("#payment-receipt-file").on("change", (e) => {
				const file = e.target.files[0];
				if (file) {
					$("#receipt-filename").text(file.name);
					$("#receipt-preview").removeClass("d-none");
					$(".custom-file-label").text(file.name);
				}
			});
		},

		setup_payment_method_toggle: function() {
			$('input[name="payment_method"]').on('change', (e) => {
				const selected = $(e.currentTarget).val();
				
				// Hide all containers first
				$("#raast-qr-container, #bank-details-container, #cod-instructions-container, #digital-payment-container, #receipt-upload-container").addClass("d-none");

				if (selected === "Raast") {
					$("#raast-qr-container, #receipt-upload-container").removeClass("d-none");
					this.fetch_raast_qr();
				} else if (selected === "Bank Transfer") {
					$("#bank-details-container, #receipt-upload-container").removeClass("d-none");
				} else if (selected === "COD") {
					$("#cod-instructions-container").removeClass("d-none");
				} else {
					$("#digital-payment-container").removeClass("d-none");
				}
			});
		},

		bind_coupon_logic: function() {
			$("#btn-apply-coupon").on("click", () => {
				const coupon_code = $("#input-coupon-code").val();
				if (!coupon_code) return;

				frappe.call({
					method: "webshop.webshop.shopping_cart.cart.apply_coupon_code",
					args: { coupon_code: coupon_code },
					callback: (r) => {
						if (r.message && r.message.status === "success") {
							location.reload();
						} else {
							frappe.show_alert({message: r.message.message, indicator: 'red'});
						}
					}
				});
			});
		},

		fetch_raast_qr: function() {
			const $wrapper = $("#raast-qr-wrapper");
			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.get_raast_qr",
				callback: (r) => {
					if (r.message && r.message.qr_string) {
						const qr_url = `https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(r.message.qr_string)}`;
						$wrapper.html(`<img src="${qr_url}" class="img-fluid" style="max-width: 200px;">`);
					} else if (r.message && r.message.error) {
						$wrapper.html(`<p class="extra-small text-danger mt-2 font-weight-bold">${r.message.error}</p>`);
					} else {
						$wrapper.html(`<p class="extra-small text-danger mt-2">${__("Dynamic QR Generation Failed")}</p>`);
					}
				}
			});
		},

		bind_shipping_events: function() {
			$('input[name="shipping_method"]').on('change', (e) => {
				const selected = $(e.currentTarget).val();
				frappe.call({
					method: 'webshop.webshop.shopping_cart.cart.set_guest_shipping_method',
					args: { method: selected },
					callback: () => {
						// Simple reload to refresh all totals/taxes from Jinja
						location.reload();
					}
				});
			});
		},

		get_values: function() {
			return {
				full_name: $("#checkout-full-name").val(),
				email: $("#checkout-email").val(),
				address_line1: $("#checkout-addr-line1").val(),
				city: $("#checkout-city").val(),
				state: $("#checkout-state").val(),
				country: $("#checkout-country").val(),
				pincode: $("#checkout-pincode").val(),
				payment_method: $('input[name="payment_method"]:checked').val(),
				create_account: $("#checkout-create-account").is(":checked"),
				phone: (() => {
					if ($("#checkout-phone").val() === "STAY_LOGGED_IN") return "STAY_LOGGED_IN";
					let num = this.iti ? this.iti.getNumber() : "";
					let rawVal = ($("#checkout-phone").val() || "").trim();
					if (!num && rawVal) {
						let dialCode = $(".iti__selected-dial-code").text() || "";
						if (dialCode && rawVal.startsWith("0")) {
							rawVal = rawVal.substring(1);
						}
						num = (dialCode + rawVal).replace(/\s+/g, '');
					}
					return num || rawVal;
				})(),
				shipping_address_name: $('input[name="shipping_address_name"]:checked').val(),
				customer_address_name: $('input[name="billing_address_type"]:checked').val() === 'different' 
					? $('input[name="customer_address"]:checked').val() 
					: $('input[name="shipping_address_name"]:checked').val(),
				billing_address_line1: $("#billing-addr-line1").val(),
				billing_city: $("#billing-city").val(),
				billing_state: $("#billing-state").val(),
				billing_country: $("#billing-country").val(),
				billing_pincode: $("#billing-pincode").val()
			};
		},

		init_phone: function() {
			const phone_input = document.querySelector("#checkout-phone");
			if (!phone_input || phone_input.type === 'hidden') return;

			this.iti = window.intlTelInput(phone_input, {
				initialCountry: "auto",
				geoIpLookup: function(success, failure) {
					fetch("https://ipapi.co/json")
						.then((res) => res.json())
						.then((data) => success(data.country_code))
						.catch(() => success("US"));
				},
				utilsScript: "https://cdn.jsdelivr.net/npm/intl-tel-input@24.6.0/build/js/utils.js",
				separateDialCode: true,
				nationalMode: true,
				autoFormat: true,
				customPlaceholder: function(selectedCountryPlaceholder, selectedCountryData) {
					return selectedCountryPlaceholder; // Ensure library doesn't wipe our styling
				}
			});
			
			// Wait a bit for ITI to be ready with data
			setTimeout(() => this.setup_country_picker(), 500);
		},

		setup_country_picker: function() {
			const me = this;
			const $wrapper = $("#country-picker-wrapper");
			const $options = $wrapper.find(".country-picker-options");
			const $search = $wrapper.find(".country-picker-search");
			const $selectedBox = $wrapper.find(".selected-country-box");
			const $hiddenInput = $("#checkout-country");

			if (!window.intlTelInputGlobals) return;
			
			let countries = window.intlTelInputGlobals.getCountryData();
			let deliverable = window.deliverable_countries || [];

			// Filter if deliverable countries are set in Webshop Settings
			if (deliverable.length > 0) {
				const deliverableNames = deliverable.map(d => d.country.toLowerCase());
				countries = countries.filter(c => deliverableNames.includes(c.name.toLowerCase()));
			}

			// Render options
			let html = "";
			countries.sort((a, b) => a.name.localeCompare(b.name)).forEach(c => {
				html += `
					<div class="country-option ${c.name === 'Pakistan' ? 'selected' : ''}" data-name="${c.name}" data-iso="${c.iso2}">
						<div class="iti__flag iti__${c.iso2}"></div>
						<span>${c.name}</span>
					</div>
				`;
			});
			$options.html(html);

			// Toggle dropdown
			$selectedBox.on("click", (e) => {
				e.stopPropagation();
				$wrapper.toggleClass("open");
				if ($wrapper.hasClass("open")) $search.focus();
			});

			$(document).on("click", () => $wrapper.removeClass("open"));
			$wrapper.on("click", (e) => e.stopPropagation());

			// Search functionality
			$search.on("input", function() {
				const val = $(this).val().toLowerCase();
				$options.find(".country-option").each(function() {
					const text = $(this).find("span").text().toLowerCase();
					$(this).toggle(text.includes(val));
				});
			});

			// Select logic
			$options.on("click", ".country-option", function() {
				const name = $(this).data("name");
				const iso = $(this).data("iso");

				$wrapper.find(".selected-country-name").text(name);
				$wrapper.find(".selected-country-info .iti__flag")
					.attr("class", `iti__flag iti__${iso}`);
				
				$hiddenInput.val(name);
				$options.find(".country-option").removeClass("selected");
				$(this).addClass("selected");
				$wrapper.removeClass("open");
			});
		},

		init_country_picker: function() {
			// Placeholder for more initialization if needed
		},

		validate: function(values) {
			let errors = [];
			if (!values.full_name) errors.push(__("Full Name is required"));
			if (!values.email) errors.push(__("Email is required"));
			
			// Only validate phone and manual address fields if not using a stored address
			const is_guest = !values.shipping_address_name && !values.customer_address_name;
			const ship_new = values.shipping_address_name === 'new';
			const bill_new = values.customer_address_name === 'new';
			
			const using_stored_address = !is_guest && !ship_new;
			const using_stored_billing = !is_guest && !bill_new;
			
			if (!using_stored_address) {
				if (!values.phone) {
					errors.push(__("Phone Number is required"));
				} else if (values.phone !== "STAY_LOGGED_IN" && this.iti && !this.iti.isValidNumber()) {
					// Fallback: If library thinks it's invalid but it has at least 7 digits, accept it
					const digitsOnly = values.phone.replace(/\D/g, '');
					if (digitsOnly.length < 7) {
						errors.push(__("Please enter a valid Phone Number"));
					}
				}
				if (!values.address_line1) errors.push(__("Delivery Address Line 1 is required"));
				if (!values.city) errors.push(__("Delivery City is required"));
				if (!values.country) errors.push(__("Delivery Country is required"));
			}

			if ($('input[name="billing_address_type"]:checked').val() === 'different' && !using_stored_billing) {
				if (!values.billing_address_line1) errors.push(__("Billing Address Line 1 is required"));
				if (!values.billing_city) errors.push(__("Billing City is required"));
				if (!values.billing_country) errors.push(__("Billing Country is required"));
			}

			if (!values.payment_method) {errors.push(__("Please select a Payment Method"));}
			
			if (errors.length) {
				this.show_error(errors.join("<br>"));
				return false;
			}
			return true;
		},

		show_error: function(msg) {
			$("#checkout-error").html(msg).show();
			frappe.utils.scroll_to("#checkout-error");
		},

		place_order: function() {
			const values = this.get_values();
			if (!this.validate(values)) return;

			$("#btn-final-place-order").prop("disabled", true).html(__("Processing..."));
			$("#checkout-error").hide();

			// Check for receipt upload
			const receipt_input = $("#payment-receipt-file")[0];
			const receipt_file = receipt_input ? receipt_input.files[0] : null;

			if (receipt_file && (values.payment_method === "Raast" || values.payment_method === "Bank Transfer")) {
				this.upload_receipt(receipt_file, (file_url) => {
					this.start_submission_flow(values, file_url);
				});
			} else {
				this.start_submission_flow(values);
			}
		},

		upload_receipt: function(file, callback) {
			const reader = new FileReader();
			reader.onload = () => {
				const base64_data = reader.result.split(',')[1];
				callback({ filename: file.name, filedata: base64_data });
			};
			reader.onerror = () => {
				this.reset_button();
				this.show_error(__("Failed to read receipt file. Please try again."));
			};
			reader.readAsDataURL(file);
		},

		start_submission_flow: function(values, receipt_info = null) {
			this.receipt_info = receipt_info;
			if (frappe.session.user === "Guest") {
				this.convert_guest_to_customer(values);
			} else {
				this.submit_order(null);
			}
		},

		convert_guest_to_customer: function(values) {
			let ajax_args = {
				email: values.email,
				full_name: values.full_name,
				phone: values.phone,
				create_account: values.create_account,
				address_data: {
					address_line1: values.address_line1,
					city: values.city,
					state: values.state,
					country: values.country,
					pincode: values.pincode
				}
			};

			if ($('input[name="billing_address_type"]:checked').val() === 'different') {
				ajax_args.billing_address_data = {
					address_line1: values.billing_address_line1,
					city: values.billing_city,
					state: values.billing_state,
					country: values.billing_country,
					pincode: values.billing_pincode
				};
			}

			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.convert_guest_cart_to_customer",
				args: ajax_args,
				callback: (r) => {
					if (r.message && r.message.status === "success") {
						this.submit_order(r.message.quotation);
					} else {
						this.reset_button();
						this.show_error(r.message ? r.message.message : __("Conversion failed"));
					}
				},
				error: (r) => {
					this.reset_button();
					this.show_error(__("Server error during guest conversion. Please try again."));
				}
			});
		},

		submit_order: function(quotation_name) {
			const payment_method = $('input[name="payment_method"]:checked').val();
			// For registered users (quotation_name will be null) or after guest conversion
			frappe.call({
				method: "webshop.webshop.shopping_cart.cart.place_order",
				args: {
					quotation_name: quotation_name,
					payment_method: payment_method,
					receipt_info: this.receipt_info
				},
				callback: (r) => {
					if (r.exc) {
						this.reset_button();
						this.show_error(__("Order placement failed. Please check your details."));
					} else {
						window.location.href = '/checkout-success?id=' + encodeURIComponent(r.message);
					}
				},
				error: (r) => {
					this.reset_button();
					this.show_error(__("Server error during order placement. Please try again."));
				}
			});
		},

		reset_button: function() {
			$("#btn-final-place-order").prop("disabled", false).html(__("Complete Order"));
		}
	}

	window.checkout = checkout;
});
