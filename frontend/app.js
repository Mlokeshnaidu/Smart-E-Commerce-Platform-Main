const API_URL = "http://127.0.0.1:8000";
const WS_URL = "ws://127.0.0.1:8000";

const AUTH0_DOMAIN = "dev-w2ceyoa7ooqr3uep.us.auth0.com";
const AUTH0_CLIENT_ID = "JPuZNoPRkcYjh01WLJoxRD9bwIhrFPfk";
let auth0Client = null;

let currentUser = null;
let currentToken = localStorage.getItem("accessToken") || "";
let isRegisterMode = false;
let ws = null;
let currentProducts = [];

// Auth0
async function initAuth0() {
    auth0Client = await auth0.createAuth0Client({
        domain: AUTH0_DOMAIN,
        clientId: AUTH0_CLIENT_ID,
        authorizationParams: {
            redirect_uri: window.location.origin,
            scope: "openid profile email"
        }
    });

    if (location.search.includes("code=") && location.search.includes("state=")) {
        await auth0Client.handleRedirectCallback();
        window.history.replaceState({}, document.title, "/");
        await handleAuth0Login();
    }
}

async function loginWithGoogle() {
    await auth0Client.loginWithRedirect({
        authorizationParams: { connection: "google-oauth2" }
    });
}

async function loginWithFacebook() {
    await auth0Client.loginWithRedirect({
        authorizationParams: { connection: "facebook" }
    });
}

