# Plan 2 — Auditer le dataset Coveo

## Objectif

Comprendre précisément le contenu du dataset Coveo avant toute modélisation.

## Pourquoi cette étape est critique

Un recommender performant dépend autant de la formulation du problème que du modèle. L'audit doit confirmer les volumes, les types d'événements, la qualité des sessions, la couverture produit et la disponibilité des signaux nécessaires.

## Actions

1. Créer un audit reproductible :
   - notebook : `notebooks/coveo_data_audit.ipynb`, ou
   - script : `scripts/audit_coveo_data.py`.
2. Auditer `browsing_train.csv` :
   - nombre de lignes ;
   - nombre de sessions ;
   - nombre de produits ;
   - distribution des événements ;
   - distribution des `product_action` ;
   - part de sessions avec product detail ;
   - part de sessions avec add-to-cart ;
   - part de sessions avec purchase ;
   - longueur des sessions.
3. Auditer `search_train.csv` :
   - nombre de recherches ;
   - nombre de sessions avec recherche ;
   - nombre moyen de résultats par recherche ;
   - présence de produits cliqués ;
   - produits affichés mais non cliqués.
4. Auditer `sku_to_content.csv` :
   - nombre de produits ;
   - couverture des catégories ;
   - couverture des price buckets ;
   - couverture des vecteurs texte ;
   - couverture des vecteurs image.
5. Identifier les premières contraintes :
   - données manquantes ;
   - sessions très courtes ;
   - sessions sans produit ;
   - produits sans métadonnées ;
   - éventuels problèmes de timestamp.
6. Produire des chiffres synthétiques réutilisables dans l'app.

## Fichiers concernés

- `data/coveo/raw/browsing_train.csv`
- `data/coveo/raw/search_train.csv`
- `data/coveo/raw/sku_to_content.csv`
- `notebooks/coveo_data_audit.ipynb`
- `scripts/audit_coveo_data.py`

## Livrables

- Audit complet des fichiers Coveo.
- Table de chiffres clés pour l'app Streamlit.
- Décision sur le périmètre de travail initial.

## Critères de validation

- On connaît les volumes principaux.
- On connaît la proportion de sessions exploitables.
- On sait quelles cibles sont réalistes : future view, future add, future purchase.
- On sait si les recherches peuvent être intégrées dès la première version.

## Risques

- Trop peu de sessions avec purchase pour commencer directement par achat.
- Fichiers trop lourds pour pandas en mémoire.
- Métadonnées vectorisées difficiles à exploiter sans parsing spécifique.

## Décision attendue

Choisir le premier objectif de modélisation :

- recommander les futurs produits consultés ;
- recommander les futurs produits ajoutés au panier ;
- recommander les futurs produits achetés ;
- ou entraîner une approche multi-signal progressive.
