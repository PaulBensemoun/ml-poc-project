# Plan 3 — Construire le parser de sessions

## Objectif

Transformer les événements bruts Coveo en sessions ordonnées et exploitables par le pipeline de recommandation.

## Pourquoi cette étape est centrale

Le projet v2 est session-based. Le modèle ne doit plus raisonner sur des couples client-produit statiques, mais sur le contexte observé au début d'une session et les produits qui apparaissent ensuite.

## Actions

1. Créer un module dédié :

```text
src/sessionize.py
```

2. Charger les événements de browsing.
3. Normaliser les colonnes utiles :
   - `session_id_hash`
   - `server_timestamp_epoch_ms`
   - `event_type`
   - `product_action`
   - `product_sku_hash`
4. Trier chaque session par timestamp.
5. Filtrer ou séparer :
   - événements sans produit ;
   - product detail ;
   - add-to-cart ;
   - remove ;
   - purchase.
6. Créer une représentation session :

```text
session_id_hash
ordered_events
observed_products
observed_actions
timestamps
```

7. Prévoir une jointure optionnelle avec `search_train.csv`.
8. Ajouter des fonctions utilitaires :
   - récupérer les produits observés ;
   - récupérer le dernier événement ;
   - détecter si une session contient un cart ;
   - détecter si une session contient un purchase ;
   - calculer la durée de session.
9. Ajouter un mode `sample_size` pour travailler vite en local.

## Fichiers concernés

- `src/sessionize.py`
- `data/coveo/raw/browsing_train.csv`
- `data/coveo/raw/search_train.csv`

## Livrables

- Fonction de chargement des sessions.
- Sessions triées chronologiquement.
- Fonctions d'extraction des actions et produits observés.
- Échantillon de sessions prêt pour la génération de train/test.

## Critères de validation

- Les événements sont bien ordonnés par timestamp.
- Une session donnée peut être affichée sous forme lisible.
- On peut compter les sessions avec detail/add/purchase.
- Les fonctions supportent un subset pour itération rapide.

## Risques

- Sessions très longues ou très courtes.
- Événements sans produit qui compliquent la séquence.
- Plusieurs produits associés à un même événement.
- Fichiers trop volumineux pour un chargement complet.

## Décision attendue

Définir le format interne standard d'une session, qui sera utilisé par `splitting.py`, `features.py`, `candidates.py` et l'app Streamlit.