async function handleAuth0Login() {
    try {
        const accessToken = await auth0Client.getTokenSilently();
        const idTokenClaims = await auth0Client.getIdTokenClaims();
        const provider = (idTokenClaims && idTokenClaims.sub && idTokenClaims.sub.startsWith("facebook")) ? "facebook" : "google";
        const res = await fetch(`${API_URL}/auth/social-login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ access_token: accessToken, provider: provider }),
        });
        const data = await res.json();
        if (res.ok) {
            currentToken = data.access_token;
            localStorage.setItem("accessToken", currentToken);
            await checkCurrentUser();
            await fetchCart();
            initWebSocket();
            showToast(`Signed in with ${provider === "facebook" ? "Facebook" : "Google"}`, "success");
            closeAuthModal();
        } else {
            showToast(data.detail || "Social sign-in failed", "danger");
        }
    } catch (e) {
        console.error("Auth0 login error:", e);
    }
}

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
    await initAuth0();
    if (!currentToken) {
        // Default login as customer
        await quickLogin("customer@example.com", "Customer");
    } else {
        await checkCurrentUser();
    }
    await fetchProducts();
    await fetchCart();
    initWebSocket();
});

// Auth & Quick Switch
async function quickLogin(email, label) {
    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ email: email, password: "Password123!" }),
        });
        const data = await res.json();
        if (res.ok) {
            currentToken = data.access_token;
            localStorage.setItem("accessToken", currentToken);
            await checkCurrentUser();
            await fetchCart();
            initWebSocket();
            showToast(`Logged in as ${label} (${email})`, "success");
            
            // Update active pill
            document.querySelectorAll(".pill").forEach(p => p.classList.remove("active"));
            event && event.target && event.target.classList.add("active");
        } else {
            showToast(data.detail || "Login failed", "danger");
        }
    } catch (e) {
        console.error(e);
    }
}

async function checkCurrentUser() {
    if (!currentToken) {
        currentUser = null;
        document.getElementById("authStatusText").innerText = "Sign In";
        return;
    }
    try {
        const res = await fetch(`${API_URL}/auth/me`, {
            headers: { "Authorization": `Bearer ${currentToken}` },
        });
        if (res.ok) {
            currentUser = await res.json();
            document.getElementById("authStatusText").innerText = `${currentUser.name} (${currentUser.role})`;
        } else {
            currentToken = "";
            localStorage.removeItem("accessToken");
            document.getElementById("authStatusText").innerText = "Sign In";
        }
    } catch (e) {
        console.error(e);
    }
}

// Product Catalog
async function fetchProducts() {
    const category = document.getElementById("categorySelect").value;
    const maxPrice = document.getElementById("priceRange").value;
    const inStock = document.getElementById("inStockCheck").checked;
    const sortPopularity = document.getElementById("sortPopularityCheck").checked;
    const searchQuery = document.getElementById("searchInput").value.toLowerCase().trim();

    let url = `${API_URL}/products?`;
    if (category) url += `category=${encodeURIComponent(category)}&`;
    if (maxPrice) url += `max_price=${maxPrice}&`;
    if (inStock) url += `in_stock=true&`;
    if (sortPopularity) url += `sort_by_popularity=true&`;

    try {
        const res = await fetch(url);
        let products = await res.json();
        if (searchQuery) {
            products = products.filter(p => p.name.toLowerCase().includes(searchQuery) || (p.description && p.description.toLowerCase().includes(searchQuery)));
        }
        currentProducts = products;
        renderProducts(products);
    } catch (e) {
        console.error("Failed to load products:", e);
    }
}

document.getElementById("searchInput").addEventListener("input", () => {
    fetchProducts();
});

function updatePriceFilter(val) {
    document.getElementById("priceDisplay").innerText = val;
    fetchProducts();
}

function renderProducts(products) {
    const grid = document.getElementById("productGrid");
    if (!products || products.length === 0) {
        grid.innerHTML = `<p class="empty-state" style="grid-column: 1 / -1;">No products found matching the criteria.</p>`;
        return;
    }

    grid.innerHTML = products.map(p => {
        const imgUrl = (p.images && p.images.length > 0) ? p.images[0] : "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600";
        const stockClass = p.stock <= 5 ? "low-stock" : "in-stock";
        const stockText = p.stock === 0 ? "Out of Stock" : (p.stock <= 5 ? `Low Stock (${p.stock})` : `In Stock (${p.stock})`);
        
        return `
            <div class="product-card">
                <img src="${imgUrl}" alt="${p.name}" class="product-image" onerror="this.src='https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=600'">
                <div class="product-body">
                    <span class="product-category">${p.category || 'Product'}</span>
                    <h4 class="product-title">${p.name}</h4>
                    <p class="product-desc">${p.description || ''}</p>
                    <div class="product-footer">
                        <div>
                            <div class="product-price">$${p.price.toFixed(2)}</div>
                            <span class="stock-tag ${stockClass}">${stockText}</span>
                        </div>
                        <button class="btn-add-cart" onclick="addToCart(${p.id})" ${p.stock === 0 ? 'disabled' : ''}>
                            + Add
                        </button>
                    </div>
                </div>
            </div>
        `;
    }).join("");
}

// Shopping Cart
async function fetchCart() {
    if (!currentToken) return;
    try {
        const res = await fetch(`${API_URL}/cart/`, {
            headers: { "Authorization": `Bearer ${currentToken}` }
        });
        if (res.ok) {
            const cart = await res.json();
            renderCart(cart);
        }
    } catch (e) {
        console.error("Failed to load cart:", e);
    }
}

function renderCart(cart) {
    const container = document.getElementById("cartItemsContainer");
    const countBadge = document.getElementById("cartCountBadge");
    
    const items = cart.items || [];
    const totalCount = items.reduce((sum, item) => sum + item.quantity, 0);
    countBadge.innerText = totalCount;

    if (items.length === 0) {
        container.innerHTML = `<p class="empty-state">Your cart is currently empty.</p>`;
        document.getElementById("cartSubtotal").innerText = "$0.00";
        document.getElementById("cartTax").innerText = "$0.00";
        document.getElementById("cartGrandTotal").innerText = "$0.00";
        return;
    }

    container.innerHTML = items.map(item => `
        <div class="cart-item">
            <div class="cart-item-info">
                <div class="cart-item-title">${item.product.name}</div>
                <div class="cart-item-price">$${item.product.price.toFixed(2)} × ${item.quantity} = <strong>$${item.item_total.toFixed(2)}</strong></div>
            </div>
            <div class="cart-qty-controls">
                <button class="qty-btn" onclick="updateCartItem(${item.product.id}, ${item.quantity - 1})">-</button>
                <span>${item.quantity}</span>
                <button class="qty-btn" onclick="updateCartItem(${item.product.id}, ${item.quantity + 1})">+</button>
            </div>
        </div>
    `).join("");

    document.getElementById("cartSubtotal").innerText = `$${cart.cart_total.toFixed(2)}`;
    document.getElementById("cartTax").innerText = `$${cart.tax.toFixed(2)}`;
    document.getElementById("cartGrandTotal").innerText = `$${cart.grand_total.toFixed(2)}`;
}

async function addToCart(productId) {
    if (!currentToken) {
        openAuthModal();
        return;
    }
    try {
        const res = await fetch(`${API_URL}/cart/add`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${currentToken}`,
            },
            body: JSON.stringify({ product_id: productId, quantity: 1 }),
        });
        const data = await res.json();
        if (res.ok) {
            renderCart(data);
            showToast("Added item to cart!", "success");
        } else {
            showToast(data.detail || "Could not add item", "warning");
        }
    } catch (e) {
        console.error(e);
    }
}

