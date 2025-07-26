// Write your script here
function setStarRating(rating) {
  // Get all radio inputs within the rating group
  var radioInputs = document.querySelectorAll("#half-stars .rating__input");

  // Uncheck all radio inputs
  radioInputs.forEach(function (input) {
    input.checked = false;
  });

  // Find the radio input that matches the given rating and check it
  radioInputs.forEach(function (input) {
    if (input.value == rating) {
      input.checked = true;
    }
  });
}


document.addEventListener("DOMContentLoaded",() => {
    rating = page_data.my_rating;
    setStarRating(rating);
})