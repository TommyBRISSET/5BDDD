# Spécification des besoins

Ce document récapitule les fonctionnalités attendues par profil utilisateur ainsi que les règles de gestion métier associées.

---

## 1. Besoins par rôle

### Utilisateur standard (`APP_USER`)
- **Authentification** : S'authentifier sur l'application (`Login`).
- **Recherche & Consultation** :
  - Rechercher des livres dans le catalogue.
  - Consulter les détails d'un livre (avec son stock disponible en temps réel).
- **Gestion des emprunts** :
  - Emprunter un livre (si le stock disponible est supérieur à 0).
  - Retourner un livre (uniquement s'il a été emprunté par l'utilisateur connecté).
  - Consulter son historique personnel d'emprunts.

### Administrateur (`APP_ADMIN`)
- *Possède l'ensemble des capacités de l'utilisateur standard.*
- **Gestion des utilisateurs** : Ajouter, modifier et supprimer des comptes.
- **Gestion de la liste noire** : Mettre ou retirer des utilisateurs de la blacklist (bloquant l'accès à l'application).
- **Gestion du catalogue** : Ajouter, modifier et supprimer des livres et des auteurs.
- **Supervision & Historique** : Consulter l'historique global de tous les emprunts de la bibliothèque.
- **Gestion des stocks** : Visualiser le stock total (`stockTot`) en plus du stock disponible (`stock`) pour chaque livre.

---

## 2. Règles de gestion métier (RG)

| Identifiant | Règle de gestion | Description / Contrainte |
| :--- | :--- | :--- |
| **RG-1** | Décrémentation du stock | L'emprunt d'un livre décrémente son stock disponible (`stock`) de 1. |
| **RG-2** | Incrémentation du stock | Le retour d'un livre incrémente son stock disponible (`stock`) de 1. |
| **RG-3** | Disponibilité à l'emprunt | Impossible d'emprunter un livre dont le stock disponible est à 0. |
| **RG-4** | Restriction de retour | Impossible de retourner un livre qui n'est pas lié à l'utilisateur en cours ou déjà restitué. |
