// Write your script here
const placeOrder = async (item_code, qty) => {
  console.log("placing order");
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.place_order`;

  console.log("Sending to:", url);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": frappe.csrf_token,
      },
    });

    if (!response.ok) throw new Error("place order failed");
    
    const jsonRes = await response.json()

    console.log("order placed", jsonRes);
    window.location.href = '/order-new/' + encodeURIComponent(jsonRes.data);
    // location.reload();
  } catch (err) {
    console.error("Update error:", err);
  }
};

const requestQuotation = async (item_code, qty) => {
  console.log("requesting quote");
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.request_for_quotation`;

  console.log("Sending to:", url);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": frappe.csrf_token,
      },
    });

    if (!response.ok) throw new Error("request quote failed");
    const jsonRes = await response.json()

    console.log("quote requested", jsonRes);
    window.location.href = '/quotation-new/' + encodeURIComponent(jsonRes.data);
    // location.reload();
  } catch (err) {
    console.error("Update error:", err);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  let placeOrderBtn = document.getElementById("btn-place-order");
  if (placeOrderBtn) {
    placeOrderBtn.addEventListener("click", placeOrder);
  }
  let reqQuoteBtn = document.getElementById("btn-request-quote");
  if (reqQuoteBtn) {
    reqQuoteBtn.addEventListener("click", requestQuotation);
  }
});
