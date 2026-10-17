document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".needs-validation").forEach(form => {
    form.addEventListener("submit", event => {
      if (!form.checkValidity()) {
        event.preventDefault();
        event.stopPropagation();
      }
      form.classList.add("was-validated");
    });
  });

  const donationForm = document.getElementById("donationForm");
  if (donationForm) {
    const prepared = document.getElementById("prepared");
    const safeUntil = document.getElementById("safeUntil");
    const error = document.getElementById("timeError");
    const localDateTime = date => {
      const pad = n => String(n).padStart(2, "0");
      return `${date.getFullYear()}-${pad(date.getMonth()+1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
    };
    prepared.max = localDateTime(new Date());
    const validate = () => {
      error.textContent = "";
      const now = new Date();
      const p = new Date(prepared.value);
      const s = new Date(safeUntil.value);
      if (prepared.value && p > now) error.textContent = "Preparation time cannot be in the future.";
      else if (prepared.value && safeUntil.value && s <= p) error.textContent = "The safe-consumption deadline must be after preparation time.";
      else if (safeUntil.value && s <= now) error.textContent = "Choose a deadline in the future.";
    };
    prepared.addEventListener("change", validate);
    safeUntil.addEventListener("change", validate);
    donationForm.addEventListener("submit", event => {
      validate();
      if (error.textContent) event.preventDefault();
    });
  }
});
