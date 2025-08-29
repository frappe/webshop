// Write your script here
// Write your script here
document.addEventListener("DOMContentLoaded", function() {
    // Select all divs with the class 'rating-bars'
    var divs = document.querySelectorAll('div.rating-bars');

    // Iterate over each div and set its width
    divs.forEach(function(div) {
        var width = div.getAttribute('data-width');
        if (width !== null) {
            div.style.width = width + '%'; // Assuming data-width is in percentage
        }
    });
});
