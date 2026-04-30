# Plan 6 — Créer les features ML

## Objectif

Construire la table d'entraînement session-produit utilisée par les modèles de ranking.

## Format cible

Chaque ligne représente :

```text
session_id_hash, candidate_product_sku_hash, features..., target
```

## Actions

1. Créer ou compléter :

```text
src/features.py
```

2. Construire les features de session :
   - nombre d'événements observés ;
   - nombre de produits observés ;
   - nombre de produits uniques ;
   - présence d'une recherche ;
   - présence d'un add-to-cart ;
   - temps écoulé ;
   - dernier type d'événement ;
   - dernier product action.
3. Construire les features produit :
   - nombre global de vues ;
   - nombre global d'ajouts panier ;
   - nombre global d'achats ;
   - taux de conversion proxy ;
   - catégorie ;
   - price bucket ;
   - vecteur texte ;
   - vecteur image.
4. Construire les features session-produit :
   - produit déjà vu dans le préfixe ;
   - produit déjà ajouté au panier ;
   - produit présent dans les résultats de recherche ;
   - produit cliqué depuis la recherche ;
   - match de catégorie ;
   - score co-visit ;
   - score co-cart ;
   - score co-purchase ;
   - similarité embedding texte ;
   - similarité embedding image ;
   - fit price bucket.
5. Construire des features d'explication :
   - top reason ;
   - co-visit evidence ;
   - co-cart evidence ;
   - search evidence ;
   - category evidence.
6. Encodage :
   - one-hot ou target encoding pour actions simples ;
   - garder les vecteurs produits sous forme exploitable ;
   - normaliser les compteurs si nécessaire.
7. Ajouter des tests simples sur un petit subset.

## Fichiers concernés

- `src/features.py`
- `src/sessionize.py`
- `src/candidates.py`
- `src/catalog.py` plus tard

## Livrables

- Table de features prête pour training.
- Colonnes numériques compatibles scikit-learn / XGBoost.
- Features d'explication utilisables dans l'app.

## Critères de validation

- La table finale n'a pas de fuite du suffixe futur.
- Les colonnes de features sont stables entre train et test.
- Les modèles peuvent consommer la table sans transformation manuelle.
- Les raisons de recommandation peuvent être dérivées des features.

## Risques

- Trop de colonnes si les embeddings sont utilisés directement.
- Features coûteuses à calculer sur le dataset complet.
- Encodage des catégories anonymisées peu interprétable.

## Décision attendue

Choisir le premier set de features minimal :

- session features ;
- product popularity features ;
- co-visit/co-cart features ;
- category/price bucket ;
- search features si disponibles rapidement.
