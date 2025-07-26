// Write your script here
const removeFromWishlist = (item_code) => {
  console.log("Removing from wishlist");
  fetch(`${page_data.url}/api/v2/method/webshop.webshop.doctype.wishlist.wishlist.remove_from_wishlist`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ item_code }),
  })
    .then((res) => {
      if (res.ok) {
        console.log("Removed from wishlist!", res), window.location.reload();
      } else console.log("Oops!", res);
    })
    .catch((err) => {
      console.error(err);
    });
};

document.addEventListener("DOMContentLoaded", () => {
  const removeButtons = document.querySelectorAll(".remove-from-wishlist");

  removeButtons.forEach((button) => {
    button.addEventListener("click", function (event) {
      event.stopPropagation(); // Stop event propagation
      event.preventDefault();

      const itemId = this.id; // Get the ID of the button
      removeFromWishlist(itemId); // Call the removeFromWishlist function
    });
  });
});
