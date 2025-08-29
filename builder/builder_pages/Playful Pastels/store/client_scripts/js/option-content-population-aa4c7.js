// Write your script here
document.querySelectorAll('option').forEach(option => {
  if (option.hasAttribute('value')) {
    option.textContent = option.getAttribute('value');
  }
});
