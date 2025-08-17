// --------------------------------------------------
// Variant selection and cart handling
// --------------------------------------------------

let insertedVariantImage = false;

// main idea is to fetch (if exists) the image of the variant being selected
// and dynamically place it at the beginning of the slideshow

let numberOfDuplications = 0;
async function getAttributeSlideshow(selectedAttributes) {
  const itemCode = page_data.web_item_code;
  const baseUrl = `${page_data.url}/api/v2/method/webshop.webshop.variant_selector.utils.get_slideshow_for_selected_attribute`;
  const url = `${baseUrl}?selected_attributes=${encodeURIComponent(
    JSON.stringify(Object.values(selectedAttributes))
  )}&web_item_code=${encodeURIComponent(itemCode)}`;
  fetch(url).then(async (response) => {
    if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
    let { exact_matches, other_matches } = (await response.json()).data;
    if (numberOfDuplications) {
      for (let i = 0; i < numberOfDuplications; i++) {
        removeDuplicatedNode(".slideshow-slide");
      }
      numberOfDuplications = 0;
    }
    for (const url of other_matches) {
      duplicateNode(".slideshow-slide", { src: url });
      numberOfDuplications++;
    }
    for (const url of exact_matches) {
      duplicateNode(".slideshow-slide", { src: url });
      numberOfDuplications++;
    }
  });
}

function duplicateNode(selector, newAttributes = {}) {
  const original = document.querySelector(selector);
  if (!original) {
    console.warn(`Element not found for selector: ${selector}`);
    return null;
  }

  const clone = original.cloneNode(true);

  // Apply new attributes
  for (const [attr, value] of Object.entries(newAttributes)) {
    clone.setAttribute(attr, value);
  }

  // Insert as the first child of the parent
  original.parentNode.insertBefore(clone, original.parentNode.firstChild);

  return clone;
}

function removeDuplicatedNode(attributeSelector) {
  // as item was inserted at the beginning of the list, removing first element works
  const node = document.querySelector(attributeSelector);
  if (node) {
    node.remove();
    return true;
  } else {
    console.warn(`No element found with selector: ${attributeSelector}`);
    return false;
  }
}

document.addEventListener("DOMContentLoaded", async function () {
  const selects = document.querySelectorAll("select.attribute-select");

  selects.forEach(function (select) {
    select.addEventListener("change", async function () {
      const selectedAttributes = {};

      selects.forEach(function (s) {
        if (s.value) {
          selectedAttributes[s.id] = s.value;
        }
      });

      await getAttributeSlideshow(selectedAttributes);

      const itemCode = page_data.name;
      const baseUrl = `${page_data.url}/api/v2/method/webshop.webshop.variant_selector.utils.get_next_attribute_and_values`;
      const url = `${baseUrl}?selected_attributes=${encodeURIComponent(
        JSON.stringify(selectedAttributes)
      )}&item_code=${encodeURIComponent(itemCode)}`;

      console.log("Fetching:", url);
      // based on selected attribute, fetch next probable ones and see if exact match is found
      // if some attributes are incompatible with other ones, make sure once one attribute is selected only
      // compatible attributes are selectable
      fetch(url)
        .then((response) => {
          if (!response.ok)
            throw new Error(`HTTP error! Status: ${response.status}`);
          return response.json();
        })
        .then((data) => {
          const validOptions = data.data.valid_options_for_attributes;

          selects.forEach(function (s) {
            const attributeId = s.id;
            const options = s.querySelectorAll("option");

            if (validOptions[attributeId]) {
              const allowedValues = validOptions[attributeId];

              options.forEach(function (option) {
                if (option.value === "") return; // Keep default placeholder enabled
                option.disabled = !allowedValues.includes(option.value);
              });
            } else {
              // If attribute not in valid_options, disable all except placeholder
              options.forEach(function (option) {
                if (option.value !== "") option.disabled = true;
              });
            }
          });

          let exact_match = data.data.exact_match;
          if (exact_match.length && data.data.product_info) {
            let price = data.data.product_info.price;
            let image = data.data.product_info.image;
            page_data.code = exact_match[0];
            document.querySelector("#add-to-cart").removeAttribute("disabled");
            price
              ? (document.querySelector(".price").innerHTML =
                  price.formatted_price)
              : "";
            if (image) {
              if (insertedVariantImage) {
                removeDuplicatedNode(".slideshow-slide");
                duplicateNode(".slideshow-slide", { src: image });
              } else {
                insertedVariantImage = true;
                duplicateNode(".slideshow-slide", { src: image });
              }
            }
            console.log({ price, image });
          }
        })
        .catch((error) => {
          console.error("Fetch error:", error);
        });
    });
  });
});

document.addEventListener("DOMContentLoaded", function () {
  document.title = page_data.name;
  page_data.has_variant
    ? (document.querySelector("#add-to-cart").disabled = true)
    : "";
  document
    .querySelectorAll("button[data-select-clear-target]")
    .forEach(function (button) {
      button.addEventListener("click", function () {
        document.querySelector(".price").innerHTML = "";
        page_data.code = "";
        document.querySelector("#add-to-cart").disabled = true;
        if (insertedVariantImage) {
          insertedVariantImage = false;
          removeDuplicatedNode(".slideshow-slide");
        }
        const targetId = button.getAttribute("data-select-clear-target");
        const select = document.getElementById(targetId);
        select.value = "";

        if (select && select.tagName.toLowerCase() === "select") {
          const options = select.querySelectorAll("option");

          options.forEach(function (option) {
            // Don't enable the placeholder option
            if (option.value !== "") {
              option.disabled = false;
            }
          });
        }
      });
    });
});

const getIfCanAccessCart = async () => {
  const baseUrl = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.can_access_cart`;
  console.log("Checking if cart can be accessed...:", baseUrl);
  let response = await fetch(baseUrl);
  return (await response.json()).data;
};

const getGuestRedirect = async () => {
  const baseUrl = `${page_data.url}/api/v2/method/webshop.webshop.api.get_guest_redirect_on_action`;
  console.log("Checking if cart can be accessed...:", baseUrl);
  fetch(baseUrl).then(async (response) => {
    let url = (await response.json()).data;
    console.log("Redirecting to: ", url);
    window.location.href = url || "/login";
  });
};

const minusBtn = document.querySelector("#decrement");
const plusBtn = document.querySelector("#increment");
const input = document.querySelector("#number");

// Add event listeners
minusBtn.addEventListener("click", () => {
  let value = parseInt(input.value) || 1;
  if (value > 1) {
    input.value = value - 1;
  }
});

plusBtn.addEventListener("click", () => {
  let value = parseInt(input.value) || 1;
  input.value = value + 1;
});

const updateCart = async () => {
  const url = `${page_data.url}/api/v2/method/webshop.webshop.shopping_cart.cart.update_cart`;

  const body = {
    item_code: page_data.code,
    qty: input.value,
  };

  console.log("Sending to:", url);
  console.log("Payload:", body);

  await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify(body),
  });
  updateCartCount();
  console.log("Added to cart");
};

document.querySelector("#add-to-cart").addEventListener("click", async () => {
  let canAccessCart = await getIfCanAccessCart();
  console.log(canAccessCart);
  if (canAccessCart) {
    updateCart();
  } else {
    await getGuestRedirect();
  }
});
