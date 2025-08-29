// Write your script here
function handlePageTurn(increment) {
  // Get the current query parameters
  const queryParams = new URLSearchParams(window.location.search);

  // Get the current page value, default to 1 if not set
  let page = queryParams.get("page");
  if (page === null) {
    page = 1;
  } else {
    page = parseInt(page);
  }

  // Increment the page value
  if (increment) page += 1;
  else page -= 1;

  // Set the new page value in the query parameters
  queryParams.set("page", page);

  // Update the URL with the new query parameters
  const newUrl = window.location.pathname + "?" + queryParams.toString();

  // Reload the page with the new URL
  window.location.href = newUrl;
}

document.addEventListener("DOMContentLoaded", function () {
  // Get the button element by its ID
  const nextPageButton = document.getElementById("nextPageButton");

  // Add an event listener for clicks on the button
  nextPageButton ? nextPageButton.addEventListener("click", () => handlePageTurn(true)) : "";
});

document.addEventListener("DOMContentLoaded", function () {
  // Get the button element by its ID
  const prevPageButton = document.getElementById("prevPageButton");

  // Add an event listener for clicks on the button
  prevPageButton ? prevPageButton.addEventListener("click", () => handlePageTurn(false)) : "";
});
