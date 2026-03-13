const state = {
  products: [],
  users: [],
  orders: [],
};

const tabs = document.querySelectorAll(".tab");
const views = {
  client: document.getElementById("view-client"),
  admin: document.getElementById("view-admin"),
};

const healthPillEl = document.getElementById("health-pill");
const productsEl = document.getElementById("products");
const productsCountEl = document.getElementById("products-count");
const ordersClientEl = document.getElementById("orders-client");

const userFeedbackEl = document.getElementById("user-feedback");
const orderFeedbackEl = document.getElementById("order-feedback");
const adminProductFeedbackEl = document.getElementById("admin-product-feedback");
const adminUserFeedbackEl = document.getElementById("admin-user-feedback");
const adminOrderFeedbackEl = document.getElementById("admin-order-feedback");

const userForm = document.getElementById("user-form");
const orderForm = document.getElementById("order-form");
const adminProductForm = document.getElementById("admin-product-form");
const adminUserForm = document.getElementById("admin-user-form");
const adminOrderForm = document.getElementById("admin-order-form");

const productsAdminTableEl = document.getElementById("products-admin-table");
const usersAdminTableEl = document.getElementById("users-admin-table");
const ordersAdminTableEl = document.getElementById("orders-admin-table");

const kpiProductsEl = document.getElementById("kpi-products");
const kpiUsersEl = document.getElementById("kpi-users");
const kpiOrdersEl = document.getElementById("kpi-orders");
const kpiRevenueEl = document.getElementById("kpi-revenue");
const kpiStockAlertEl = document.getElementById("kpi-stock-alert");

const ordersFilterInput = document.getElementById("orders-filter-user");

function formatDate(value) {
  return new Date(value).toLocaleString("fr-FR");
}

function formatPrice(value) {
  return new Intl.NumberFormat("fr-FR", {
    style: "currency",
    currency: "EUR",
    minimumFractionDigits: 2,
  }).format(value);
}

function setFeedback(el, message, isError = false) {
  el.textContent = message;
  el.className = `feedback ${isError ? "bad" : "ok"}`;
}

async function requestJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const hasBody = response.status !== 204;
  const isJson = response.headers.get("content-type")?.includes("application/json");
  const data = hasBody && isJson ? await response.json() : null;

  if (!response.ok) {
    throw new Error(data?.error || `Erreur HTTP ${response.status}`);
  }

  return data;
}

function switchView(viewName) {
  tabs.forEach((tab) => tab.classList.toggle("active", tab.dataset.view === viewName));
  Object.entries(views).forEach(([name, el]) => {
    el.classList.toggle("active", name === viewName);
  });
}

function renderClientProducts() {
  productsCountEl.textContent = `${state.products.length} pizza${state.products.length > 1 ? "s" : ""}`;

  if (!state.products.length) {
    productsEl.innerHTML = "<p class='muted'>Aucun produit disponible.</p>";
    return;
  }

  productsEl.innerHTML = "";
  state.products.forEach((product) => {
    const card = document.createElement("article");
    card.className = "card";
    card.innerHTML = `
      <h3>${product.name}</h3>
      <span class="tag">Taille ${product.size}</span>
      <p class="price">${formatPrice(product.price)}</p>
      <p class="muted">Stock: ${product.stock}</p>
      <button class="btn btn-ghost" type="button">Commander cette pizza</button>
    `;
    card.querySelector("button").addEventListener("click", () => {
      orderForm.product_id.value = product.id;
      orderForm.quantity.focus();
    });
    productsEl.appendChild(card);
  });
}

function renderClientOrders() {
  if (!state.orders.length) {
    ordersClientEl.innerHTML = "<p class='muted'>Aucune commande pour le moment.</p>";
    return;
  }

  ordersClientEl.innerHTML = "";
  state.orders
    .slice()
    .reverse()
    .slice(0, 8)
    .forEach((order) => {
      const el = document.createElement("article");
      el.className = "item";
      el.innerHTML = `
        <strong>Commande #${order.id}</strong><br>
        User ${order.user_id} · Produit ${order.product_id} · Quantite ${order.quantity}<br>
        Total ${formatPrice(order.total_price)} · Statut ${order.status}
      `;
      ordersClientEl.appendChild(el);
    });
}

function renderAdminProductsTable() {
  if (!state.products.length) {
    productsAdminTableEl.innerHTML = "<tr><td colspan='5'>Aucun produit</td></tr>";
    return;
  }

  productsAdminTableEl.innerHTML = state.products
    .map(
      (p) => `<tr>
        <td>${p.id}</td>
        <td>${p.name}</td>
        <td>${p.size}</td>
        <td>${formatPrice(p.price)}</td>
        <td>${p.stock}</td>
      </tr>`
    )
    .join("");
}

