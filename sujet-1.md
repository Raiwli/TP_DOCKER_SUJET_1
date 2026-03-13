#  Projet Docker — "Microservices from Scratch"

## Système de e-commerce simplifié

---

## Contexte

Vous êtes une équipe de 2 développeurs. Votre client souhaite une plateforme e-commerce simplifiée, construite en **architecture microservices** et entièrement **conteneurisée avec Docker**.

Chaque service doit être **indépendant**, avoir **sa propre base de données**, et l'ensemble doit être orchestré via **Docker Compose**.

> **Durée** : 4h
> **Binôme** : Étudiant A + Étudiant B
> **Langage** : libre (Python/Flask, Node/Express, Go, etc.)

---

## Architecture cible

```
┌─────────────────────────────────────────────────────┐
│           CLIENT (curl/Postman/navigateur)          │
│                           │                         │
│                           ▼                         │
│                   ┌───────────────┐                 │
│                   │  API Gateway  │ :80             │
│                   │    (Nginx)    │                 │
│                   └───────┬───────┘                 │
│                           │                         │
│            ┌──────────────┼──────────────┐          │
│            ▼              ▼              ▼          │
│   ┌────────────┐  ┌─────────────┐  ┌───────────┐    │
│   │  Users API │  │ Products API│  │ Orders API│    │
│   │   :5001    │  │    :5002    │  │   :5003   │    │
│   └─────┬──────┘  └──────┬──────┘  └─────┬─────┘    │
│         ▼                ▼                ▼         │
│   ┌──────────┐    ┌──────────┐     ┌──────────┐     │
│   │  DB Users│    │DB Products│    │DB Orders │     │
│   │ Postgres │    │ Postgres  │    │ Postgres │     │
│   └──────────┘    └──────────┘     └──────────┘     │
│                                                     │
│   Réseau Docker : ecommerce-network                 │
└─────────────────────────────────────────────────────┘
```
---

## Répartition du travail

### Étudiant A — Services métier

#### Service "Products" (port 5002)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/products` | Lister tous les produits |
| GET | `/products/{id}` | Détail d'un produit |
| POST | `/products` | Créer un produit |
| PUT | `/products/{id}` | Modifier un produit |
| DELETE | `/products/{id}` | Supprimer un produit |
| GET | `/health` | Healthcheck |

**Modèle de données produit** : id, name, price, stock, created_at

#### Service "Orders" (port 5003)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/orders` | Lister toutes les commandes |
| GET | `/orders/{id}` | Détail d'une commande |
| POST | `/orders` | Créer une commande |
| GET | `/orders/user/{user_id}` | Commandes d'un utilisateur |
| GET | `/health` | Healthcheck |

**Modèle de données commande** : id, user_id, product_id, quantity, total_price, status, created_at

> **⚠️ Contrainte importante** : lors de la création d'une commande, le service Orders doit **appeler le service Products** via le réseau Docker pour :
> - Vérifier que le produit existe
> - Vérifier que le stock est suffisant
> - Récupérer le prix pour calculer le total
> - Décrémenter le stock

---

### Étudiant B — Utilisateurs & Infrastructure

#### Service "Users" (port 5001)

| Méthode | Route | Description |
|---------|-------|-------------|
| GET | `/users` | Lister tous les utilisateurs |
| GET | `/users/{id}` | Détail d'un utilisateur |
| POST | `/users` | Créer un utilisateur |
| PUT | `/users/{id}` | Modifier un utilisateur |
| DELETE | `/users/{id}` | Supprimer un utilisateur |
| POST | `/users/login` | Authentification simple |
| GET | `/health` | Healthcheck |

**Modèle de données utilisateur** : id, username, email, password_hash, created_at

#### API Gateway (Nginx)

- Seul point d'entrée exposé sur le port **80**
- Route `/api/users` → service Users
- Route `/api/products` → service Products
- Route `/api/orders` → service Orders
- Les services API ne doivent **PAS** être accessibles directement depuis l'extérieur

---

## Exigences techniques Docker

### Dockerfile (chaque service)

Chaque Dockerfile **doit** respecter ces bonnes pratiques :
- Image de base légère (alpine ou slim)
- Utilisateur non-root
- `.dockerignore` présent
- `HEALTHCHECK` défini
- Labels (maintainer, version)
- `EXPOSE` déclaré

### compose.yaml

- **Réseaux séparés** : les bases de données ne doivent pas être accessibles entre elles
- **Volumes nommés** pour la persistance de chaque BDD
- **Variables d'environnement** via un fichier `.env` (pas de secrets en dur)
- **depends_on** avec `condition: service_healthy`
- **restart: unless-stopped** sur chaque service
- **Healthchecks** sur chaque base de données et chaque API

---

## 📦 Rendu

- **Repo Git** avec tout le code source
- **compose.yaml** fonctionnel (un seul `docker compose up` doit tout lancer)
- **README.md** avec instructions de lancement
- **Schéma d'architecture** (dans `/docs`)
- **Documentation des API** (dans `/docs`)

---

## 🌟 Bonus

| Bonus | Points |
|---|---|
| Cache Redis pour les produits | +1 |
| Tests automatisés dans un conteneur | +1 |
| Frontend simple (même une page HTML) | +1 |
| Logs centralisés | +1 |
| Multi-stage build (image < 100 Mo) | +1 |
| Script de seed pour peupler les BDD | +1 |