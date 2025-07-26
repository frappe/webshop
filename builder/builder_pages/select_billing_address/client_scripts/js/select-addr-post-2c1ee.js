// Write your script here
async function selectAddress() {
  if (!page_data?.selected) {
    alert("No Address Selected!");
    return;
  }
  const data = {
    address_type: "billing",
    address_name: page_data.selected,
  };
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.update_cart_address`;
  let response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify(data),
  });
  console.log(await response.json());
  if (!response.ok) {
    alert(response.errors[0]?.message || "Something went wrong");
    return;
  }
  console.log("Address selected, you will now be redirected to cart!");
  window.location.href = "/cart-new";
}


document.addEventListener("DOMContentLoaded", () => {
  document.querySelector("#select-address").addEventListener("click", () => {
    selectAddress()
  });
});
