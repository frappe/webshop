// Write your script here
const removeCouponCode = async () => {
  console.log("removing coupon code...");
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.remove_coupon_code`;
  let response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
  });
  window.location.reload();
};

const applyCouponCode = async () => {
  console.log("adding coupon code...");
  const couponCode = document.querySelector("#coupon-code-input").value;
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.apply_coupon_code`;
  let response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({
      applied_code: couponCode,
      applied_referral_sales_partner: "", // not sure what to put here
    }),
  });
  if(!response.ok){
      const body = await response.json()
      alert(body.errors[0]?.message || "Something went wrong!");
      return;
  }
  console.log(response)
  window.location.reload()
};

document.addEventListener("DOMContentLoaded", () => {
  const addButton = document.querySelector("#add-coupon-code");
  addButton ? addButton.addEventListener("click", applyCouponCode) : "";

  const removeButton = document.querySelector("#remove-coupon-code");
  removeButton ? removeButton.addEventListener("click", removeCouponCode) : "";
});
