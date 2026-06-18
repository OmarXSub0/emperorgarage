document.addEventListener('DOMContentLoaded', function () {

    function setActiveThumbnails() {
        var carThumbnails = document.querySelectorAll('#carsGrid .thumbnail');
        var processedCars = {};

        for (var i = 0; i < carThumbnails.length; i++) {
            var thumb = carThumbnails[i];
            var productId = thumb.getAttribute('data-product-id');
            var imageIndex = thumb.getAttribute('data-image-index');

            if (imageIndex === '0' && !processedCars[productId]) {
                thumb.classList.add('active');
                processedCars[productId] = true;
            }
        }

        var partThumbnails = document.querySelectorAll('#partsGrid .thumbnail');
        var processedParts = {};

        for (var i = 0; i < partThumbnails.length; i++) {
            var thumb = partThumbnails[i];
            var productId = thumb.getAttribute('data-product-id');
            var imageIndex = thumb.getAttribute('data-image-index');

            if (imageIndex === '0' && !processedParts[productId]) {
                thumb.classList.add('active');
                processedParts[productId] = true;
            }
        }
    }
    var carThumbnails = document.querySelectorAll('#carsGrid .thumbnail');
    for (var i = 0; i < carThumbnails.length; i++) {
        carThumbnails[i].addEventListener('click', function () {
            var productId = this.getAttribute('data-product-id');
            var imageIndex = this.getAttribute('data-image-index');
            changeImage('car', productId, imageIndex, this);
        });
    }

    var partThumbnails = document.querySelectorAll('#partsGrid .thumbnail');
    for (var i = 0; i < partThumbnails.length; i++) {
        partThumbnails[i].addEventListener('click', function () {
            var productId = this.getAttribute('data-product-id');
            var imageIndex = this.getAttribute('data-image-index');
            changeImage('part', productId, imageIndex, this);
        });
    }
    setActiveThumbnails();
});

function changeMainImage(mainImageId, imageUrl) {
    const mainImage = document.getElementById(mainImageId);
    if (mainImage) {
        mainImage.src = imageUrl;
    }
}
const spinner = document.getElementById('popupspinner');
const Deletebtn = document.getElementById('deletebtn');

async function deleteProduct(productId) {
    if (confirm('Are you sure you want to delete this product? This action cannot be undone!')) {
        Deletebtn.disabled = true;
        if (spinner) spinner.classList.add('show');
        try {
            const response = await fetch(`/api/delete_product/${productId}`, {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' }
            });

            const result = await response.json();

            if (result.success) {
                alert('Product Deleted Successfully!');
                setTimeout(() => window.location.reload(), 3000);
            } else {
                alert('Error Deleting Product: ' + result.message);
            }
        } catch (error) {
            console.error('Delete error:', error);
            alert('Error deleting product. Please try again.');
        }
        finally {
            Deletebtn.disabled = false;
            if (spinner) spinner.classList.remove('show');
        }
    }
}

function showMessage(msg, type) {
    const messageDiv = document.getElementById('popupmessage');
    if (messageDiv) {
        messageDiv.textContent = msg;
        messageDiv.style.color = type === 'success' ? '#00ff41' : '#ff4444';
        messageDiv.style.backgroundColor = type === 'success' ? 'rgba(0,255,65,0.1)' : 'rgba(255,68,68,0.1)';
        messageDiv.style.padding = '10px';
        messageDiv.style.borderRadius = '5px';
        messageDiv.style.marginBottom = '15px';
        messageDiv.style.textAlign = 'center';

        setTimeout(() => {
            messageDiv.textContent = '';
            messageDiv.style.padding = '0';
        }, 2000);
    } else {
        alert(msg);
    }
}

window.changeImage = function (section, productId, imageIndex, clickedThumb) {
    var productCard = clickedThumb.closest('.product-card');

    if (!productCard) {
        console.error('Product card not found from clicked element');
        return;
    }

    // Optional: Verify section matches
    var cardCategory = productCard.getAttribute('data-category');
    if ((section === 'car' && cardCategory !== 'cars') ||
        (section === 'part' && cardCategory !== 'parts')) {
        console.warn('Section mismatch:', section, 'vs', cardCategory);
    }

    var mainImage = productCard.querySelector('.main-image');
    if (!mainImage) {
        console.error('Main image not found');
        return;
    }

    var newImageSrc = null;
    var thumbImg = clickedThumb.querySelector('img');
    if (thumbImg && thumbImg.src) {
        newImageSrc = thumbImg.src;
    }

    if (newImageSrc) {
        mainImage.src = newImageSrc;
    }

    var allThumbnails = productCard.querySelectorAll('.thumbnail');
    for (var i = 0; i < allThumbnails.length; i++) {
        allThumbnails[i].classList.remove('active');
    }
    clickedThumb.classList.add('active');
};