function renderAdminUsersTable() {
  if (!state.users.length) {
    usersAdminTableEl.innerHTML = "<tr><td colspan='4'>Aucun user</td></tr>";
    return;
  }

  usersAdminTableEl.innerHTML = state.users
    .map(
      (u) => `<tr>
        <td>${u.id}</td>
        <td>${u.username}</td>
        <td>${u.email}</td>
        <td>${formatDate(u.created_at)}</td>
      </tr>`
    )
    .join("");
}

function renderAdminOrdersTable(orders = state.orders) {
  if (!orders.length) {
    ordersAdminTableEl.innerHTML = "<tr><td colspan='6'>Aucune commande</td></tr>";
    return;
  }

  ordersAdminTableEl.innerHTML = orders
    .map(
      (o) => `<tr>
        <td>${o.id}</td>
        <td>${o.user_id}</td>
        <td>${o.product_id}</td>
        <td>${o.quantity}</td>
        <td>${formatPrice(o.total_price)}</td>
        <td>${o.status}</td>
      </tr>`
    )
    .join("");
}

function renderAdminKpi() {
  const revenue = state.orders.reduce((sum, order) => sum + Number(order.total_price || 0), 0);
  const lowStock = state.products.filter((p) => p.stock <= 3);

  kpiProductsEl.textContent = String(state.products.length);
  kpiUsersEl.textContent = String(state.users.length);
  kpiOrdersEl.textContent = String(state.orders.length);
  kpiRevenueEl.textContent = formatPrice(revenue);

  if (!lowStock.length) {
    kpiStockAlertEl.textContent = "Alerte stock: aucune pizza en stock faible.";
  } else {
    const names = lowStock.map((p) => `${p.name}(${p.stock})`).join(", ");
    kpiStockAlertEl.textContent = `Alerte stock: ${names}`;
  }
}

async function loadHealth() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      throw new Error("Gateway indisponible");
    }
    healthPillEl.textContent = "API: en ligne";
    healthPillEl.style.color = "#5adb91";
  } catch {
    healthPillEl.textContent = "API: hors ligne";
    healthPillEl.style.color = "#ff7f72";
  }
}

async function loadProducts() {
  state.products = await requestJson("/api/products");
  renderClientProducts();
  renderAdminProductsTable();
}

async function loadUsers() {
  state.users = await requestJson("/api/users");
  renderAdminUsersTable();
}

async function loadOrders() {
  state.orders = await requestJson("/api/orders");
  renderClientOrders();
  renderAdminOrdersTable();
  renderAdminKpi();
}

async function loadAllData() {
  try {
    await Promise.all([loadProducts(), loadUsers(), loadOrders(), loadHealth()]);
    renderAdminKpi();
  } catch (error) {
    setFeedback(orderFeedbackEl, error.message, true);
  }
}

tabs.forEach((tab) => {
  tab.addEventListener("click", () => switchView(tab.dataset.view));
});

userForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFeedback(userFeedbackEl, "Creation en cours...");

  const payload = {
    username: userForm.username.value.trim(),
    email: userForm.email.value.trim(),
    password: userForm.password.value,
  };

  try {
    const created = await requestJson("/api/users", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setFeedback(userFeedbackEl, `Compte cree. User ID: ${created.id}`);
    userForm.reset();
    await loadUsers();
  } catch (error) {
    setFeedback(userFeedbackEl, error.message, true);
  }
});

orderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  setFeedback(orderFeedbackEl, "Commande en cours...");

  const payload = {
    user_id: Number(orderForm.user_id.value),
    product_id: Number(orderForm.product_id.value),
    quantity: Number(orderForm.quantity.value),
  };

  try {
    const created = await requestJson("/api/orders", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setFeedback(orderFeedbackEl, `Commande #${created.id} confirmee. Total ${formatPrice(created.total_price)}`);
    await Promise.all([loadOrders(), loadProducts()]);
  } catch (error) {
    setFeedback(orderFeedbackEl, error.message, true);
  }
});

adminProductForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = adminProductForm.id.value.trim();
  const payload = {
    name: adminProductForm.name.value.trim(),
    size: adminProductForm.size.value,
    price: Number(adminProductForm.price.value),
    stock: Number(adminProductForm.stock.value),
  };

  try {
    if (id) {
      await requestJson(`/api/products/${id}`, {
        method: "PUT",
        body: JSON.stringify(payload),
      });
      setFeedback(adminProductFeedbackEl, `Produit ${id} mis a jour.`);
    } else {
      const created = await requestJson("/api/products", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setFeedback(adminProductFeedbackEl, `Produit cree avec ID ${created.id}.`);
    }
    await loadProducts();
    renderAdminKpi();
  } catch (error) {
    setFeedback(adminProductFeedbackEl, error.message, true);
  }
});

