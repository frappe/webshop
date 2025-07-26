// Write your script here
// const baseUrlForWishList = `${page_data.url}/api/v2/method/webshop.webshop.doctype.wishlist.wishlist`; (deos not work as page_data is not available before domcontentload)
const midUrlForWishList = `/api/v2/method/webshop.webshop.doctype.wishlist.wishlist`;

const addToWishList = () => {
  console.log("Adding to wishlist");
  fetch(`${page_data.url}${midUrlForWishList}.add_to_wishlist`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ item_code: page_data?.code }),
  })
    .then((res) => {
      if (res.ok && !res.redirected) {
        console.log("Yes adding reviews is allowed!", res);
        window.location.reload();
      } else if (res.redirected) {
        window.location.href = res.url;
      } else console.log("Oops!", res);
    })
    .catch((err) => {
      console.error(err);
    });
};

const removeFromWishlist = () => {
  console.log("Removing from wishlist");
  fetch(`${page_data.url}${midUrlForWishList}.remove_from_wishlist`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ item_code: page_data?.code }),
  })
    .then((res) => {
      if (res.ok) {
        console.log("Removed from wishlist!", res);
        window.location.reload();
      } else console.log("Oops!", res);
    })
    .catch((err) => {
      console.error(err);
    });
};
const bindWishlistButtonActions = () => {
  const addToWishlistButton = document.getElementById("add-to-wishlist");
  if (addToWishlistButton) {
    addToWishlistButton.addEventListener("click", addToWishList);
  }
  const removeFromWishlistButton = document.getElementById(
    "remove-from-wishlist"
  );
  if (removeFromWishlistButton) {
    removeFromWishlistButton.addEventListener("click", removeFromWishlist);
  }
};

document.addEventListener("DOMContentLoaded", bindWishlistButtonActions);
