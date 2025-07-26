// Write your script here
const loadModal = (modalContentId) => {
  const modalBg = document.getElementById("modal-bg");
  modalBg.style.top = 0;
  modalBg.style.bottom = 0;
  const modalContent = document.getElementById(modalContentId);
  if (modalContent) {
    try {
      const hiddenModalContentWrapper = document.getElementById(
        "hidden-modal-contents-wrapper"
      );
      hiddenModalContentWrapper.removeChild(modalContent);
      modalBg.appendChild(modalContent);
    } catch (err) {
      console.error("Error while showing modal:" ,err);
    }
  }
};

const hideModal = (modalContentId) => {
  const modalBg = document.getElementById("modal-bg");
  modalBg.style.top = "unset";
  modalBg.style.bottom = "-110vh";
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