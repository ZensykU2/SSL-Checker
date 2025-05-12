document.addEventListener("DOMContentLoaded", function () {
  const checkboxes = document.querySelectorAll(".log-checkbox");
  const selectAll = document.getElementById("select-all");
  const bulkDeleteButton = document.getElementById("bulk-delete-button");
  const bulkDeleteIdsInput = document.getElementById("bulk-delete-ids");
  const singleDeleteForms = document.querySelectorAll(".single-delete-form");

  function updateDeleteUI() {
    const selectedIds = Array.from(checkboxes)
      .filter((cb) => cb.checked)
      .map((cb) => cb.value);

    bulkDeleteIdsInput.value = selectedIds.join(",");
    bulkDeleteButton.classList.toggle("hidden", selectedIds.length <= 1);

    singleDeleteForms.forEach((form) => {
      form.style.visibility = selectedIds.length > 1 ? "hidden" : "visible";
    });
  }

  checkboxes.forEach((cb) => cb.addEventListener("change", updateDeleteUI));

  if (selectAll) {
    selectAll.addEventListener("change", function () {
      const isChecked = selectAll.checked;
      checkboxes.forEach((cb) => (cb.checked = isChecked));
      updateDeleteUI();
    });
  }

  const multiDeleteForm = document.getElementById("multi-delete-form-top");
  if (multiDeleteForm) {
    multiDeleteForm.addEventListener("submit", function (e) {
      const logIds = bulkDeleteIdsInput.value;
      if (!logIds) {
        e.preventDefault();
        alert("Bitte wählen Sie mindestens einen Logeintrag zum Löschen aus.");
      } else {
        console.log("Formular wird mit diesen IDs abgeschickt:", logIds);
      }
    });
  }
});