async function updateCartItem(productId, quantity) {
    try {
        const res = await fetch(`${API_URL}/cart/update`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${currentToken}`,
            },
            body: JSON.stringify({ product_id: productId, quantity: quantity }),
        });
        const data = await res.json();
        if (res.ok) {
            renderCart(data);
        } else {
            showToast(data.detail || "Update failed", "warning");
        }
    } catch (e) {
        console.error(e);
    }
}

function toggleCartDrawer() {
    document.getElementById("cartDrawer").classList.toggle("open");
}

// Checkout
async function initiateCheckout() {
    if (!currentToken) {
        openAuthModal();
        return;
    }
    const btn = document.getElementById("checkoutBtn");
    btn.disabled = true;
    btn.innerText = "⏳ Processing Stripe Checkout...";

    try {
        const res = await fetch(`${API_URL}/checkout`, {
            method: "POST",
            headers: { "Authorization": `Bearer ${currentToken}` }
        });
        const data = await res.json();
        if (res.ok) {
            showToast(`Order #${data.order_id} created! Stripe checkout initialized.`, "success");
            await fetchCart();
            await fetchProducts();
            toggleCartDrawer();
            
            // Trigger simulated webhook completion for demo
            setTimeout(async () => {
                await simulateStripeWebhook(data.order_id);
            }, 1500);
        } else {
            showToast(data.detail || "Checkout failed", "danger");
        }
    } catch (e) {
        console.error(e);
    } finally {
        btn.disabled = false;
        btn.innerText = "💳 Proceed to Stripe Checkout";
    }
}

async function simulateStripeWebhook(orderId) {
    try {
        const webhookPayload = {
            type: "checkout.session.completed",
            data: {
                object: {
                    metadata: { order_id: String(orderId) }
                }
            }
        };
        await fetch(`${API_URL}/checkout/webhook`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "stripe-signature": "mock_sig" },
            body: JSON.stringify(webhookPayload)
        });
    } catch (e) {
        console.error("Webhook trigger:", e);
    }
}

// WebSockets & Notifications
function initWebSocket() {
    if (!currentToken) return;
    if (ws) {
        ws.close();
    }

    try {
        ws = new WebSocket(`${WS_URL}/ws/notifications?token=${currentToken}`);
        
        ws.onopen = () => {
            console.log("Connected to Live WebSocket Notification Server");
        };

        ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            console.log("WebSocket event:", msg);
            if (msg.event === "order_status_updated") {
                showToast(`🔔 Order #${msg.data.order_id} updated: ${msg.data.status.toUpperCase()}`, "info");
                fetchNotifications();
            } else if (msg.event === "cart_updated") {
                renderCart(msg.data);
            }
        };

        ws.onclose = () => {
            console.log("WebSocket closed");
        };
    } catch (e) {
        console.error("WebSocket error:", e);
    }
}

