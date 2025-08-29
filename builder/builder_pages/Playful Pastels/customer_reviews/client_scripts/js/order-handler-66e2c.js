// Write your script here
document.addEventListener("DOMContentLoaded", function () {
  // Get the button element by its ID
  const orderToggleButton = document.getElementById("orderToggleBtn");

  // Add an event listener for clicks on the button
  orderToggleButton.addEventListener("click", function () {
    // Get the current query parameters
    const queryParams = new URLSearchParams(window.location.search);

    // Get the current order value, default to 'asc' if not set
    let order = queryParams.get("order");
    let sortBy = queryParams.get("sort_by");
    if (!sortBy) {
      alert("Select a field to sort by!");
      return;
    }
    if (order === "asc") {
      queryParams.set("order", "desc");
    } else {
      queryParams.set("order", "asc");
    }

    // Update the URL with the new query parameters
    const newUrl = window.location.pathname + "?" + queryParams.toString();

    // Reload the page with the new URL
    window.location.href = newUrl;
  });
});
