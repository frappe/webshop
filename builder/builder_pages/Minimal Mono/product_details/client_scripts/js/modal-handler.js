// --------------------------------------------------
// Handle modal toggling
// --------------------------------------------------

const loadModal = (modalContentId) => {
  // load modal backdrop
  const modalBg = document.getElementById("modal-bg");
  modalBg.style.top = 0;
  modalBg.style.bottom = 0;
  // add content on top of modal backdrop
  const modalContent = document.getElementById(modalContentId);
  if (modalContent) {
    try {
      // remove content from the hidden wrapper
      const hiddenModalContentWrapper = document.getElementById(
        "hidden-modal-contents-wrapper"
      );
      hiddenModalContentWrapper.removeChild(modalContent);
      // and add it upon backdrop
      modalBg.appendChild(modalContent);
    } catch (err) {
      console.error("Error while showing modal:" ,err);
    }
  }
};

const hideModal = (modalContentId) => {
  // remove modal backdrop
  const modalBg = document.getElementById("modal-bg");
  modalBg.style.top = "unset";
  modalBg.style.bottom = "-110vh";
  // reverse what we did for adding the modal
  const modalContent = document.getElementById(modalContentId);
  if (modalContent) {
    try {
      const hiddenModalContentWrapper = document.getElementById(
        "hidden-modal-contents-wrapper"
      );
      modalBg.removeChild(modalContent);
      hiddenModalContentWrapper.appendChild(modalContent);
    } catch (err) {
      console.error("Error while hiding modal:" ,err);
    }
  }
};


document.addEventListener("DOMContentLoaded",() => {
    const allCloseModalButtons = document.querySelectorAll(".close-modal")
    for(const button of allCloseModalButtons){
        button.addEventListener("click",() => {
            hideModal(button.dataset.modalId)
        })
    }
})