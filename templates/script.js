function loadProducts() { // Función para cargar los productos desde el servidor
    fetch('obtener_productos.php') // Hace una petición GET al archivo PHP
        .then(response => response.json()) // Convierte la respuesta a formato JSON
        .then(products => { // Cuando los productos llegan como JSON:
            const productList = document.getElementById('product-list'); // Obtiene el contenedor donde se mostrarán los productos
            productList.innerHTML = ''; // Limpia el contenido previo (si lo hubiera)

            products.forEach(product => { // Recorre cada producto recibido

                const productDiv = document.createElement('div'); // Crea un div para el producto
                productDiv.classList.add('product'); // Le agrega la clase 'product' para estilos
                productDiv.setAttribute('data-id', product.id); // Guarda el ID como atributo HTML

                /*const img = document.createElement('img'); // Crea una imagen para el producto
                img.src = `images/${product.imagen}`; // Establece la ruta de la imagen
                img.alt = product.nombre; // Establece el texto alternativo
                productDiv.appendChild(img); // Agrega la imagen al div del producto
 */
                const name = document.createElement('h3'); // Crea un título para el nombre
                name.textContent = product.nombre; // Le pone el nombre del producto
                productDiv.appendChild(name); // Lo agrega al div

                const price = document.createElement('p'); // Crea un párrafo para el precio
                price.classList.add('price'); // Le agrega la clase 'price'
                price.textContent = `Precio: ${product.precio}`; // Establece el texto con el precio
                productDiv.appendChild(price); // Lo agrega al div

                const button = document.createElement('button'); // Crea un botón de "añadir al carrito"
                button.textContent = 'Añadir al carrito'; // Texto del botón
                button.classList.add('add-to-cart'); // Clase para estilos
                button.addEventListener('click', () => { // Al hacer clic en el botón...
                    addToCart(product); // Se agrega el producto al carrito
                });
                productDiv.appendChild(button); // Agrega el botón al div del producto

                productList.appendChild(productDiv); // Finalmente, agrega el producto completo al contenedor principal
            });
        });
}

let cart = []; // Carrito vacío al inicio (array de productos)

function updateCart() { // Función que actualiza el contenido del carrito
    const cartItems = document.getElementById('cart-items'); // Contenedor de los productos del carrito
    const cartTotal = document.getElementById('cart-total'); // Elemento donde se muestra el total

    cartItems.innerHTML = ''; // Limpia el contenido anterior del carrito

    if (cart.length === 0) { // Si el carrito está vacío
        cartItems.innerHTML = '<p> Tu carrito esta vacio.</p>'; // Mensaje en el carrito
        cartTotal.textContent = '0'; // Total en cero
        return; // Sale de la función
    }

    let total = 0; // Variable para acumular el total
    cart.forEach(item => { // Recorre los productos del carrito
        const productDiv = document.createElement('div'); // Crea un div para el producto
        productDiv.textContent = `${item.nombre} - ${item.precio}`; // Muestra nombre y precio
        cartItems.appendChild(productDiv); // Lo agrega al carrito
        total += parseFloat(item.precio); // Suma el precio al total
    });

    cartTotal.textContent = total.toFixed(2); // Muestra el total con 2 decimales
}

function addToCart(product) { // Función para agregar un producto al carrito
    cart.push(product); // Lo agrega al array
    updateCart(); // Actualiza la vista del carrito
}

document.getElementById('checkout').addEventListener('click', () => { // Al hacer clic en el botón "Procesar compra"

    if (cart.length === 0) { // Si el carrito está vacío
        alert('El carrito esta vacio'); // Muestra alerta
        return; // Sale
    }

    // Envía el contenido del carrito al servidor (procesar_compra.php)
    fetch('procesar_compra.php', {
        method: 'POST', // Método HTTP POST
        headers: {
            'Content-Type': 'application/json' // Tipo de contenido que se envía (JSON)
        },
        body: JSON.stringify(cart) // Convierte el carrito a JSON y lo manda en el cuerpo de la solicitud
    })
    .then(response => response.json()) // Convierte la respuesta del servidor a JSON
    .then(data => {
        alert(data.message); // Muestra el mensaje devuelto por el servidor
        cart = []; // Vacía el carrito
        updateCart(); // Actualiza la vista
    });
});

loadProducts(); // Carga los productos al cargar la página
