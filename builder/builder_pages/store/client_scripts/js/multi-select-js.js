/*
 * Created by David Adams
 * https://codeshack.io/multi-select-dropdown-html-javascript/
 *
 * Released under the MIT license
 */
class MultiSelect {
  constructor(element, options = {}) {
    let defaults = {
      placeholder: "Select item(s)",
      max: null,
      search: true,
      selectAll: true,
      listAll: true,
      closeListOnItemSelect: false,
      name: "",
      width: "",
      height: "",
      dropdownWidth: "",
      dropdownHeight: "",
      data: [],
      onChange: function () {},
      onSelect: function () {},
      onUnselect: function () {},
    };
    this.options = Object.assign(defaults, options);
    this.selectElement =
      typeof element === "string" ? document.querySelector(element) : element;

    const booleanOptions = [
      "search",
      "selectAll",
      "listAll",
      "closeListOnItemSelect",
    ];
    for (const prop in this.selectElement.dataset) {
      if (this.options.hasOwnProperty(prop)) {
        let value = this.selectElement.dataset[prop];
        if (booleanOptions.includes(prop)) {
          this.options[prop] = value === "true";
        } else if (prop === "max" && value !== null && value !== "") {
          this.options[prop] = parseInt(value, 10);
        } else if (value !== null && value !== "") {
          this.options[prop] = value;
        }
      }
    }
    this.name = this.selectElement.getAttribute("name")
      ? this.selectElement.getAttribute("name")
      : "multi-select-" + Math.floor(Math.random() * 1000000);
    if (!this.options.data.length) {
      let options = this.selectElement.querySelectorAll("option");
      for (let i = 0; i < options.length; i++) {
        this.options.data.push({
          value: options[i].value,
          text: options[i].innerHTML,
          selected: options[i].selected,
          html: options[i].getAttribute("data-html"),
        });
      }
    }
    this.element = this._template();
    this.selectElement.replaceWith(this.element);
    this._updateSelected();
    this._eventHandlers();
    this._updateSelectAllButtonState(); // Initial state update
  }

  _template() {
    let optionsHTML = "";
    for (let i = 0; i < this.data.length; i++) {
      optionsHTML += `
                <div class="multi-select-option${
                  this.selectedValues.includes(this.data[i].value)
                    ? " multi-select-selected"
                    : ""
                }" data-value="${this.data[i].value}">
                    <span class="multi-select-option-radio"></span>
                    <span class="multi-select-option-text">${
                      this.data[i].html ? this.data[i].html : this.data[i].text
                    }</span>
                </div>
            `;
    }
    let selectAllHTML = "";
    // Simplified boolean check
    if (this.options.selectAll) {
      selectAllHTML = `<div class="multi-select-all">
                <span class="multi-select-option-radio"></span>
                <span class="multi-select-option-text">Select all</span>
            </div>`;
    }
    let template = `
            <div class="multi-select ${this.name}"${
      this.selectElement.id ? ' id="' + this.selectElement.id + '"' : ""
    } style="${this.width ? "width:" + this.width + ";" : ""}${
      this.height ? "height:" + this.height + ";" : ""
    }">
                ${this.selectedValues
                  .map(
                    (value) =>
                      `<input type="hidden" name="${this.name}[]" value="${value}">`
                  )
                  .join("")}
                <div class="multi-select-header" style="${
                  this.width ? "width:" + this.width + ";" : ""
                }${this.height ? "height:" + this.height + ";" : ""}">
                    <span class="multi-select-header-max">${
                      this.options.max
                        ? this.selectedValues.length + "/" + this.options.max
                        : ""
                    }</span>
                    <span class="multi-select-header-placeholder">${
                      this.placeholder
                    }</span>
                </div>
                <div class="multi-select-options" style="${
                  this.options.dropdownWidth
                    ? "width:" + this.options.dropdownWidth + ";"
                    : ""
                }${
      this.options.dropdownHeight
        ? "height:" + this.options.dropdownHeight + ";"
        : ""
    }">
                    ${
                      this.options.search === true ||
                      this.options.search === "true"
                        ? '<input type="text" class="multi-select-search" placeholder="Search...">'
                        : ""
                    }
                    ${selectAllHTML}
                    ${optionsHTML}
                </div>
            </div>
        `;
    let element = document.createElement("div");
    element.innerHTML = template;
    element.style.minWidth = this.width;
    return element;
  }

