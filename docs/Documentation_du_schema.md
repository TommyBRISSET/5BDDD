# Schéma de la base de données

Ce document décrit la structure détaillée des tables, des relations et des entités de la base de données.

---

## 1. Diagramme Entité-Association (ERD)

![Schéma de la base de données](schema_bdd.png)

---

## 2. Description des entités

### Table : `authors` (`Author`)
Stocke les informations relatives aux auteurs des livres.

| Colonne | Type | Contraintes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK**, Auto-incrément (`authors_id_seq`) | Identifiant unique de l'auteur |
| `surname` | `String(50)` | Not Null | Prénom de l'auteur |
| `family_name` | `String(50)` | Not Null | Nom de famille de l'auteur |

---

### Table : `books` (`Book`)
Catalogue des ouvrages disponibles dans la bibliothèque.

| Colonne | Type | Contraintes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK**, Auto-incrément (`books_id_seq`) | Identifiant unique du livre |
| `name` | `String(150)` | Not Null | Titre du livre |
| `description` | `String(500)` | Nullable | Résumé ou description de l'ouvrage |
| `stockTot` | `Integer` | Not Null (défaut `0`) | Quantité totale possédée par la bibliothèque |
| `stock` | `Integer` | Not Null (défaut `0`) | Quantité actuellement disponible en rayon |
| `genre` | `String(50)` | Nullable | Catégorie littéraire / genre |
| `editor` | `String(100)` | Nullable | Maison d'édition |
| `id_author` | `Integer` | **FK** (`authors.id`), Not Null | Référence vers l'auteur du livre |

---

### Table : `app_users` (`User`)
Comptes utilisateurs et administrateurs accédant à l'application.

| Colonne | Type | Contraintes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK**, Auto-incrément (`app_users_id_seq`) | Identifiant unique de l'utilisateur |
| `email` | `String(150)` | **Unique**, Not Null | Adresse email (identifiant de connexion) |
| `password` | `String(255)` | Not Null | Mot de passe haché (Argon2id) |
| `surname` | `String(50)` | Not Null | Prénom |
| `family_name` | `String(50)` | Not Null | Nom de famille |
| `blacklist` | `Boolean` | Not Null (défaut `False`) | Indicateur de liste noire (si `True`, accès bloqué) |

---

### Table : `rent_books` (`RentBook`)
Historique et suivi des emprunts de livres.

| Colonne | Type | Contraintes | Description |
| :--- | :--- | :--- | :--- |
| `id` | `Integer` | **PK**, Auto-incrément (`rent_books_id_seq`) | Identifiant unique de l'emprunt |
| `id_book` | `Integer` | **FK** (`books.id`), Not Null | Référence vers le livre emprunté |
| `id_user` | `Integer` | **FK** (`app_users.id`), Not Null | Référence vers l'utilisateur emprunteur |
| `dateBeginRen` | `DateTime` | Not Null (défaut `now()`) | Date et heure de début de l'emprunt |
| `dateEnd` | `DateTime` | Nullable | Date et heure de retour (si `NULL`, emprunt en cours) |
