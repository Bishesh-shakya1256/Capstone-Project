
const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

tabButtons.forEach(button => {
  button.addEventListener("click", () => {
    const tabId = button.dataset.tab;

    // Remove active class from all buttons
    tabButtons.forEach(btn => btn.classList.remove("active"));

    // Hide all contents
    tabContents.forEach(content => {
      content.classList.remove("active");
    });

    // Activate clicked button
    button.classList.add("active");

    // Show corresponding content
    document.getElementById(tabId).classList.add("active");
  });
});