function contactDealer(productName, productType, productphone, productlocation) {
    var safeName = productName.replace(/[&<>]/g, function (m) {
        if (m === '&') return '&amp;';
        if (m === '<') return '&lt;';
        if (m === '>') return '&gt;';
        return m;
    });
    var phone = productphone;
    var location = productlocation;
    var message = "Hello! I'm interested in purchasing this seller's " + " (" + productType.toUpperCase()
        + ")" + safeName + " at " + location + " with number ";
    message += "\n" + phone;
    var encodedMessage = encodeURIComponent(message);
    var phoneNumber = '+233248631627';
    var whatsappUrl = 'https://wa.me/' + phoneNumber + '?text=' + encodedMessage;
    window.open(whatsappUrl, '_blank');
}

document.addEventListener('click', function (e) {
    var btn = e.target.closest('.call-btn');
    if (!btn) return;

    contactDealer(
        btn.getAttribute('data-product-name'),
        btn.getAttribute('data-product-type'),
        btn.getAttribute('data-product-phone'),
        btn.getAttribute('data-product-location')
    );
});

async function loadMyProducts() {
    try {
        const response = await fetch('/api/products/user');
        if (response.status === 401) return;

        const products = await response.json();
        const myProductsGrid = document.getElementById('myProductsGrid');
        if (!myProductsGrid) return;

        if (products.length === 0) {
            myProductsGrid.innerHTML = '<p>You haven\'t listed any products. Click "Sell Product" to get started!</p>';
            return;
        }

        myProductsGrid.innerHTML = products.map(product => `
            <div class="product-card">
                <img src="${product.image_url || 'https://via.placeholder.com/300x200?text=NO+IMAGE'}" 
                     alt="${product.name}">
                <h3>${escapeHtml(product.name)}</h3>
                <p>${escapeHtml(product.description?.substring(0, 100) || '')}...</p>
                <div class="price">$${product.price}</div>
                <div class="product-actions">
                    <button onclick="editProduct('${product.id}')" class="btn-edit">✏️ Edit</button>
                    <button onclick="deleteProduct('${product.id}')" class="btn-delete">🗑️ Delete</button>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error loading my products:', error);
    }
}

async function addProduct(productData) {
    try {
        const response = await fetch('/api/products', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });

        if (response.ok) {
            alert('Product added successfully!');
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to add product');
        }
    } catch (error) {
        console.error('Error adding product:', error);
        alert('Failed to add product');
    }
}

async function updateProduct(productId, productData) {
    try {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(productData)
        });

        if (response.ok) {
            alert('Product Updated Successfully!');
            loadMyProducts();
            closeProductModal();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to update product');
        }
    } catch (error) {
        console.error('Error updating product:', error);
        alert('Failed to update product');
    }
}

async function deleteProduct(productId) {
    if (!confirm('Are you sure you want to delete this product?')) return;

    try {
        const response = await fetch(`/api/products/${productId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            alert('Product deleted successfully!');
            window.location.reload();
        } else {
            const error = await response.json();
            alert(error.error || 'Failed to delete product');
        }
    } catch (error) {
        console.error('Error deleting product:', error);
        alert(error.message || JSON.stringify(error));
    }
}

function openImageModal(imageUrl, productName) {
    const modal = document.createElement('div');
    modal.style.cssText = `
        position: fixed;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        background: rgba(0,0,0,0.9);
        z-index: 10000;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
    `;

    const img = document.createElement('img');
    img.src = imageUrl;
    img.style.cssText = `
        max-width: 90%;
        max-height: 90%;
        object-fit: contain;
        border-radius: 8px;
    `;

    const caption = document.createElement('div');
    caption.style.cssText = `
        position: absolute;
        bottom: 20px;
        left: 0;
        right: 0;
        text-align: center;
        color: white;
        font-family: Arial, sans-serif;
        padding: 10px;
        background: rgba(0,0,0,0.5);
    `;
    caption.textContent = productName || 'Product Image';

    const closeBtn = document.createElement('button');
    closeBtn.innerHTML = '✖';
    closeBtn.style.cssText = `
        position: absolute;
        top: 20px;
        right: 30px;
        font-size: 40px;
        background: none;
        border: none;
        color: white;
        cursor: pointer;
        z-index: 10001;
    `;

    // Add to modal
    modal.appendChild(img);
    modal.appendChild(caption);
    modal.appendChild(closeBtn);
    document.body.appendChild(modal);

    modal.addEventListener('click', function (e) {
        if (e.target === modal || e.target === closeBtn) {
            modal.remove();
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape' && document.body.contains(modal)) {
            modal.remove();
        }
    });
}

async function filterByBrand(brand) {
    // Filter products by brand
    const productsGrid = document.getElementById('productsGrid');
    if (!productsGrid) return;

    try {
        const response = await fetch('/api/products');
        const products = await response.json();

        const filtered = products.filter(p => p.brand === brand);

        if (filtered.length === 0) {
            productsGrid.innerHTML = `<p>No products found for ${brand}</p>`;
            return;
        }

        // Re-render with filtered products
        productsGrid.innerHTML = filtered.map(product => `
            <div class="product-card">
                <img src="${product.image_url || 'https://via.placeholder.com/300x200?text=NO+IMAGE'}" 
                     alt="${product.name}">
                <h3>${escapeHtml(product.name)}</h3>
                <p>${escapeHtml(product.description?.substring(0, 100) || '')}...</p>
                <div class="price">$${product.price}</div>
                <div class="seller">Seller: ${escapeHtml(product.seller || 'Unknown')}</div>
                <button class="call-btn" onclick="contactSeller('${escapeHtml(product.seller)}')">
                    📞 Contact Seller
                </button>
            </div>
        `).join('');

        // Scroll to products section
        document.getElementById('products').scrollIntoView({ behavior: 'smooth' });
    } catch (error) {
        console.error('Error filtering products:', error);
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function contactSeller(seller) {
    alert(`Contact ${seller} via the marketplace messaging system (coming soon!)`);
}

let editingProductId = null;

function openProductModal(editMode = false, product = null) {
    const modal = document.getElementById('productModal');
    const title = document.getElementById('productModalTitle');

    if (editMode && product) {
        editingProductId = product.id;
        title.textContent = 'Edit Product';
        document.getElementById('productName').value = product.name || '';
        document.getElementById('productDescription').value = product.description || '';
        document.getElementById('productPrice').value = product.price || '';
        document.getElementById('productCategory').value = product.category || '';
        document.getElementById('productBrand').value = product.brand || '';
        document.getElementById('productImage').value = product.image_url || '';
    } else {
        editingProductId = null;
        title.textContent = 'Add Product';
        document.getElementById('productName').value = '';
        document.getElementById('productDescription').value = '';
        document.getElementById('productPrice').value = '';
        document.getElementById('productCategory').value = '';
        document.getElementById('productBrand').value = '';
        document.getElementById('productImage').value = '';
    }

    modal.style.display = 'block';
}

function closeProductModal() {
    document.getElementById('productModal').style.display = 'none';
    editingProductId = null;
}

function saveProduct() {
    const productData = {
        name: document.getElementById('productName').value,
        description: document.getElementById('productDescription').value,
        price: parseFloat(document.getElementById('productPrice').value),
        category: document.getElementById('productCategory').value,
        brand: document.getElementById('productBrand').value,
        location: document.getElementById('productLocation').value,
        phone: document.getElementById('productphone').value,
        image_url: document.getElementById('productImage').value
    };

    if (!productData.name || !productData.price) {
        alert('Please fill in product name and price');
        return;
    }

    if (editingProductId) {
        updateProduct(editingProductId, productData);
    } else {
        addProduct(productData);
    }
}

function editProduct(productId) {
    fetch(`/api/products`)
        .then(response => response.json())
        .then(products => {
            const product = products.find(p => p.id === productId);
            if (product) {
                openProductModal(true, product);
            }
        })
        .catch(error => console.error('Error fetching product:', error));
}
// ==================
// SEARCH-INITIALIZE
// ==================
document.addEventListener('DOMContentLoaded', () => {

    setTimeout(() => {
        collectAllProducts();
    }, 1000);

    const carBrands = [
        { name: "BMW", code: "bmw" },
        { name: "Audi", code: "audi" },
        { name: "Mercedes-Benz", code: "mercedes-benz" },
        { name: "Volkswagen", code: "volkswagen" },
        { name: "Toyota", code: "toyota" },
        { name: "Ford", code: "ford" },
        { name: "Honda", code: "honda" },
        { name: "Chevrolet", code: "chevrolet" },
        { name: "Nissan", code: "nissan" },
        { name: "Hyundai", code: "hyundai" },
        { name: "Kia", code: "kia" },
        { name: "Daewoo", code: "daewoo" },
        { name: "Mazda", code: "mazda" },
        { name: "Lexus", code: "lexus" },
        { name: "Volvo", code: "volvo" },
        { name: "Jaguar", code: "jaguar" },
        { name: "Land-Rover", code: "land-rover" },
        { name: "Mclaren", code: "mclaren" },
        { name: "Maserati", code: "maserati" },
        { name: "Dodge", code: "dodge" },
        { name: "Ram", code: "ram" },
        { name: "Jeep", code: "jeep" },
        { name: "GMC", code: "gmc" },
        { name: "Cadillac", code: "cadillac" },
        { name: "Acura", code: "acura" },
        { name: "Mitsubishi", code: "mitsubishi" },
        { name: "Suzuki", code: "suzuki" },
        { name: "Ferrari", code: "ferrari" },
        { name: "Lamborghini", code: "lamborghini" },
        { name: "Porsche", code: "porsche" },
        { name: "Tesla", code: "tesla" }
    ];
    const searchInput = document.getElementById('searchInput');
    const searchButton = document.getElementById('searchButton');

    if (searchInput) {
        searchInput.addEventListener('input', (e) => {
            showSuggestions(e.target.value);
        });

        searchInput.addEventListener('keyup', (e) => {
            if (e.key === 'Enter') {
                const term = searchInput.value.trim();
                if (term) {
                    performSearch();
                    saveRecentSearch(term);
                }
                document.getElementById('searchSuggestions').style.display = 'none';
            }
        });

        document.addEventListener('click', (e) => {
            const container = document.getElementById('searchSuggestions');
            if (container && !searchInput.contains(e.target) && !container.contains(e.target)) {
                container.style.display = 'none';
            }
        });
    }

    if (searchButton) {
        searchButton.addEventListener('click', () => {
            const term = searchInput.value.trim();
            if (term) {
                performSearch();
                saveRecentSearch(term);
            }
            document.getElementById('searchSuggestions').style.display = 'none';
        });
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const filter = e.target.getAttribute('data-filter');
            setFilter(filter);
        });
    });

    initVoiceSearch();

    const clearRecentBtn = document.getElementById('clearRecentBtn');
    if (clearRecentBtn) {
        clearRecentBtn.addEventListener('click', clearAllRecentSearches);
    }

    async function loadBrands() {
        try {
            const response = await fetch('/api/brands');
            const brands = await response.json();

            const brandsGrid = document.getElementById('brandsGrid');
            if (!brandsGrid) return;

            brandsGrid.innerHTML = brands.map(brand => `
            <div class="brand-item" onclick="filterByBrand('${brand.name}')">
                <img src="/static/images/brands/${brand.code}.png" 
                     class="brand-logo" 
                     alt="${brand.name}"
                     onerror="this.src='data:image/svg+xml,%3Csvg xmlns=\'https://www.carlogos.org/car-brands/\' width=\'80\' height=\'80\'%3E%3Crect width=\'80\' height=\'80\' fill=\'%234286f4\'/%3E%3Ctext x=\'50%25\' y=\'50%25\' text-anchor=\'middle\' dy=\'.3em\' font-size=\'36\' fill=\'white\'%3E${brand.name.charAt(0)}%3C/text%3E%3C/svg%3E'">
                <p>${brand.name}</p>
            </div>
        `).join('');
        } catch (error) {
            console.error('Error loading brands:', error);
        }

    }
    function searchBrand(brand) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = brand;
            performSearch();
            saveRecentSearch(brand);
        }
    }
    let currentFilter = 'all';

    function performSearch() {
        const searchInput = document.getElementById('searchInput');
        const searchTerm = searchInput.value.toLowerCase().trim();
        const searchTermSpan = document.getElementById('searchTerm');

        const carsCards = document.querySelectorAll('#cars .product-card');
        const partsCards = document.querySelectorAll('#parts .product-card');
        const allCards = [...carsCards, ...partsCards];

        let hasResults = false;
        let resultCount = 0;

        allCards.forEach(card => {
            const title = card.querySelector('h3')?.innerText.toLowerCase() || '';
            const description = card.querySelector('p')?.innerText.toLowerCase() || '';
            const price = card.querySelector('.price')?.innerText.toLowerCase() || '';

            const matchesSearch = searchTerm === '' ||
                title.includes(searchTerm) ||
                description.includes(searchTerm) ||
                price.includes(searchTerm);

            const category = card.closest('#cars') ? 'cars' : 'parts';
            const matchesFilter = currentFilter === 'all' || category === currentFilter;

            if (matchesSearch && matchesFilter) {
                card.style.display = 'block';
                hasResults = true;
                resultCount++;
                card.style.animation = 'highlight 0.5s ease';
                setTimeout(() => {
                    card.style.animation = '';
                }, 500);
            } else {
                card.style.display = 'none';
            }
        });

        const resultCountDiv = document.getElementById('resultCount');
        if (resultCountDiv) {
            if (searchTerm !== '') {
                resultCountDiv.innerHTML = `Found ${resultCount} result${resultCount !== 1 ? 's' : ''} for "${searchTerm}"`;
                resultCountDiv.style.display = 'block';
            } else {
                resultCountDiv.style.display = 'none';
            }
        }

        const noResultsDiv = document.getElementById('noResults');
        if (!hasResults && searchTerm !== '') {
            noResultsDiv.style.display = 'block';
            if (searchTermSpan) searchTermSpan.innerText = searchTerm;

            const suggestionsDiv = document.getElementById('noResultsSuggestions');
            if (suggestionsDiv) {
                if (carBrands.some(b => String(b || '').toLowerCase().includes(searchTerm))) {
                    suggestionsDiv.innerHTML = `💡 Try clicking on the ${searchTerm.toUpperCase()} logo below!`;
                } else {
                    suggestionsDiv.innerHTML = '💡 Try: BMW, brake pads, turbo, oil filter, or any car brand';
                }
            }
        } else {
            noResultsDiv.style.display = 'none';
        }
    }

    function setFilter(filter) {
        currentFilter = filter;

        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.remove('active');
            if (btn.getAttribute('data-filter') === filter) {
                btn.classList.add('active');
            }
        });

        performSearch();
    }
    let allProductsData = [];

    function collectAllProducts() {
        const carsCards = document.querySelectorAll('#cars .product-card');
        const partsCards = document.querySelectorAll('#parts .product-card');

        const products = [];

        carsCards.forEach(card => {
            const title = card.querySelector('h3')?.innerText || '';
            if (title) products.push({ title: title, category: 'car', element: card });
        });

        partsCards.forEach(card => {
            const title = card.querySelector('h3')?.innerText || '';
            if (title) products.push({ title: title, category: 'part', element: card });
        });

        allProductsData = products;
    }

    function showSuggestions(input) {
        const suggestionsContainer = document.getElementById('searchSuggestions');
        if (!suggestionsContainer) return;

        if (input.length < 2) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        const productMatches = allProductsData
            .filter(p => p.title.toLowerCase().includes(input.toLowerCase()))
            .slice(0, 5)
            .map(p => ({ text: p.title, type: 'product', category: p.category }));

        const brandMatches = carBrands
            .filter(b => b.name.toLowerCase().includes(input.toLowerCase()))
            .slice(0, 3)
            .map(b => ({ text: b.name, type: 'brand', category: 'brand' }));

        const suggestions = [...productMatches, ...brandMatches];

        if (suggestions.length === 0) {
            suggestionsContainer.style.display = 'none';
            return;
        }

        suggestionsContainer.innerHTML = suggestions.map(s => `
        <div class="suggestion-item" onclick="selectSuggestion('${s.text.replace(/'/g, "\\'")}')">
            <span class="suggestion-icon">${s.type === 'brand' ? '' : (s.category === 'car' ? '🚗' : '🔧')}</span>
            <span class="suggestion-text">${s.text}</span>
            <span class="suggestion-category">${s.type === 'brand' ? 'Brand' : (s.category === 'car' ? 'Car' : 'Part')}</span>
        </div>
    `).join('');

        suggestionsContainer.style.display = 'block';
    }

    function selectSuggestion(text) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = text;
            performSearch();
            saveRecentSearch(text);
        }
        const container = document.getElementById('searchSuggestions');
        if (container) container.style.display = 'none';
    }

    function initVoiceSearch() {
        const voiceBtn = document.getElementById('voiceSearchBtn');
        if (!voiceBtn) return;

        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            voiceBtn.style.display = 'none';
            return;
        }

        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = 'en-US';

        voiceBtn.addEventListener('click', () => {
            voiceBtn.classList.add('voice-listening');
            voiceBtn.innerHTML = '🎤 LISTENING...';

            recognition.start();

            recognition.onresult = (event) => {
                const transcript = event.results[0][0].transcript;
                const searchInput = document.getElementById('searchInput');
                if (searchInput) {
                    searchInput.value = transcript;
                    performSearch();
                    saveRecentSearch(transcript);
                }
                voiceBtn.classList.remove('voice-listening');
                voiceBtn.innerHTML = '🎤';
            };

            recognition.onerror = () => {
                voiceBtn.classList.remove('voice-listening');
                voiceBtn.innerHTML = '🎤';
            };

            recognition.onend = () => {
                voiceBtn.classList.remove('voice-listening');
                voiceBtn.innerHTML = '🎤';
            };
        });
    }
    let recentSearches = [];

    function loadRecentSearches() {
        const saved = localStorage.getItem('garage_recent_searches');
        if (saved) {
            recentSearches = JSON.parse(saved);
        }
        updateRecentSearchesDisplay();
    }

    function saveRecentSearch(term) {
        if (!term || term.trim() === '') return;

        recentSearches = recentSearches.filter(s => s !== term);
        recentSearches.unshift(term);
        recentSearches = recentSearches.slice(0, 10);

        localStorage.setItem('garage_recent_searches', JSON.stringify(recentSearches));
        updateRecentSearchesDisplay();
    }

    function updateRecentSearchesDisplay() {
        const container = document.getElementById('recentSearchesContainer');
        if (!container) return;

        if (recentSearches.length === 0) {
            container.innerHTML = '<div class="recent-empty">No recent searches yet 🔍</div>';
            return;
        }

        container.innerHTML = recentSearches.map(term => `
        <div class="recent-item" onclick="applyRecentSearch('${term.replace(/'/g, "\\'")}')">
            <span class="recent-icon">🕐</span>
            <span class="recent-term">${term}</span>
            <span class="recent-delete" onclick="event.stopPropagation(); deleteRecentSearch('${term.replace(/'/g, "\\'")}')">✖</span>
        </div>
    `).join('');
    }

    function applyRecentSearch(term) {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.value = term;
            performSearch();
            const container = document.getElementById('searchSuggestions');
            if (container) container.style.display = 'none';
        }
    }

    function deleteRecentSearch(term) {
        recentSearches = recentSearches.filter(s => s !== term);
        localStorage.setItem('garage_recent_searches', JSON.stringify(recentSearches));
        updateRecentSearchesDisplay();
    }

    function clearAllRecentSearches() {
        recentSearches = [];
        localStorage.setItem('garage_recent_searches', JSON.stringify(recentSearches));
        updateRecentSearchesDisplay();
    }
    loadBrands();
    loadRecentSearches();
});