  _eventHandlers() {
    let headerElement = this.element.querySelector(".multi-select-header");
    this.element.querySelectorAll(".multi-select-option").forEach((option) => {
      option.onclick = () => {
        let selected = true;
        if (!option.classList.contains("multi-select-selected")) {
          if (
            this.options.max &&
            this.selectedValues.length >= this.options.max
          ) {
            return;
          }
          option.classList.add("multi-select-selected");
          this.element
            .querySelector(".multi-select")
            .insertAdjacentHTML(
              "afterbegin",
              `<input type="hidden" name="${this.name}[]" value="${option.dataset.value}">`
            );
          this.data.filter(
            (data) => data.value == option.dataset.value
          )[0].selected = true;
        } else {
          option.classList.remove("multi-select-selected");
          this.element
            .querySelector(`input[value="${option.dataset.value}"]`)
            .remove();
          this.data.filter(
            (data) => data.value == option.dataset.value
          )[0].selected = false;
          selected = false;
        }
        if (!this.options.listAll) {
          if (this.element.querySelector(".multi-select-header-option")) {
            this.element.querySelector(".multi-select-header-option").remove();
          }
          headerElement.insertAdjacentHTML(
            "afterbegin",
            `<span class="multi-select-header-option">${this.selectedValues.length} selected</span>`
          );
        }
        if (this.options.max) {
          this.element.querySelector(".multi-select-header-max").innerHTML =
            this.selectedValues.length + "/" + this.options.max;
        }
        if (this.options.search) {
          this.element.querySelector(".multi-select-search").value = "";
        }
        this.element
          .querySelectorAll(".multi-select-option")
          .forEach((option) => (option.style.display = "flex"));
        if (this.options.closeListOnItemSelect) {
          headerElement.classList.remove("multi-select-header-active");
        }
        this.options.onChange(
          option.dataset.value,
          option.querySelector(".multi-select-option-text").innerHTML,
          option
        );
        if (selected) {
          this.options.onSelect(
            option.dataset.value,
            option.querySelector(".multi-select-option-text").innerHTML,
            option
          );
        } else {
          this.options.onUnselect(
            option.dataset.value,
            option.querySelector(".multi-select-option-text").innerHTML,
            option
          );
        }
        this._updateSelectAllButtonState(); // Update after individual click
      };
    });
    headerElement.onclick = () =>
      headerElement.classList.toggle("multi-select-header-active");

    if (this.options.search) {
      let search = this.element.querySelector(".multi-select-search");
      search.oninput = () => {
        this.element
          .querySelectorAll(".multi-select-option")
          .forEach((option) => {
            option.style.display =
              option
                .querySelector(".multi-select-option-text")
                .innerHTML.toLowerCase()
                .indexOf(search.value.toLowerCase()) > -1
                ? "flex"
                : "none";
          });
        this._updateSelectAllButtonState(); // Update after search filters items
      };
    }

    if (this.options.selectAll) {
      let selectAllButton = this.element.querySelector(".multi-select-all");
      selectAllButton.onclick = () => {
        let isCurrentlySelectAllActive = selectAllButton.classList.contains(
          "multi-select-selected"
        );
        let changedItems = [];
        let currentSelectedCount = this.selectedValues.length;

        this.element
          .querySelectorAll(".multi-select-option")
          .forEach((option) => {
            // Only consider visible options for select/deselect all
            if (option.style.display === "none") return;

            let dataItem = this.data.find(
              (data) => data.value == option.dataset.value
            );
            if (!dataItem) return;

            const shouldBeSelected = !isCurrentlySelectAllActive;

            if (dataItem.selected !== shouldBeSelected) {
              if (shouldBeSelected) {
                // Try to select
                if (
                  !this.options.max ||
                  currentSelectedCount < this.options.max
                ) {
                  option.classList.add("multi-select-selected");
                  this.element
                    .querySelector(".multi-select")
                    .insertAdjacentHTML(
                      "afterbegin",
                      `<input type="hidden" name="${this.name}[]" value="${option.dataset.value}">`
                    );
                  dataItem.selected = true;
                  currentSelectedCount++;
                  changedItems.push({
                    value: option.dataset.value,
                    text: option.querySelector(".multi-select-option-text")
                      .innerHTML,
                    option: option,
                    selected: true,
                  });
                }
              } else {
                // Try to unselect
                option.classList.remove("multi-select-selected");
                this.element
                  .querySelector(`input[value="${option.dataset.value}"]`)
                  ?.remove();
                dataItem.selected = false;
                currentSelectedCount--;
                changedItems.push({
                  value: option.dataset.value,
                  text: option.querySelector(".multi-select-option-text")
                    .innerHTML,
                  option: option,
                  selected: false,
                });
              }
            }
          });

        this._processBatchChanges(changedItems);
        this._updateSelectAllButtonState(); // Update button state based on actual selections
      };
    }
    if (
      this.selectElement.id &&
      document.querySelector('label[for="' + this.selectElement.id + '"]')
    ) {
      document.querySelector(
        'label[for="' + this.selectElement.id + '"]'
      ).onclick = () => {
        headerElement.classList.toggle("multi-select-header-active");
      };
    }
    document.addEventListener("click", (event) => {
      if (
        !event.target.closest("." + this.name) &&
        !event.target.closest('label[for="' + this.selectElement.id + '"]')
      ) {
        headerElement.classList.remove("multi-select-header-active");
      }
    });
  }

