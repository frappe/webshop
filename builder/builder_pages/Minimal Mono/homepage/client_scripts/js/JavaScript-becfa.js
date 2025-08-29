// Write your script here
const navbar = document.getElementById("navbar");
const hero = document.getElementById("hero");
if (navbar && hero) {
  const observer = new IntersectionObserver(
    ([entry]) => {
      if (!navbar) return;
      if (entry.isIntersecting) {
        navbar.classList.add("transparent");
        navbar.classList.remove("opaque");
      } else {
        navbar.classList.add("opaque");
        navbar.classList.remove("transparent");
      }
    },
    { threshold: 0.1 }
  );

  if (window.innerWidth > 640) {
    observer.observe(hero);
  } else {
    navbar.classList.remove("transparent");
    navbar.classList.add("opaque");
  }

  // Handle resize events
  window.addEventListener("resize", () => {
    if (window.innerWidth <= 640) {
      observer.unobserve(hero);
      navbar.classList.remove("transparent");
      navbar.classList.add("opaque");
    } else if (!observer.takeRecords().length) {
      observer.observe(hero);
    }
  });
}