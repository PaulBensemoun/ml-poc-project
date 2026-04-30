# Plan 9 — Entraîner les premiers modèles

## Objectif

Entraîner les premiers modèles ML de ranking session-produit et les comparer aux baselines.

## Modèles prioritaires

1. Logistic Regression.
2. Random Forest.
3. XGBoost.
4. Item-item recommender.
5. Matrix factorization si le temps le permet.

## Actions

1. Adapter ou remplacer progressivement :

```text
scripts/train_models.py
```

2. Créer éventuellement :

```text
scripts/train_recommenders.py
```

3. Charger la table de features du Plan 6.
4. Séparer train/validation/test selon le protocole du Plan 4.
5. Entraîner Logistic Regression :
   - baseline interprétable ;
   - utile pour vérifier la cohérence des features.
6. Entraîner Random Forest :
   - robuste sur features tabulaires ;
   - utile pour feature importance.
7. Entraîner XGBoost :
   - candidat fort pour le modèle final ;
   - bon compromis performance / simplicité.
8. Produire un score pour chaque candidat.
9. Évaluer chaque modèle avec les métriques du Plan 7.
10. Comparer aux baselines du Plan 8.
11. Sauvegarder les modèles dans `models/`.
12. Sauvegarder les résultats dans :

```text
results/recommender_metrics.csv
```

## Fichiers concernés

- `v1/scripts/train_models.py` (baseline historique)
- `v2/scripts/train_recommenders.py`
- `v2/src/features.py`
- `v2/src/recommendation.py`
- `v2/src/recommender_metrics.py`
- `models/`
- `v2/results/recommender_metrics.csv`

## Livrables

- Modèles entraînés.
- Scores par modèle.
- Tableau de comparaison.
- Premier choix de modèle final.

## Critères de validation

- Les modèles battent random baseline.
- Le meilleur modèle bat ou égale une baseline forte sur au moins une métrique clé.
- Les résultats sont reproductibles.
- Le modèle final peut scorer une session en temps acceptable.

## Risques

- XGBoost lent sur dataset complet.
- Baselines item-item meilleures que les modèles tabulaires.
- Features insuffisantes pour battre la popularité.

## Décision attendue

Choisir le modèle candidat pour la demo :

- XGBoost si performance forte ;
- Random Forest si plus stable et explicable ;
- Co-visitation/co-cart si les baselines restent meilleures ;
- hybride si combinaison simple possible.
