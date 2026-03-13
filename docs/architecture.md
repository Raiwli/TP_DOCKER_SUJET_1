# Architecture du projet

```
               Client (curl / Postman)
                       |
                       v
               +---------------+
               |  API Gateway  | :80
               |    (Nginx)    |
               +-------+-------+
                       |
        +--------------+--------------+
        v              v              v
  +-----------+  +-----------+  +-----------+
  | Users API |  |Products API| |Orders API |
  |   :5001   |  |   :5002   |  |   :5003   |
  +-----+-----+  +-----+-----+  +-----+-----+
        v              v              v
  +-----------+  +-----------+  +-----------+
  | Users DB  |  |Products DB|  |Orders DB  |
  | PostgreSQL|  |PostgreSQL |  |PostgreSQL |
  +-----------+  +-----------+  +-----------+
```

## Reseaux Docker

- `frontend` : Gateway + les 3 services API
- `users-network` : Users API + Users DB
- `products-network` : Products API + Products DB
- `orders-network` : Orders API + Orders DB

## Communication inter-services

Le service Orders appelle le service Products pour :
- Verifier l'existence d'un produit
- Verifier le stock disponible
- Recuperer le prix pour calculer le total
- Decrementer le stock apres commande
