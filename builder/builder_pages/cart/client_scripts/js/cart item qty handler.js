const updateCart = async (item_code, qty) => {
  console.log("being called");
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.update_cart`;

  const body = {
    item_code: item_code,
    qty: qty,
    with_items: 1,
  };

  console.log("Sending to:", url);
  console.log("Payload:", body);

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Frappe-CSRF-Token": frappe.csrf_token,
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) throw new Error("Cart update failed");

    console.log("Cart updated");
    location.reload();
  } catch (err) {
    console.error("Update error:", err);
  }
};

// const normalize = () => {
//   const input = container.querySelector(".quantity");
//   let val = parseFloat(input.value);
//   if (isNaN(val) || val < 0) val = 0;
//   input.value = Number.isInteger(val) ? val.toString() : val.toFixed(1);
// };

document.querySelectorAll(".item-input").forEach((container) => {
  const input = container.querySelector(".quantity");
  const incrementBtn = container.querySelector(".increment");
  const decrementBtn = container.querySelector(".decrement");
  const itemCode = container.id;

  const normalize = () => {
    const input = container.querySelector(".quantity");
    let val = parseFloat(input.value);
    if (isNaN(val) || val < 0) val = 0;
    input.value = Number.isInteger(val) ? val.toString() : val.toFixed(1);
  };

  incrementBtn.addEventListener("click", () => {
    input.value = parseFloat(input.value) + 1;
    normalize();
    updateCart(itemCode, input.value);
  });

  decrementBtn.addEventListener("click", () => {
    input.value = Math.max(0, parseFloat(input.value) - 1);
    normalize();
    updateCart(itemCode, input.value);
  });

  input.addEventListener("input", () => {
    normalize();
    updateCart(itemCode, input.value);
  });
  normalize();
});

document.querySelectorAll("[data-remove-from-cart]").forEach((button) => {
  button.addEventListener("click", () => {
    const itemCode = button.getAttribute("data-remove-from-cart");
    updateCart(itemCode, 0);
  });
});

// document.addEventListener("DOMContentLoaded", () => {
//   normalize();
// });
