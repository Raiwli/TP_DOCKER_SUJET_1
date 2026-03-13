# Documentation API

Base URL publique: `http://localhost`

## Users

- `GET /api/users`
- `GET /api/users/{id}`
- `POST /api/users`
- `PUT /api/users/{id}`
- `DELETE /api/users/{id}`
- `POST /api/users/login`
- `GET /api/users/health`

### Exemple creation user

```json
{
  "username": "hugo",
  "email": "hugo@example.com",
  "password": "secret123"
}
```

## Products

- `GET /api/products`
- `GET /api/products/{id}`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`
- `GET /api/products/health`

Route interne utilisee par Orders:

- `POST /products/{id}/reserve` (appel service-to-service)

### Regles metier produit

- `name`: prenom humain (chaine)
- `size`: `U9`, `U12`, `U15`
- `price`: `>= 1000 EUR`
- `stock`: entier `>= 0`

### Exemple creation produit

```json
{
  "name": "Kevin",
  "size": "U12",
  "price": 1999.99,
  "stock": 12
}
```

## Orders

- `GET /api/orders`
- `GET /api/orders/{id}`
- `GET /api/orders/user/{user_id}`
- `POST /api/orders`
- `GET /api/orders/health`

### Exemple creation commande

```json
{
  "user_id": 1,
  "product_id": 2,
  "quantity": 3
}
```

`orders` valide le produit, verifie le stock, recupere le prix, decremente le stock puis enregistre la commande.
