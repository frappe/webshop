// Write your script here
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("option").forEach((option) => {
    option.innerHTML = option.value;
  });
  document.querySelector("#go-back").addEventListener("click", () => {
    window.history.back();
  });
});
