// Write your script here
const svgString = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-circle-check-icon lucide-circle-check"><circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/></svg>`;

window.addEventListener("DOMContentLoaded", () => {
  const selectedId = page_data?.selected;
  if (selectedId) {
    const selectedDiv = document.getElementById(selectedId);
    if (selectedDiv) {
      selectedDiv.classList.add("selected");
    }
  }
  document.querySelectorAll("div.selected").forEach((div) => {
    const target = div.querySelector(".is-selected-check");
    if (target) {
      target.innerHTML = svgString;
    }
  });

  const selectableDivs = document.querySelectorAll(".selectable"); // Add 'selectable' class to your divs

  selectableDivs.forEach((div) => {
    div.addEventListener("click", () => {
      // Remove 'selected' from currently selected div
      const currentSelected = document.querySelector(".selectable.selected");
      if (currentSelected) {
        currentSelected.classList.remove("selected");
        currentSelected.querySelector(".is-selected-check").innerHTML = ""
      }

      // Add 'selected' to clicked div
      div.classList.add("selected");
      div.querySelector(".is-selected-check").innerHTML = svgString
      selectedDivId = div.id;
      page_data.selected = selectedDivId
      console.log("Selected ID:", selectedDivId);
    });
  });
});
