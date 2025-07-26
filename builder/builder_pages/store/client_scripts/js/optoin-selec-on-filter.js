// Write your script here
document.addEventListener("DOMContentLoaded", () => {
  setTimeout(() => {
    console.log(page_data);
    filters = page_data;
    Object.entries(filters).forEach(([key, values]) => {
      console.log(key, values);
      const select = document.querySelector(`select[name="${key}"]`);
      if (!select) return;
      Array.from(select.options).forEach((option) => {
        option.selected = values.includes(option.value);
      });
    });
  }, 0);
});
