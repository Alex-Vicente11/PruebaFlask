function loadProducts() {
    fetch('/productos') // apunta al endpoint Flask
        .then(response => response.json())
        .then(products => {
            const productList = document.getElementById('product-list');
            productList.innerHTML = '';

            products.forEach(product => {
                const productDiv = document.createElement('div');
                productDiv.classList.add('product');
                productDiv.setAttribute('data-id', product.id);

                const name = document.createElement('h3');
                name.textContent = product.nombre;  
                productDiv.appendChild(name);

                const price = document.createElement('p');
                price.classList.add('price');
                price.textContent = `Precio: ${product.precio}`;
                productDiv.appendChild(price);

                const button = document.createElement('button');
                button.textContent = 'Añadir al carrito';
                button.classList.add('add-to-cart');
                button.addEventListener('click', () => {
                    addToCart(product);
                });
                productDiv.appendChild(button);

                productList.appendChild(productDiv);
            });
        });
}

let cart = [];

function updateCart() {
    const cartItems = document.getElementById('cart-items');
    const cartTotal = document.getElementById('cart-total');

    cartItems.innerHTML = '';

    if (cart.length === 0) {
        cartItems.innerHTML = '<p> Tu carrito esta vacio.</p>';
        cartTotal.textContent = '0';
        return;
    }

    let total = 0;
    cart.forEach(item => {
        const productDiv = document.createElement('div');
        productDiv.textContent = `${item.nombre} - ${item.precio}`;
        cartItems.appendChild(productDiv);
        total += parseFloat(item.precio);
    });

    cartTotal.textContent = total.toFixed(2);
}

function addToCart(product) {
    cart.push(product);
    localStorage.setItem('cart', JSON.stringify(cart));  //nueva linea para guardar en el carrito
    updateCart();
}

document.getElementById('checkout').addEventListener('click', () => {
    if (cart.length === 0) {
        alert('El carrito esta vacio');
        return;
    }

    //simulacion de compra
    alert('Compra procesada exitosamente');

    //Mostrar mensaje en pantalla
    const mensaje = document.getElementById('mensaje-compra');
    mensaje.style.display = 'block';

    //ocultar despues de 3 segundos
    setTimeout(() => {
        mensaje.style.display = 'none';
    }, 5000);

    localStorage.setItem('ultimaCompra', JSON.stringify(cart)); //guarda copia

    //vaciar carrito y actualizar
    cart = [];
    localStorage.removeItem('cart');
    updateCart();

    fetch('/procesar_compra', { 
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(cart)
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        cart = [];
        localStorage.removeItem('cart'); //borra el carrito del localStorage
        updateCart();
    });
});

//si hay carrito guardado en localStorage, se carga
const savedCart = localStorage.getItem('cart');
if (savedCart) {
    cart = JSON.parse(savedCart);
    updateCart();
}

loadProducts();



