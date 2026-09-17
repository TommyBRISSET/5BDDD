# cours_5bddd

## Introduction
* **Documentation** : https://fastapi.tiangolo.com/

## Mise en place du projet Python
1. **Création du projet de base GitHub** (`README.md`, `.gitignore`)
2. **Clonage en local**
3. **Création et activation de l'environnement virtuel (`venv/`)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python.exe -m pip install --upgrade pip
```
4. **Création du fichier `requirements.txt` et installation des librairies**
```bash
pip install "fastapi[standard]"
pip install -r requirements.txt
```
5. **Création du programme principal (à commenter)**
```bash
uvicorn app.main:app --reload
```

## Exécution et vérification
* **Ouvrir le navigateur** : http://127.0.0.1:8000
* **Test** : http://127.0.0.1:8000/items/42?q=test
* **Documentation** : http://127.0.0.1:8000/docs

## Test avec requêtes mal formés 

* **Ouvrir le navigateur** : http://127.0.0.1:8000/items/abc
* **Mettre un string dans le champs price**
