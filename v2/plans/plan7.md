# Plan 7 — Implémenter les métriques recommender

## Objectif

Remplacer l'évaluation principale accuracy/F1 par des métriques de ranking adaptées à un recommender.

## Métriques cibles

- Precision@K
- Recall@K
- MAP@K
- NDCG@K
- HitRate@K
- Catalog coverage

## Actions

1. Créer un module :

```text
src/recommender_metrics.py
```

2. Définir le format d'entrée :

```text
session_id_hash
candidate_product_sku_hash
score
target
```

3. Grouper les prédictions par session.
4. Trier les candidats par score décroissant.
5. Calculer les métriques à différents K :
   - K = 5 ;
   - K = 10 ;
   - K = 20 si utile.
6. Implémenter :
   - `precision_at_k`;
   - `recall_at_k`;
   - `map_at_k`;
   - `ndcg_at_k`;
   - `hit_rate_at_k`;
   - `catalog_coverage_at_k`.
7. Gérer les sessions sans positif si elles sont incluses.
8. Ajouter une comparaison par cible :
   - future detail ;
   - future add ;
   - future purchase.
9. Sauvegarder les résultats dans :

```text
results/recommender_metrics.csv
```

## Fichiers concernés

- `v2/src/recommender_metrics.py`
- `v2/results/recommender_metrics.csv`
- `v2/scripts/evaluate_recommenders.py`

## Livrables

- Fonctions de métriques ranking.
- Fichier de résultats recommender.
- Support de plusieurs modèles et baselines.

## Critères de validation

- Les métriques sont calculées par session, puis moyennées.
- Les modèles sont comparables sur le même set de sessions.
- Les baselines et modèles avancés utilisent le même protocole.
- L'app peut afficher les résultats.

## Risques

- Sessions sans positifs qui faussent le calcul.
- Mauvaise interprétation de Precision@K si peu de cibles par session.
- NDCG mal calculé si les cibles ne sont pas binaires.

## Décision attendue

Définir la métrique principale du projet, probablement :

```text
NDCG@10 ou Recall@10 sur future purchase
```

Si `purchase` est trop rare, utiliser d'abord `add` ou `detail`, puis présenter `purchase` comme analyse complémentaire.
