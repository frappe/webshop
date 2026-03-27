// Override place_order to handle MoMo payment redirect
frappe.ready(function() {
    // Hook into the checkout form submit
    // The webshop uses a Shopping Cart controller — we patch after DOM ready
    $(document).on("click", ".btn-place-order, [data-action='place_order'], #btn-place-order", function(e) {
        e.preventDefault();
        e.stopImmediatePropagation();

        var btn = $(this);
        btn.prop("disabled", true).text(__("Processing..."));

        frappe.call({
            method: "webshop.webshop.shopping_cart.cart.place_order",
            callback: function(r) {
                if (r.message && r.message.payment_url) {
                    // MoMo flow: redirect to MoMo checkout page
                    window.location.href = r.message.payment_url;
                } else if (r.message && r.message.sales_order) {
                    // Fallback: go to order page
                    window.location.href = "/orders?name=" + r.message.sales_order;
                } else if (typeof r.message === "string") {
                    // Original webshop response (plain SO name)
                    window.location.href = "/orders?name=" + r.message;
                } else {
                    btn.prop("disabled", false).text(__("Place Order"));
                    frappe.msgprint(__("Something went wrong. Please try again."));
                }
            },
            error: function() {
                btn.prop("disabled", false).text(__("Place Order"));
            }
        });
    });
});