window.selectSuggestion = function (text) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = text;
        if (typeof performSearch === 'function') {
            performSearch();
        }
        if (typeof saveRecentSearch === 'function') {
            saveRecentSearch(text);
        }
    }
    const container = document.getElementById('searchSuggestions');
    if (container) container.style.display = 'none';
};

window.applyRecentSearch = function (term) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = term;
        if (typeof performSearch === 'function') {
            performSearch();
        }
    }
    const container = document.getElementById('searchSuggestions');
    if (container) container.style.display = 'none';
};

window.deleteRecentSearch = function (term) {
    // This needs access to recentSearches
    const recentSearchesContainer = document.getElementById('recentSearchesContainer');
    if (recentSearchesContainer) {
        // Trigger the delete through a custom event or refetch
        const event = new CustomEvent('deleteRecentSearch', { detail: term });
        document.dispatchEvent(event);
    }
};

window.filterByBrand = function (brandName) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = brandName;
        if (typeof performSearch === 'function') {
            performSearch();
        }
        if (typeof saveRecentSearch === 'function') {
            saveRecentSearch(brandName);
        }
    }
    const resultsSection = document.getElementById('cars');
    if (resultsSection) {
        resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
};

window.searchBrand = function (brand) {
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.value = brand;
        if (typeof performSearch === 'function') {
            performSearch();
        }
        if (typeof saveRecentSearch === 'function') {
            saveRecentSearch(brand);
        }
    }
};
//================
// ADDING=PRODUCT
// ===============
document.addEventListener('DOMContentLoaded', () => {
    const productForm = document.getElementById('productForm');
    if (productForm) {
        productForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const name = productForm.querySelector('[name="name"]').value.trim();
            const price = productForm.querySelector('[name="price"]').value;
            const location = productForm.querySelector('[name="location"]').value;
            const phone = productForm.querySelector('[name="phone"]').value;
            const category = productForm.querySelector('[name="category"]').value;
            const stock = productForm.querySelector('[name="stock"]').value;
            const description = productForm.querySelector('[name="description"]').value.trim();
            const spinner = document.getElementById('popupspinner');
            const form = productForm;
            const submitButton = form.querySelector('button[type="submit"]')

            if (!name) {
                showMessage('Product name is required!', 'error');
                return;
            }

            if (!phone) {
                showMessage('Contact is required!', 'error');
                return;
            }

            if (!location) {
                showMessage('Location is required!', 'error');
                return;
            }

            if (!price || price <= 0) {
                showMessage('Valid price is required!', 'error');
                return;
            }

            if (!category) {
                showMessage('Category is required!', 'error');
                return;
            }

            submitButton.disabled = true;
            if (spinner) spinner.classList.add('show');

            const formData = new FormData(productForm);

            try {
                const response = await fetch('/add_product', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    showMessage('Product Added Successfully!', 'success');
                    setTimeout(() => window.location.reload(), 1000);
                } else {
                    showMessage(result.message || 'Failed to add product', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                showMessage('Error Adding Product: ', 'INTERNET UNAVAILABLE', 'error');
            }
            finally {
                submitButton.disabled = false;
                if (spinner) spinner.classList.remove('show');
            }
        });
    }

    function showMessage(msg, type) {
        const messageDiv = document.getElementById('popupmessage');
        if (messageDiv) {
            messageDiv.textContent = msg;
            messageDiv.className = `message ${type} show`;
            messageDiv.style.color = type === 'success' ? '#00ff41' : '#ff4444';
            messageDiv.style.backgroundColor = type === 'success' ? 'rgba(0,255,65,0.1)' : 'rgba(255,68,68,0.1)';
            messageDiv.style.padding = '10px';
            messageDiv.style.borderRadius = '5px';
            messageDiv.style.marginBottom = '15px';
            messageDiv.style.textAlign = 'center';

            setTimeout(() => {
                messageDiv.textContent = '';
                messageDiv.style.padding = '0';
            }, 3000);
        } else {
            alert(msg);
        }
    }
});
//=================
// SIGNIN*-*SIGNUP
//=================
document.addEventListener('DOMContentLoaded', function () {
    const signinFormPopup = document.getElementById('signinFormPopup');

    if (signinFormPopup) {
        signinFormPopup.addEventListener('submit', async function (e) {
            e.preventDefault();

            const email = document.getElementById('popupEmail').value.trim();
            const password = document.getElementById('popupPassword').value;
            const popupErrorMsg = document.getElementById('popupErrorMsg');

            if (!email || !password) {
                if (popupErrorMsg) {
                    popupErrorMsg.textContent = 'Please fill in both email and password';
                    popupErrorMsg.style.display = 'block';
                }
                return;
            }

            if (!email.includes('@') || !email.includes('.com')) {
                if (popupErrorMsg) {
                    popupErrorMsg.textContent = 'Please enter a valid email address';
                    popupErrorMsg.style.display = 'block';
                }
                return;
            }

            const form = signinFormPopup;
            const messageBox = document.getElementById('popupmessageBox');
            const spinner = document.getElementById('popupspinner');
            const submitButton = form.querySelector('button[type="submit"]');

            function showMessage(message, type) {
                if (messageBox) {
                    messageBox.textContent = message;
                    messageBox.className = `message ${type} show`;
                    setTimeout(() => {
                        messageBox.classList.remove('show');
                    }, 3000);
                } else {
                    alert(message);
                }
            }

            submitButton.disabled = true;
            if (spinner) spinner.classList.add('show');

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: email,
                        password: password
                    })
                });

                const data = await response.json();

                if (response.ok && data.success) {
                    const passwordField = document.getElementById('popupPassword');
                    if (passwordField) passwordField.value = '';

                    showMessage(data.message || 'Login successful! Redirecting...', 'success');
                    sessionStorage.setItem('justLoggedIn', 'true');

                    setTimeout(() => {
                        window.location.href = data.redirect || '/dashboard';
                    }, 4000);
                } else {
                    const errorMsg = data.message || data.error || 'Login failed. Please try again.';
                    showMessage(errorMsg, 'error');
                }

            } catch (error) {
                console.error('Login error:', error);
                let errorMessage = 'Connection error. Please try again.';
                showMessage(errorMessage, 'error');

            } finally {
                submitButton.disabled = false;
                if (spinner) spinner.classList.remove('show');
            }
        });
    }
    const openPopupBtn = document.getElementById('openSigninPopup');
    const popupModal = document.getElementById('signinPopup');
    const popupErrorMsg = document.getElementById('popupErrorMsg');

    if (openPopupBtn && popupModal) {
        openPopupBtn.addEventListener('click', function (e) {
            e.preventDefault();
            popupModal.style.display = 'block';
            document.body.style.overflow = 'hidden';

            if (popupErrorMsg) {
                popupErrorMsg.style.display = 'none';
                popupErrorMsg.textContent = '';
            }

            const emailField = document.getElementById('popupEmail');
            const passwordField = document.getElementById('popupPassword');
            if (emailField) emailField.value = '';
            if (passwordField) passwordField.value = '';
        });

        // CLOSE POPUP - Click outside
        window.addEventListener('click', function (e) {
            if (e.target === popupModal) {
                popupModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && popupModal.style.display === 'block') {
                popupModal.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        });
    }

    // SIGNUP FORM
    const signupForm = document.getElementById('signupForm');
    if (signupForm) {
        signupForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const password = signupForm.querySelector('[name="password"]').value;
            const messageBox = document.getElementById('popupmessageS');
            const spinner = document.getElementById('popupspinner');
            const submitButton = signupForm.querySelector('button[type="submit"]');

            submitButton.disabled = true;
            if (spinner) spinner.classList.add('show');

            function showMessage(message, type) {
                if (messageBox) {
                    messageBox.textContent = message;
                    messageBox.className = `message ${type} show`;
                    setTimeout(() => {
                        messageBox.classList.remove('show');
                    }, 3000);
                } else {
                    alert(message);
                }
            }

            try {
                const formData = {
                    business_name: signupForm.querySelector('[name="business_name"]')?.value || '',
                    email: signupForm.querySelector('[name="email"]')?.value,
                    phone: signupForm.querySelector('[name="phone"]')?.value || '',
                    business_type: signupForm.querySelector('[name="business_type"]')?.value,
                    password: password,
                };

                const response = await fetch('/api/signup', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(formData)
                });

                const result = await response.json();

                if (result.success) {
                    showMessage(result.message, 'success');
                    setTimeout(() => {
                        window.location.href = '/dashboard';
                    }, 4000);
                } else {
                    showMessage(result.message, 'error');
                }
            } catch (error) {
                console.error('Signup error:', error);
                showMessage('Error submitting form: ' + error.message, 'error');
            } finally {
                submitButton.disabled = false;
                if (spinner) spinner.classList.remove('show');
            }
        });
    }
});

