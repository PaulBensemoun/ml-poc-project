# Plan 1 — Récupérer et installer le dataset Coveo

## Objectif

Installer la nouvelle base de travail du projet : **Coveo SIGIR eCom 2021**. Cette étape remplace `Online Retail II` comme dataset cible pour la v2 ML-first.

## Pourquoi cette étape est prioritaire

Toute la refonte dépend de la structure réelle des fichiers Coveo. Avant d'écrire le pipeline, il faut disposer localement des fichiers et vérifier qu'ils correspondent aux hypothèses des documents `context/`.

## Actions

1. Télécharger le dataset Coveo SIGIR eCom 2021 depuis la source officielle.
2. Créer une organisation claire dans `data/`, par exemple :

```text
data/coveo/
  raw/
    browsing_train.csv
    search_train.csv
    sku_to_content.csv
  processed/
```

3. Vérifier que les fichiers attendus sont présents :
   - `browsing_train.csv`
   - `search_train.csv`
   - `sku_to_content.csv`
4. Noter la taille des fichiers.
5. Vérifier rapidement les colonnes de chaque fichier.
6. Documenter toute différence entre la documentation Coveo et les fichiers réellement téléchargés.
7. Conserver `data/online_retail_II.csv` uniquement comme baseline v1.

## Fichiers concernés

- `data/coveo/raw/`
- `context/V2_DATASET_DECISION.md`
- `context/DATA_STRATEGY.md`
- `README.md` plus tard

## Livrables

- Dataset Coveo disponible localement.
- Structure `data/coveo/raw/` prête.
- Liste des fichiers et colonnes confirmée.
- Première note sur la taille et la faisabilité locale.

## Critères de validation

- Les trois fichiers Coveo principaux existent localement.
- Le projet peut lire un échantillon de chaque fichier.
- On sait si le dataset complet est manipulable localement ou s'il faudra travailler sur un sous-échantillon.

## Risques

- Dataset trop volumineux pour une itération rapide.
- Téléchargement manuel nécessaire.
- Colonnes légèrement différentes de la documentation.

## Décision attendue

À la fin de cette étape, décider si le développement commence sur :

- le dataset complet ;
- un échantillon représentatif ;
- un subset par période ou nombre de sessions.
