// Write your script here
window.addEventListener("load", () => {
  const scrollPos = localStorage.getItem("scrollPos");
  if (scrollPos !== null) {
    window.scrollTo(0, parseInt(scrollPos));
  }
});

window.addEventListener("scroll", () => {
  localStorage.setItem("scrollPos", window.scrollY);
});