async function fetchNotifications() {
    if (!currentToken) return;
    try {
        const res = await fetch(`${API_URL}/notifications`, {
            headers: { "Authorization": `Bearer ${currentToken}` }
        });
        if (res.ok) {
            const notifs = await res.json();
            const list = document.getElementById("notifList");
            const badge = document.getElementById("notifBadge");

            const unread = notifs.filter(n => !n.read_status);
            badge.innerText = unread.length;
            badge.classList.toggle("hidden", unread.length === 0);

            if (notifs.length === 0) {
                list.innerHTML = `<p class="empty-state">No notifications recorded</p>`;
                return;
            }

            list.innerHTML = notifs.map(n => `
                <div class="cart-item" style="opacity: ${n.read_status ? 0.6 : 1}">
                    <div class="cart-item-info">
                        <div style="font-size: 0.8rem; font-weight: 700; color: var(--primary); text-transform: uppercase;">${n.type.replace('_', ' ')}</div>
                        <div style="font-size: 0.85rem; margin-top: 2px;">${n.message}</div>
                    </div>
                </div>
            `).join("");
        }
    } catch (e) {
        console.error(e);
    }
}

function toggleNotifications() {
    const drawer = document.getElementById("notifDrawer");
    drawer.classList.toggle("open");
    if (drawer.classList.contains("open")) {
        fetchNotifications();
    }
}

// Toast alerts
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    const toast = document.createElement("div");
    toast.className = "toast";
    
    const icons = { success: "✅", danger: "❌", warning: "⚠️", info: "⚡" };
    toast.innerHTML = `<span>${icons[type] || '⚡'}</span> <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 4000);
}

// Auth Modal
function openAuthModal() {
    document.getElementById("authModal").classList.add("open");
}

function closeAuthModal() {
    document.getElementById("authModal").classList.remove("open");
}

function toggleAuthMode(toRegister) {
    isRegisterMode = toRegister;
    document.getElementById("modalTitle").innerText = isRegisterMode ? "Create Account" : "Account Login";
    document.getElementById("nameGroup").style.display = isRegisterMode ? "block" : "none";
    document.getElementById("submitAuthBtn").innerText = isRegisterMode ? "Register" : "Sign In";
    document.getElementById("toggleAuthModeText").innerHTML = isRegisterMode
        ? `Already have an account? <a href="#" onclick="toggleAuthMode(false)">Sign in</a>`
        : `Don't have an account? <a href="#" onclick="toggleAuthMode(true)">Create one</a>`;
}

async function handleAuthSubmit(event) {
    event.preventDefault();
    const email = document.getElementById("authEmail").value;
    const password = document.getElementById("authPassword").value;
    const name = document.getElementById("authName").value;

    const endpoint = isRegisterMode ? "/auth/register" : "/auth/login";
    const payload = isRegisterMode ? { name, email, password } : { email, password };

    try {
        const res = await fetch(`${API_URL}${endpoint}`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (res.ok) {
            if (isRegisterMode) {
                showToast("Account registered! Signing in...", "success");
                toggleAuthMode(false);
                await quickLogin(email, name);
            } else {
                currentToken = data.access_token;
                localStorage.setItem("accessToken", currentToken);
                await checkCurrentUser();
                await fetchCart();
                initWebSocket();
                showToast("Successfully signed in!", "success");
            }
            closeAuthModal();
        } else {
            showToast(data.detail || "Authentication failed", "danger");
        }
    } catch (e) {
        console.error(e);
    }
}