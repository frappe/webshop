// Write your script here
async function saveAddress(event) {
  event.preventDefault();
  const form = event.target;
  const formData = new FormData(form);
  const jsonData = {};

  for (const [key, value] of formData.entries()) {
    jsonData[key] = value;
  }
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.add_new_address`;
  let response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ doc: jsonData }),
  });
  console.log(await response.json());
  if(!response.ok){
      alert(response.errors[0]?.message || "Something went wrong");
      return;
  }
  alert("Address added, you will now be redirected to cart!");
  window.location.href = '/cart-new';
}