  _processBatchChanges(changedItems) {
    if (changedItems.length === 0) return;

    // Update header
    if (!this.options.listAll) {
      const headerOption = this.element.querySelector(
        ".multi-select-header-option"
      );
      if (headerOption) headerOption.remove();
      this.element
        .querySelector(".multi-select-header")
        .insertAdjacentHTML(
          "afterbegin",
          `<span class="multi-select-header-option">${this.selectedValues.length} selected</span>`
        );
    }

    // Update max count if needed
    if (this.options.max) {
      this.element.querySelector(".multi-select-header-max").innerHTML =
        this.selectedValues.length + "/" + this.options.max;
    }

    // Trigger single onChange for all items
    this.options.onChange(
      changedItems.map((item) => item.value),
      changedItems.map((item) => item.text),
      changedItems.map((item) => item.option)
    );

    // Trigger onSelect/onUnselect for items
    changedItems.forEach((item) => {
      if (item.selected) {
        this.options.onSelect(item.value, item.text, item.option);
      } else {
        this.options.onUnselect(item.value, item.text, item.option);
      }
    });
  }

  _updateSelected() {
    if (
      this.element.querySelector(".multi-select-header-option") &&
      this.element.querySelector(".multi-select-header-placeholder")
    ) {
      this.element.querySelector(".multi-select-header-placeholder").remove();
    }
    // Call _updateSelectAllButtonState here if not called at the end of constructor
    // this._updateSelectAllButtonState();
  }

  _updateSelectAllButtonState() {
    if (!this.options.selectAll) return;
    const selectAllButton = this.element.querySelector(".multi-select-all");
    if (!selectAllButton) return;

    const visibleOptions = Array.from(
      this.element.querySelectorAll(".multi-select-option")
    ).filter((opt) => opt.style.display !== "none");

    if (visibleOptions.length === 0) {
      selectAllButton.classList.remove("multi-select-selected");
      return;
    }

    const selectedVisibleOptionsCount = visibleOptions.filter((opt) =>
      opt.classList.contains("multi-select-selected")
    ).length;

    if (selectedVisibleOptionsCount === visibleOptions.length) {
      // All visible items are selected
      selectAllButton.classList.add("multi-select-selected");
    } else {
      // Not all visible items are selected
      selectAllButton.classList.remove("multi-select-selected");
    }
  }

  get selectedValues() {
    return this.data.filter((data) => data.selected).map((data) => data.value);
  }

  get selectedItems() {
    return this.data.filter((data) => data.selected);
  }

  set data(value) {
    this.options.data = value;
  }

  get data() {
    return this.options.data;
  }

  set selectElement(value) {
    this.options.selectElement = value;
  }

  get selectElement() {
    return this.options.selectElement;
  }

  set element(value) {
    this.options.element = value;
  }

  get element() {
    return this.options.element;
  }

  set placeholder(value) {
    this.options.placeholder = value;
  }

  get placeholder() {
    return this.options.placeholder;
  }

  set name(value) {
    this.options.name = value;
  }

  get name() {
    return this.options.name;
  }

  set width(value) {
    this.options.width = value;
  }

  get width() {
    return this.options.width;
  }

  set height(value) {
    this.options.height = value;
  }

  get height() {
    return this.options.height;
  }
}

const loadMultiSelectUI = () => {
  document.querySelectorAll("[data-multi-select]").forEach((select) => {
    let obj = new MultiSelect(select, {
      onChange: (value, text, option) => {
        items = obj.selectedItems.map((item) => item.value);
        key = obj.name;
        console.log(key, items)
        const params = new URLSearchParams(window.location.search);
        const url = new URL(window.location.href);

        // Set or replace the target key
        if(items.length) params.set(key, items.join(","));
        else params.delete(key)
        console.log(params)
        // Reload page with updated params
        window.location.search = params.toString();
      },
    });
  });
  const multiSelectWrapper = document.querySelector(".multi-select-wrapper")
  if(multiSelectWrapper) multiSelectWrapper.style.visibility = "visible"
//   const element = document.getElementById("shop-filters");
//   if (element) {
//     const yOffset = -100; // adjust this value as needed
//     const y = element.getBoundingClientRect().top + window.pageYOffset + yOffset;
//     window.scrollTo({ top: y });
//     window.scrollTo({ top: y, behavior: "smooth" });
//   }
}


document.addEventListener("DOMContentLoaded", () => {
  const selectList = document.querySelectorAll(`.multi-select-filter`);
  if (!selectList) return;
  for (const select of selectList) {
    const key = select.getAttribute('name')
    select.setAttribute("id", key.toLowerCase());
    select.setAttribute("name", key.toLowerCase());
    select.setAttribute("data-placeholder", key);
  }

  setTimeout(() => {
    filters = page_data;
    Object.entries(filters).forEach(([key, values]) => {
      const select = document.querySelector(`select[name="${key}"]`);
      if (!select) return;
      Array.from(select.options).forEach((option) => {
        option.selected = values.includes(option.value);
      });
    });
    loadMultiSelectUI()
  }, 0);
});