const backendUrl = "http://127.0.0.1:8000"; // Адрес Django сервера

// Загрузка категорий
async function loadCategories() {
    try {
        const res = await fetch(`${backendUrl}/api/v1/category/`);
        if (!res.ok) throw new Error(`Категории: ${res.status}`);
        const categories = await res.json();
        const container = document.getElementById("categories");
        container.innerHTML = categories.map(c => `
            <a href="#" onclick="filterCategory(${c.id})">${c.title}</a>
        `).join('');
    } catch (error) {
        console.error("Ошибка загрузки категорий:", error);
        document.getElementById("categories").innerHTML = "<p>Категории недоступны</p>";
    }
}

// Загрузка товаров
let allProducts = [];

async function loadProducts() {
    try {
        const res = await fetch(`${backendUrl}/api/v1/product/`);
        if (!res.ok) throw new Error(`Товары: ${res.status}`);

        const data = await res.json();
        console.log("Получено товаров:", data.results?.length || 0);

        allProducts = (data.results || []).filter(p => p.is_published);
        renderProducts(allProducts);
    } catch (error) {
        console.error("Ошибка загрузки товаров:", error);
        document.getElementById("products").innerHTML =
            "<p style='color:red; text-align:center; font-size:18px;'>Не удалось загрузить товары</p>";
    }
}

// Отображение карточек товаров
function renderProducts(products) {
    const container = document.getElementById("products");
    container.innerHTML = "";

    if (!products.length) {
        container.innerHTML = "<p style='text-align:center; color:#666;'>Товары не найдены</p>";
        return;
    }

    container.innerHTML = products.map(p => {
        // image уже содержит полный URL
        const imgUrl = p.image || 'images/no-image.png';

        return `
        <div class="product-card">
            <img src="${imgUrl}" alt="${p.name}" onclick="openProduct('${p.slug}')">
            <h3>${p.name}</h3>
            <p>${p.price} ₽</p>
            <button onclick="addToCart('${p.slug}')">В корзину</button>
        </div>
        `;
    }).join('');
}

// Фильтр по категории
function filterCategory(categoryId) {
    const filtered = allProducts.filter(p => p.category === categoryId);
    renderProducts(filtered);
}

// Открыть страницу товара
function openProduct(slug) {
    window.location.href = `product.html?slug=${slug}`;
}

// Добавить в корзину
async function addToCart(slug) {
    try {
        const token = localStorage.getItem("authToken") || "";
        const res = await fetch(`${backendUrl}/api/item/add/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                ...(token && { "Authorization": `Token ${token}` })
            },
            body: JSON.stringify({ product: slug, quantity: 1 })
        });

        if (!res.ok) {
            const err = await res.json();
            throw new Error(err.detail || "Ошибка добавления");
        }

        alert("Товар добавлен в корзину");
    } catch (err) {
        console.error(err);
        alert("Не удалось добавить товар: " + (err.message || "неизвестная ошибка"));
    }
}

// Инициализация страницы
document.addEventListener("DOMContentLoaded", () => {
    loadCategories();
    loadProducts();
});