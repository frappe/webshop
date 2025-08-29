const navbar = document.getElementById("navbar");
let hasBorderBeenAdded = false;
window.addEventListener("scroll", function () {
  if (window.scrollY > 0 || (window.pageYOffset > 0 && !hasBorderBeenAdded)) {
    navbar.classList.add("border-bottom");
    hasBorderBeenAdded = true;
  } else {
    navbar.classList.remove("border-bottom");
  }
});
