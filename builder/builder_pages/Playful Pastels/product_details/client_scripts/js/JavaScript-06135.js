// Write your script here
const variantImagesAddedEvent = new CustomEvent('variantImagesAddedEvent', {
  detail: {
    message: 'variantImagesAddedEvent!',
    data: {
      timestamp: Date.now(),
      origin: 'document-level-event'
    }
  },
  bubbles: true,
  cancelable: true
});


const scrollToSlideshowIndex = (index) => {
  let slideShowScrollWrapper = document.querySelector(
    ".slideshow-scroll-wrapper"
  );
  let slideShowItem = document.querySelector(".slideshow-slide");
  if (slideShowScrollWrapper && slideShowItem) {
    slideShowScrollWrapper.scrollTo({
      left: slideShowItem.width * index,
      behavior: "smooth",
    });
  }
};

const removeAllSlideshowThumbnailListeners = () => {
  thumbnailClickHandlers.forEach((handler, item) => {
    item.removeEventListener("click", handler);
  });
  thumbnailClickHandlers.clear();
}
// Use a Map to store the element and its corresponding handler function
const thumbnailClickHandlers = new Map();

document.addEventListener("DOMContentLoaded", () => {
  let allSlideShowThumbnails = document.querySelectorAll(
    ".slideshow-slide-thumbnail"
  );

  allSlideShowThumbnails.forEach((item, index) => {
    const handler = () => {
      scrollToSlideshowIndex(index);
    };
    item.addEventListener("click", handler);
    thumbnailClickHandlers.set(item, handler);
  });
});




document.addEventListener("variantImagesAddedEvent", () => {
  let allSlideShowThumbnails = document.querySelectorAll(
    ".slideshow-slide-thumbnail"
  );
  removeAllSlideshowThumbnailListeners();
  allSlideShowThumbnails.forEach((item, index) => {
      item.addEventListener("click",() => {
          scrollToSlideshowIndex(index)
      })
  })
});