document.getElementById("delete-product-btn").addEventListener("click", async () => {
  const id = adminProductForm.id.value.trim();
  if (!id) {
    setFeedback(adminProductFeedbackEl, "Saisis un Product ID pour suppression.", true);
    return;
  }
  if (!window.confirm(`Supprimer le produit ${id} ?`)) {
    return;
  }

  try {
    await requestJson(`/api/products/${id}`, { method: "DELETE" });
    setFeedback(adminProductFeedbackEl, `Produit ${id} supprime.`);
    await loadProducts();
    renderAdminKpi();
  } catch (error) {
    setFeedback(adminProductFeedbackEl, error.message, true);
  }
});

adminUserForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = adminUserForm.id.value.trim();

  const payload = {};
  if (adminUserForm.username.value.trim()) payload.username = adminUserForm.username.value.trim();
  if (adminUserForm.email.value.trim()) payload.email = adminUserForm.email.value.trim();
  if (adminUserForm.password.value) payload.password = adminUserForm.password.value;

  if (!Object.keys(payload).length) {
    setFeedback(adminUserFeedbackEl, "Aucune valeur a mettre a jour.", true);
    return;
  }

  try {
    await requestJson(`/api/users/${id}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    });
    setFeedback(adminUserFeedbackEl, `User ${id} mis a jour.`);
    adminUserForm.password.value = "";
    await loadUsers();
    renderAdminKpi();
  } catch (error) {
    setFeedback(adminUserFeedbackEl, error.message, true);
  }
});

document.getElementById("delete-user-btn").addEventListener("click", async () => {
  const id = adminUserForm.id.value.trim();
  if (!id) {
    setFeedback(adminUserFeedbackEl, "Saisis un User ID pour suppression.", true);
    return;
  }
  if (!window.confirm(`Supprimer le user ${id} ?`)) {
    return;
  }

  try {
    await requestJson(`/api/users/${id}`, { method: "DELETE" });
    setFeedback(adminUserFeedbackEl, `User ${id} supprime.`);
    await loadUsers();
    renderAdminKpi();
  } catch (error) {
    setFeedback(adminUserFeedbackEl, error.message, true);
  }
});

adminOrderForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = adminOrderForm.id.value.trim();
  const status = adminOrderForm.status.value;

  try {
    await requestJson(`/api/orders/${id}`, {
      method: "PUT",
      body: JSON.stringify({ status }),
    });
    setFeedback(adminOrderFeedbackEl, `Order ${id} passe en ${status}.`);
    await loadOrders();
  } catch (error) {
    setFeedback(adminOrderFeedbackEl, error.message, true);
  }
});

document.getElementById("delete-order-btn").addEventListener("click", async () => {
  const id = adminOrderForm.id.value.trim();
  if (!id) {
    setFeedback(adminOrderFeedbackEl, "Saisis un Order ID pour suppression.", true);
    return;
  }
  if (!window.confirm(`Supprimer la commande ${id} ?`)) {
    return;
  }

  try {
    await requestJson(`/api/orders/${id}`, { method: "DELETE" });
    setFeedback(adminOrderFeedbackEl, `Commande ${id} supprimee.`);
    await loadOrders();
  } catch (error) {
    setFeedback(adminOrderFeedbackEl, error.message, true);
  }
});

document.getElementById("refresh-all").addEventListener("click", loadAllData);
document.getElementById("refresh-orders-client").addEventListener("click", loadOrders);
document.getElementById("refresh-admin").addEventListener("click", () => {
  renderAdminKpi();
  setFeedback(adminOrderFeedbackEl, "Dashboard admin actualise.");
});
document.getElementById("refresh-products-admin").addEventListener("click", loadProducts);
document.getElementById("refresh-users-admin").addEventListener("click", loadUsers);
document.getElementById("refresh-orders-admin").addEventListener("click", async () => {
  await loadOrders();
  ordersFilterInput.value = "";
});
document.getElementById("filter-orders-admin").addEventListener("click", async () => {
  const userId = Number(ordersFilterInput.value);
  if (!userId) {
    renderAdminOrdersTable();
    return;
  }

  try {
    const filtered = await requestJson(`/api/orders/user/${userId}`);
    renderAdminOrdersTable(filtered);
  } catch (error) {
    setFeedback(adminOrderFeedbackEl, error.message, true);
  }
});

loadAllData();
