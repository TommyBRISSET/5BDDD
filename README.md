# Système de gestion de bibliothèque — API REST (FastAPI & Oracle RBAC)

Cette API REST assure la gestion d'une bibliothèque. Développée avec **FastAPI** et **Oracle Database**, la gestion des habilitations (RBAC) repose sur les **rôles systèmes natifs d'Oracle** (`APP_USER`, `APP_ADMIN`). Ces rôles sont interrogés via le dictionnaire de données et intégrés dans un token **JWT**, remplaçant ainsi l'usage d'une colonne applicative dédiée aux rôles.

## 1. Fonctionnalités et règles métier

L'application implémente deux niveaux d'habilitation.

### Utilisateur standard (`APP_USER`)
- **Authentification** : Sécurisée par JWT (mots de passe hachés via Argon2id).
- **Consultation** : Recherche de livres et affichage de la disponibilité en temps réel (`stock`).
- **Emprunts** : 
  - Décrémentation automatique du stock lors de l'emprunt.
  - Action bloquée si le stock disponible est de 0.
- **Retours** : 
  - Incrémentation du stock lors de la restitution.
  - Impossible de rendre un livre non emprunté par l'utilisateur ou déjà restitué.
- **Historique** : Consultation limitée aux emprunts de l'utilisateur actif.

### Administrateur (`APP_ADMIN`)
- *Hérite des droits de l'utilisateur standard.*
- **Gestion des utilisateurs** : Création, modification et mise sur liste noire (bloquant l'accès à l'API).
- **Gestion du catalogue** : Création, modification et suppression de livres et d'auteurs.
- **Supervision** : Accès à l'historique global des emprunts.
- **Gestion des stocks** : Accès à la quantité totale de livres (`stockTot`), une donnée qui reste masquée pour les utilisateurs standards.

---

## 2. Architecture et base de données

### Schéma de la base de données
Le modèle relationnel illustre les entités et relations nécessaires au respect des règles de gestion.

![schema_bdd.png](docs/schema_bdd.png)

### Architecture technique
Le processus d'initialisation (IaC) sépare la création de la structure de données (Alembic) de l'attribution des droits systèmes Oracle (`init_roles.py`).

![architecture.png](docs/architecture.png)

---

## 3. Prérequis

- **Python** : 3.10 ou supérieur.
- **Oracle Database** : Instance fonctionnelle et accessible (ex: `localhost:1521`, service `FREEPDB1`).

> **Option Docker (Oracle Database 23c Free) :** Vous pouvez lancer une instance Oracle Database via Docker avec la commande suivante :
> ```powershell
> docker run -d --name oracle23c -p 1521:1521 -e ORACLE_PWD=mot_de_passe container-registry.oracle.com/database/free:latest
> ```
> *(Patientez 5 minutes après le lancement pour que la base et le service `FREEPDB1` soient complètement initialisés).*

---

## 4. Installation et démarrage

### 4.1. Configuration de l'environnement
Clonage du dépôt, création de l'environnement virtuel et installation des dépendances :
```powershell
git clone https://github.com/TommyBRISSET/5BDDD.git
cd 5BDDD
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4.2. Configuration du schéma et de l'utilisateur Oracle applicatif

Pour des raisons de sécurité, nous n'utilisons pas le compte d'administration `SYS` pour faire fonctionner l'application. Créez un utilisateur applicatif dédié (ex: `test`) dans la base (`FREEPDB1`) :

1. Connectez-vous avec `sqlplus` dans le conteneur en tant que `SYS` :
```powershell
docker exec -it oracle23c sqlplus sys/mot_de_passe@localhost:1521/FREEPDB1 as sysdba
```

2. Exécutez les instructions SQL suivantes pour créer l'utilisateur et lui attribuer les droits nécessaires :
```sql
-- Création de l'utilisateur applicatif
CREATE USER test IDENTIFIED BY "mot_de_passe"
  DEFAULT TABLESPACE users
  QUOTA UNLIMITED ON users;

-- Privilèges de base et création des objets
GRANT CONNECT, RESOURCE, CREATE VIEW, CREATE SEQUENCE, CREATE TABLE TO test;

-- Privilèges pour la gestion dynamique des rôles et l'interrogation du catalogue (RBAC)
GRANT CREATE ROLE, DROP ANY ROLE, GRANT ANY ROLE TO test;
GRANT CREATE USER, DROP USER, GRANT ANY PRIVILEGE TO test;
GRANT SELECT_CATALOG_ROLE TO test;

EXIT;
```

### 4.3. Variables d'environnement

Création du fichier `.env` à la racine à partir de l'exemple fourni (`.env.example`) :
```powershell
APP_NAME="Projet FastAPI"
DEBUG=True
DATABASE_URL="oracle+oracledb://test:mot_de_passe@localhost:1521/?service_name=FREEPDB1"
API_KEY="secret-token-12345"
PORT=8000
JWT_SECRET_KEY="Mettre_un_token"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=30
```

### 4.4. Initialisation de la base de données
Le déploiement de la base s'effectue en deux étapes pour garantir l'ordre de création des objets dans Oracle.

**Étape 1 :** Création des tables et séquences (Alembic)
```powershell
alembic upgrade head
```

**Étape 2 :** Création des rôles, droits et jeux d'essai (Script Python)
```powershell
python -m app.roles.init_roles
```
_Note : Ce script configure les rôles `app_user` et `app_admin`, applique les privilèges (`GRANT`) et crée les comptes de test._

### 4.5. Lancement du serveur
```powershell
uvicorn app.main:app --reload
```

L'API et la documentation Swagger sont accessibles à l'adresse : http://127.0.0.1:8000

### 4.6 Erreur de login/mdp

Si vous rencontrez une erreur de login ou de mot de passe, effectuez cette commande :
```powershell
python -c "from pwdlib import PasswordHash; print(PasswordHash.recommended().hash('secret'))"
```

Modifiez ensuite le fichier `app/roles/init_roles.py` pour utiliser le mot de passe hashé généré.

Refaire la commande suivante :
```powershell
python -m app.roles.init_roles
```

---

## 5. Tests automatisés (Pytest)
Le projet inclut une suite de 20 tests automatisés vérifiant la validité des tokens JWT, l'application du contrôle d'accès (RBAC) et la logique métier des stocks et emprunts.

Exécution de la suite de tests :
```powershell
python -m pytest -v tests/test_main.py
```

---

## 6. Comptes de test fournis

| Profil | Email de connexion | Mot de passe | Rôle Oracle attribué |
| :--- | :--- | :--- | :--- |
| **Administrateur** | `alice@admin.com` | `secret` | `APP_ADMIN` |
| **Utilisateur** | `bob@user.com` | `secret` | `APP_USER` |

## 7. Contributeurs

Ce projet a été développé par :
* **Tommy Brisset** - [TommyBrisset](https://github.com/TommyBRISSET)
* **Kilian Moreau** - [KilianMoreau](https://github.com/KilianMoreau)
