// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ready(() => {
  // Initialize elements
  const elements = {
    loyalty: {
      input: document.getElementById("loyalty-point-to-redeem"),
      status: document.getElementById("loyalty-points-status"),
      handler: applyLoyaltyPoints,
    },
    payment: {
      methodSelect: document.getElementById("payment-method"),
      phoneField: document.getElementById("mpesa-phone-field"),
      phoneInput: document.getElementById("phone-number"),
      handler: toggleMpesaField,
    },
  };

  // Set up event listeners
  if (elements.loyalty.input) {
    elements.loyalty.input.onblur = elements.loyalty.handler;
  }

  if (elements.payment.methodSelect) {
    elements.payment.methodSelect.addEventListener(
      "change",
      elements.payment.handler
    );
    // Initialize on load
    elements.payment.handler();
  }

  // Payment button handler
  const payButton = document.getElementById("pay-for-order");
  if (payButton) {
    payButton.addEventListener("click", processPayment);
  }

  // Common function to get payment gateway account
  function getPaymentGatewayAccount() {
    return new Promise((resolve) => {
      frappe.call({
        method: "frappe.client.get_value",
        args: {
          doctype: "Webshop Settings",
          fieldname: "payment_gateway_account",
        },
        callback: (r) => resolve(r.message?.payment_gateway_account),
      });
    });
  }

  // Common function to build request args
  async function buildRequestArgs(additionalArgs = {}) {
    const args = {
      dn: doc_info.doctype_name,
      dt: doc_info.doctype,
      submit_doc: 1,
      order_type: "Shopping Cart",
      ...additionalArgs,
    };

    // Include phone number if it exists (for both payment and loyalty)
    const phoneNumber = elements.payment.phoneInput?.value;
    if (phoneNumber) {
      args.phone_number = phoneNumber;
    }

    // Get payment gateway account if needed
    if (!additionalArgs.loyalty_points) {
      const paymentGatewayAccount = await getPaymentGatewayAccount();
      if (paymentGatewayAccount) {
        args.payment_gateway_account = paymentGatewayAccount;
      }
    }

    return args;
  }

  // Common function to create payment URL
  function createPaymentUrl(args) {
    const argsStr = Object.entries(args)
      .map(([key, val]) => `${key}=${encodeURIComponent(val)}`)
      .join("&");
    return `/api/method/erpnext.accounts.doctype.payment_request.payment_request.make_payment_request?${argsStr}`;
  }

  // Toggle MPesa field visibility
  function toggleMpesaField() {
    const method = elements.payment.methodSelect.value;
    if (elements.payment.phoneField) {
      elements.payment.phoneField.style.display =
        method === "mpesa" ? "block" : "none";
    }
  }

  // Process payment
  async function processPayment() {
    try {
      const paymentMethod = elements.payment.methodSelect?.value || "others";
      const args = await buildRequestArgs();
      window.location.href = createPaymentUrl(args);
    } catch (error) {
      console.error("Payment processing error:", error);
      showError(__("Error processing payment. Please try again."), error);
    }
  }

  // Apply loyalty points
  async function applyLoyaltyPoints() {
    const loyaltyPoints = parseInt(elements.loyalty.input.value);
    if (!loyaltyPoints) return;

    try {
      const redemptionFactor = await getRedemptionFactor();
      if (!redemptionFactor) return;

      const loyaltyAmount = flt(redemptionFactor * loyaltyPoints);

      if (doc_info.grand_total && doc_info.grand_total < loyaltyAmount) {
        const redeemableAmount = parseInt(
          doc_info.grand_total / redemptionFactor
        );
        showMessage(
          `You can only redeem max ${redeemableAmount} points in this order.`
        );
        return;
      }

      showMessage(
        `${loyaltyPoints} Loyalty Points of amount ${loyaltyAmount} is applied.`,
        true
      );

      const args = await buildRequestArgs({ loyalty_points: loyaltyPoints });
      updatePaymentButton(createPaymentUrl(args));
    } catch (error) {
      showError(__("Error applying loyalty points."), error);
    }
  }

  // Helper function to get redemption factor
  function getRedemptionFactor() {
    return new Promise((resolve) => {
      frappe.call({
        method:
          "erpnext.accounts.doctype.loyalty_program.loyalty_program.get_redeemption_factor",
        args: { customer: doc_info.customer },
        callback: (r) => resolve(r.message),
      });
    });
  }

  // Helper function to update payment button
  function updatePaymentButton(url) {
    const paymentButton = document.getElementById("pay-for-order");
    if (paymentButton) {
      paymentButton.innerHTML = __("Pay Remaining");
      paymentButton.href = url;
    }
  }

  // Helper function to show messages
  function showMessage(message, updateStatus = false) {
    frappe.msgprint(__(message));
    if (updateStatus && elements.loyalty.status) {
      elements.loyalty.status.innerHTML = message;
    }
  }

  // Helper function for error handling
  function showError(defaultMessage, error) {
    frappe.msgprint(__(defaultMessage));
    if (error?.message) {
      console.error(error);
      frappe.msgprint(__("Details: ") + error.message);
    }
  }
});
