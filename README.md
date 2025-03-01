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
flask syncdb
```

2. Lancer l'application
```bash
flask run
```
##### L'application sera accessible localement à l'adresse `http://127.0.0.1:5000`

## Commandes Flask disponibles
- Synchroniser la bd
    ```bash
    flask syncdb
    ```
- Créer un administrateur
  ### Prérequis
  - Créer un utilisteur sur le site
  
  ```bash
    flask setadmin [num_tel]
    ```
