# Architecture microservices

Architecture cible du projet:

```text
Client (curl/Postman/navigateur)
        |
        v
 API Gateway (Nginx :80)
   |         |         |
   v         v         v
Users      Products   Orders
 :5001      :5002      :5003
   |          |          |
   v          v          v
Users DB   Products DB Orders DB
Postgres   Postgres    Postgres
```

## Reseaux Docker

- `api-network`: `gateway`, `users`, `products`, `orders`
- `users-db-network`: `users`, `users-db`
- `products-db-network`: `products`, `products-db`
- `orders-db-network`: `orders`, `orders-db`

Chaque base est isolee sur son reseau dedie pour eviter l'acces entre bases.

## Flux cle de commande

1. Le client appelle `POST /api/orders` via le gateway.
2. `orders` appelle `products` pour verifier le produit et le stock.
3. `orders` appelle `products` pour reserver (decrementer) le stock.
4. `orders` enregistre la commande avec le `total_price` calcule.
