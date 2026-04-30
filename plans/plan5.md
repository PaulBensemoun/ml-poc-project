# Plan 5 — Générer les candidats produits

## Objectif

Créer, pour chaque session, une liste de produits candidats que les modèles devront ranker.

## Pourquoi c'est important

Un recommender ne score pas seulement un produit isolé. Il doit choisir les meilleurs produits dans un ensemble de candidats réalistes. La qualité de cet ensemble conditionne la crédibilité des métriques.

## Actions

1. Créer un module :

```text
src/candidates.py
```

2. Définir les candidats positifs :
   - produits présents dans le suffixe futur cible ;
   - future detail, add ou purchase selon la cible choisie.
3. Définir les candidats négatifs simples :
   - produits absents du suffixe futur cible.
4. Définir les hard negatives :
   - produits populaires globalement ;
   - produits dans la même catégorie ;
   - produits affichés dans les résultats de recherche mais non cliqués ;
   - produits co-visités avec le préfixe mais absents du futur ;
   - produits co-cartés avec le préfixe mais absents du futur ;
   - produits proches via embeddings texte/image.
5. Créer des stratégies de génération :

```text
generate_popularity_candidates()
generate_search_candidates()
generate_covisit_candidates()
generate_cocart_candidates()
generate_content_candidates()
```

6. Garantir que les produits cibles futurs sont toujours inclus dans les candidats.
7. Limiter le nombre de candidats par session pour garder le training faisable.
8. Ajouter un paramètre `random_state`.
9. Sauvegarder un dataset candidat intermédiaire si utile.

## Fichiers concernés

- `src/candidates.py`
- `src/sessionize.py`
- `src/splitting.py`
- `src/features.py`

## Livrables

- Génération reproductible de candidats.
- Candidats positifs et négatifs par session.
- Hard negatives réalistes.
- Contrôle du nombre de candidats par session.

## Critères de validation

- Chaque session évaluée contient au moins un candidat positif.
- Les négatifs ne contiennent pas la cible future.
- Les candidats ne proviennent pas d'informations futures interdites.
- Les candidats incluent des alternatives réalistes, pas seulement du random.

## Risques

- Trop de candidats par session.
- Trop peu de positifs pour certaines cibles.
- Hard negatives trop difficiles au début.

## Décision attendue

Définir la composition initiale de l'ensemble candidat, par exemple :

- 20 produits populaires ;
- 20 produits co-visités ;
- 20 produits issus de recherche ;
- 20 produits même catégorie ;
- tous les positifs futurs.
