// js/auth.js
function checkAuth() {
  const token = localStorage.getItem("authToken");
  const loginLink = document.getElementById("login-link");
  const logoutBtn = document.getElementById("logout-btn");

  if (token) {
    if (loginLink) loginLink.style.display = "none";
    if (logoutBtn) logoutBtn.style.display = "inline-block";
  } else {
    if (loginLink) loginLink.style.display = "inline-block";
    if (logoutBtn) logoutBtn.style.display = "none";
  }
}

function logout() {
  localStorage.removeItem("authToken");
  alert("Вы вышли из аккаунта");
  window.location.href = "index.html";
}

// Проверка при загрузке страницы
document.addEventListener("DOMContentLoaded", checkAuth);