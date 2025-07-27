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
function getCookie(name) {
  const cookies = document.cookie.split("; ");
  for (const cookie of cookies) {
    const [key, value] = cookie.split("=");
    if (key === name) return decodeURIComponent(value);
  }
  return null;
}

function updateCartCount() {
  let cart_count = getCookie("cart_count");
  console.log(cart_count, "cart_cout");
  let cartCountContainer = document.querySelector("#cart-count");
  let cartCountContainerMobile = document.querySelector("#cart-count-mobile");
  if (parseInt(cart_count)) {
    if (cartCountContainer) {
      cartCountContainer.style = "display: flex";
      cartCountContainer.innerHTML = cart_count;
    }
    if (cartCountContainerMobile) {
      cartCountContainerMobile.style = "display: flex";
      cartCountContainerMobile.innerHTML = cart_count;
    }
  } else {
    if (cartCountContainer) {
      cartCountContainer.style = "display: none";
    }
    if (cartCountContainerMobile) {
      cartCountContainerMobile.style = "display: none";
    }
  }
}
document.addEventListener("DOMContentLoaded", updateCartCount);


function highlightMatchingLink() {
  // Get the current URL
  const currentURL = window.location.href;

  // Get the element with the ID "links"
  const linksContainer = document.getElementById("links");

  // Check if the element exists
  if (linksContainer) {
    // Get the children of the "links" element
    const links = linksContainer.children;

    // Iterate over the children
    for (let i = 0; i < links.length; i++) {
      const link = links[i];

      // Check if the child has an ID and if the URL includes the ID
      if (link.id && currentURL.includes(link.id)) {
        // Add a grey background to the child
        link.style.textDecoration = "underline";
      }
    }
  }
}


document.addEventListener("DOMContentLoaded", () => {
    console.log("Loaded!");
    highlightMatchingLink();
})

document.addEventListener('DOMContentLoaded', function() {
    document.getElementById('openMobileMenu').addEventListener('click', function() {
        document.getElementById('mobileNavpanel').style.right = '0px';
    });
    document.getElementById('closeMobileMenu').addEventListener('click', function() {
        document.getElementById('mobileNavpanel').style.right = '-100%';
    });
});


