# Plan 8 — Créer les baselines recommender

## Objectif

Construire des baselines solides pour prouver que les modèles ML apportent une vraie valeur.

## Pourquoi c'est indispensable

Un modèle performant n'est pas crédible s'il n'est pas comparé à des règles simples mais fortes. En recommandation e-commerce, les baselines de popularité et de co-visitation sont souvent difficiles à battre.

## Baselines à implémenter

1. Random baseline.
2. Global popularity.
3. Recent-session baseline.
4. Co-visitation baseline.
5. Co-cart baseline.
6. Co-purchase baseline.

## Actions

1. Créer ou compléter :

```text
src/recommendation.py
```

2. Implémenter random baseline :
   - score aléatoire reproductible ;
   - sert uniquement de sanity check.
3. Implémenter global popularity :
   - score basé sur vues ;
   - score basé sur adds ;
   - score basé sur purchases.
4. Implémenter recent-session baseline :
   - recommander les derniers produits observés ;
   - utile pour répétition, retour produit ou comparaison.
5. Construire matrices item-item :
   - co-visitation ;
   - co-cart ;
   - co-purchase.
6. Pour chaque session :
   - récupérer les produits du préfixe observé ;
   - scorer les candidats par similarité item-item ;
   - agréger les scores.
7. Évaluer chaque baseline avec les métriques du Plan 7.
8. Sauvegarder les résultats dans `results/recommender_metrics.csv`.

## Fichiers concernés

- `src/recommendation.py`
- `src/recommender_metrics.py`
- `src/candidates.py`
- `scripts/evaluate_recommenders.py`

## Livrables

- Baselines opérationnelles.
- Scores de baseline par candidat.
- Comparaison baseline vs modèles ML.

## Critères de validation

- Random baseline donne une performance faible.
- Popularity baseline donne une référence forte.
- Co-visitation/co-cart exploitent vraiment le contexte de session.
- Toutes les baselines utilisent le même protocole de candidates et métriques.

## Risques

- Matrices item-item trop volumineuses.
- Co-purchase trop sparse si achats rares.
- Popularity baseline très forte, difficile à battre.

## Décision attendue

Définir la baseline principale à battre dans la présentation finale, probablement :

```text
co-visitation ou global purchase popularity
```
