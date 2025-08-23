// Write your script here
document.querySelectorAll('.options-repeater').forEach(div => {
  const parent = div.parentNode;
  while (div.firstChild) {
    parent.insertBefore(div.firstChild, div);
  }
  parent.removeChild(div);
});
