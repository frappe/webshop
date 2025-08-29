document.addEventListener("DOMContentLoaded", function () {
  // Get the select element by its ID
  const selectElement = document.getElementById("sortBySelect"); // replace 'yourSelectId' with the actual id of your select tag

  // Add an event listener for changes to the select element
  selectElement.addEventListener("change", function () {
    // Get the selected option's value
    const selectedOption =
      this.options[this.selectedIndex].textContent.toLowerCase();

    // Construct the query parameters
    const queryParams = new URLSearchParams(window.location.search);
    queryParams.set("sort_by", selectedOption);
    if (!queryParams.get("order")) {
      queryParams.set("order", "desc");
    }

    // Update the URL with the new query parameters
    const newUrl = window.location.pathname + "?" + queryParams.toString();

    // Reload the page with the new URL
    window.location.href = newUrl;
  });

  // Initialize the select element based on the current query parameters
  const queryParams = new URLSearchParams(window.location.search);
  const sortBy = queryParams.get("sort_by");

  if (sortBy === "rating" || sortBy === "date") {
    const options = selectElement.querySelectorAll("option");
    for (let i = 0; i < options.length; i++) {
      if (options[i].textContent.toLowerCase() === sortBy) {
        options[i].selected = true;
        break;
      }
    }
  }
});
