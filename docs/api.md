# Documentation API

Base URL : `http://localhost/api`

---

## Users Service (`/api/users`)

### GET /api/users
Liste tous les utilisateurs.

### GET /api/users/{id}
Detail d'un utilisateur.

### POST /api/users
Creer un utilisateur.
```json
{
  "username": "john",
  "email": "john@example.com",
  "password": "secret123"
}
```

### PUT /api/users/{id}
Modifier un utilisateur.
```json
{
  "username": "john_updated",
  "email": "john_new@example.com"
}
```

### DELETE /api/users/{id}
Supprimer un utilisateur.

### POST /api/users/login
Authentification.
```json
{
  "username": "john",
  "password": "secret123"
}
```

---

## Products Service (`/api/products`)

### GET /api/products
Liste tous les produits.

### GET /api/products/{id}
Detail d'un produit.

### POST /api/products
Creer un produit.
```json
{
  "name": "Laptop",
  "price": 999.99,
  "stock": 50
}
```

### PUT /api/products/{id}
Modifier un produit.
```json
{
  "name": "Laptop Pro",
  "price": 1299.99,
  "stock": 30
}
```

### DELETE /api/products/{id}
Supprimer un produit.

---

## Orders Service (`/api/orders`)

### GET /api/orders
Liste toutes les commandes.

### GET /api/orders/{id}
Detail d'une commande.

### POST /api/orders
Creer une commande.
```json
{
  "user_id": 1,
  "product_id": 1,
  "quantity": 2
}
```

### GET /api/orders/user/{user_id}
Commandes d'un utilisateur.
