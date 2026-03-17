# Archilog

> Permet de crée des cagnottes, d'y ajouter ou supprimer des participations, de calculer qui doit a qui.

## 📋 Table des matières
* [Présentation](#-présentation)
* [Fonctionnalités](#-fonctionnalités)
* [Installation](#-installation)

---

## 🚀 Présentation
Projet développer dans le cadre du cours d'architecture logiciel de deuxieme année de BUT informatique

## ✨ Fonctionnalités
* Création d'une cagnotte si elle le nom entrer n'existe pas dans la base de donnée
* Ajouter à sa participation ou crée une nouvelle participation si l'utilisateur n'a pas encore participé dans la cagnotte
* Supprimer une participation, si il n'y a plus de participant dans la cagnotte, elle se supprime
* Calculer les dettes pour équilibrer la cagnotte

## 🛠️ Installation
installer archilog sur votre pc, ouvrir un terminal a la racine puis :

```bash
$ uv sync

Pour utiliser click et tester les fonction via le terminal :
$ uv run archilog
Usage: archilog [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  create
  delete
  get
  get-all
  import-csv
  init-db
  update

Pour utiliser flask et acceder à l'interface graphique sur votre navigateur :
uv run flask --app archilog.views --debug run  
```

Cours & exampls : [https://kathode.neocities.org](https://kathode.neocities.org)
