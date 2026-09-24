# Détails : Sécurité, rôles et utilisateurs

## Stratégie d'authentification et RBAC (Role-Based Access Control)
Ce projet implémente une architecture de sécurité où les rôles applicatifs ne sont pas stockés dans une colonne de la table `User`, mais sont directement calqués sur les **rôles système d'Oracle Database**.

1. **Authentification** : L'utilisateur s'authentifie sur l'API avec son email et son mot de passe (haché via Argon2id dans la table `app_users`).
2. **Autorisation** : Lors de la connexion, l'API interroge le catalogue Oracle (`DBA_ROLE_PRIVS`) pour récupérer les privilèges système accordés à cet utilisateur.
3. **Session (JWT)** : Les rôles Oracle récupérés sont scellés dans le token JWT pour sécuriser les routes (Stateless).

## Rôles Oracle et privilèges

### Rôle : `APP_USER` (Utilisateur standard)
* **Droits Oracle (GRANT)** : `SELECT` sur les tables `books` et `authors`. `SELECT`, `INSERT`, `UPDATE` sur `rent_books`.
* **Droits API** :
  - S'authentifier.
  - Lister / Rechercher des livres et consulter leurs détails (disponibilité).
  - Emprunter un livre (crée une entrée dans `rent_books`).
  - Retourner un livre (met à jour `dateEnd` dans `rent_books`).
  - Consulter son propre historique d'emprunts.

### Rôle : `APP_ADMIN` (Administrateur)
* **Droits Oracle (GRANT)** : `SELECT`, `INSERT`, `UPDATE`, `DELETE` sur **toutes** les tables de l'application.
* **Droits API** :
  - *Tous les droits de l'utilisateur standard.*
  - Gérer les utilisateurs (CRUD complet + mise sur liste noire).
  - Gérer le catalogue de livres et d'auteurs (CRUD complet).
  - Superviser la totalité des emprunts de la bibliothèque.
  - Visualiser le stock total (`stockTot`) en plus du stock disponible (`stock`).

## Comptes de test par défaut

| Profil | Email (Login API) | Mot de passe API | Compte Oracle | Rôle Oracle accordé |
| :--- | :--- | :--- | :--- | :--- |
| **Administrateur** | `alice@admin.com` | `secret` | `alice` | `APP_ADMIN` |
| **Utilisateur** | `bob@user.com` | `secret` | `bob` | `APP_USER` |