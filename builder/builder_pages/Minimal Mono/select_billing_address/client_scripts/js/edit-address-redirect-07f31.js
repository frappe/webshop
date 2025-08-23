// Write your script here
document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".edit-address").forEach((div) => {
    div.addEventListener("click", () => {
      window.location.assign("/address/" + div.id)
    });
  });
});
