# SAE FI - Sujet 3

### Lien du projet
https://github.com/LeskGit/SAE_FI

## Composition de l'équipe
- **Axel MEUNIER** (Chef de projet)
- Loris GRANDCHAMP
- Alexis NISOL
- Corentin THUAULT
- Elyandre BURET

## Installation de l'application

### Prérequis
- Python 3.8 ou supérieur

### Étapes d'installation

1. **Cloner le dépôt** :
```bash
git clone https://github.com/LeskGit/SAE_FI.git
cd project-oumami
```

2. **Créer et activer un environnement virtuel** (recommandé)
```bash
# Création
python -m venv venv

# Activation
    # Pour Windows
.\venv\Scripts\activate
    # Pour Linux
source venv/bin/activate
```

3. **Installer les dépendances**
```bash
pip install -r requirements.txt
```

## Lancement de l'application
1. Initier la base de données (avant le premier lancement)
```bash
flask loaddb tuto/static/data.yml
```

2. Lancer l'application
```bash
flask run
```
##### L'application sera accessible localement à l'adresse `http://127.0.0.1:5000`

## Commandes Flask disponibles
- Synchroniser la base de données (*créer les tables manquantes*)
    ```bash
    flask syncdb
    ```
- Ajouter un utilisateur
    ```bash
    flask newuser username password
    ```
- Changer le mot de passe
    ```bash
    flask newuser username password
    ```
    
## Ressources :
| Description | Lien |
|-------------|------|
| Flask-WTF Forms Documentation | [flask-wtf.readthedocs.io](https://flask-wtf.readthedocs.io/en/1.2.x/form/) |
| Flask Tutorial by Grey Li | [gist.github.com](https://gist.github.com/greyli/81d7e5ae6c9baf7f6cdfbf64e8a7c037) |
| Flask-Resize API Documentation | [flask-resize.readthedocs.io](https://flask-resize.readthedocs.io/api.html#module-flask_resize.resizing) |
| Flask-Uploads Documentation | [flask-uploads.readthedocs.io](https://flask-uploads.readthedocs.io/en/latest/) |