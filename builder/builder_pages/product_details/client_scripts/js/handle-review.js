// Write your script here
const midUrlForReview = `/api/v2/method/webshop.webshop.doctype.item_review.item_review`;

const checkIfAllowed = () => {
  let resolveFunc;
  let rejectFunc;
  let promise = new Promise((resolve, reject) => {
    // Store the resolve and reject functions
    resolveFunc = resolve;
    rejectFunc = reject;
  });
  fetch(`${page_data.url}${midUrlForReview}.check_if_allowed`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ item_code: page_data?.code }),
  })
    .then((res) => {
      if (res.ok && !res.redirected) {
        console.log("Yes adding reviews is allowed!");
        resolveFunc(true);
      } else if (res.redirected) {
        window.location.href = res.url;
      } else console.log("Oops!", res);
      rejectFunc(false);
    })
    .catch((err) => {
      console.error(err);
    });
  return promise;
};

function getSelectedRatingValue() {
  // Get all radio inputs within the rating group
  var radioInputs = document.querySelectorAll("#half-stars .rating__input");

  // Iterate through the radio inputs to find the checked one
  for (var i = 0; i < radioInputs.length; i++) {
    if (radioInputs[i].checked) {
      return radioInputs[i].value;
    }
  }

  // If no radio button is checked, return null or a default value
  return null;
}

const saveReview = async () => {
  const url = `${page_data.url}${midUrlForReview}.add_item_review`;
  const title = document.getElementById("rating-title-input")?.value;
  const comment = document.getElementById("rating-comment-input")?.value;
  const web_item = page_data.web_item_code;
  const rating = getSelectedRatingValue() / 5;
  if (!title.trim() || !rating) {
    alert("Please enter required items!");
    return;
  }
  let res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ web_item, title, comment, rating }),
  });
  if (res.ok && !res.redirected) {
    console.log("Review added!");
    window.location.reload();
  } else if (res.redirected) {
    window.location.href = res.url;
  } else {
    console.log("Oops!", res);
  }
};

const deleteReview = async () => {
  const url = `${page_data.url}${midUrlForReview}.delete_item_review`;
  const web_item = page_data.web_item_code;

  let res = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Frappe-CSRF-Token": frappe.csrf_token,
    },
    body: JSON.stringify({ web_item }),
  });
  if (res.ok && !res.redirected) {
    console.log("Review deleted!");
    window.location.reload();
  } else if (res.redirected) {
    window.location.href = res.url;
  } else {
    console.log("Oops!", res);
  }
};

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".open-rating-input").forEach((elem) => {
    elem.addEventListener("click", async () => {
      let res = await checkIfAllowed();
      if (res) loadModal("rating-input");
    });
  });
  const reviewSaveButton = document.getElementById("review-save");
  if (reviewSaveButton) {
    reviewSaveButton.addEventListener("click", saveReview);
  }
  const reviewDeleteButton = document.getElementById("review-delete");
  if (reviewDeleteButton) {
    reviewDeleteButton.addEventListener("click", deleteReview);
  }
});
