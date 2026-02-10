// js/cart.js
document.addEventListener('alpine:init', () => {
    Alpine.store('cart', {
        items: [],
        count: 0,
        total: 0,

        async init() {
            await this.loadCart();
        },

        async loadCart() {
            try {
                const cartData = await getCart();
                if (cartData && cartData.items) {
                    this.items = cartData.items.map(item => ({
                        id: item.id,
                        name: item.product_name,
                        slug: item.product_slug,
                        price: parseFloat(item.price),
                        quantity: item.quantity,
                        total: parseFloat(item.total_price)
                    }));
                    this.updateStats();
                }
            } catch (err) {
                console.warn('Не удалось загрузить корзину с сервера', err);
            }
        },

        async add(slug, quantity = 1) {
            try {
                await addToCart(slug, quantity);
                await this.loadCart();          // перезагружаем с сервера
                alert('Товар добавлен в корзину!');
            } catch (err) {
                alert(err.detail || 'Ошибка при добавлении товара');
            }
        },

        updateStats() {
            this.count = this.items.reduce((sum, item) => sum + item.quantity, 0);
            this.total = this.items.reduce((sum, item) => sum + item.total, 0);
        },

        // можно добавить позже: remove, update quantity и т.д.
    });
});