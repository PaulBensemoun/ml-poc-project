# Plan 4 — Définir le protocole d'évaluation

## Objectif

Mettre en place une évaluation réaliste de recommandation session-based.

## Principe

Le modèle doit simuler une situation réelle :

> On observe le début d'une session, puis on recommande les produits qui seront consultés, ajoutés au panier ou achetés dans la suite de cette session.

## Actions

1. Créer un module :

```text
src/splitting.py
```

2. Définir une stratégie de coupure de session :
   - prendre les N premiers événements ;
   - ou couper à un pourcentage de la session ;
   - ou couper avant le premier add-to-cart ;
   - ou couper avant le premier purchase.
3. Définir le préfixe observé :

```text
observed_prefix = events[:cutoff]
```

4. Définir le suffixe futur :

```text
future_suffix = events[cutoff:]
```

5. Définir les cibles possibles :
   - futur product detail ;
   - futur add-to-cart ;
   - futur purchase.
6. Choisir la cible principale pour la v2 :
   - recommandation achat si le volume est suffisant ;
   - sinon recommandation add-to-cart ou product detail pour le premier modèle.
7. Construire les labels :
   - `1` si le produit candidat apparaît dans le suffixe futur cible ;
   - `0` sinon.
8. Séparer train/validation/test :
   - split chronologique par timestamp de session ;
   - ou split session-level reproductible ;
   - éviter les fuites entre préfixe et suffixe.
9. Documenter clairement le protocole dans l'app.

## Fichiers concernés

- `src/splitting.py`
- `src/sessionize.py`
- `context/V2_RECOMMENDER_STRATEGY.md`

## Livrables

- Fonction de découpe préfixe/suffixe.
- Définition claire des targets.
- Splits train/validation/test.
- Dataset d'évaluation session-product.

## Critères de validation

- Aucune feature ne provient du suffixe futur.
- Chaque session évaluée a un préfixe observé non vide.
- Chaque session évaluée a au moins un produit cible futur.
- Les targets sont reproductibles.

## Risques

- Trop peu de sessions avec achat futur.
- Trop de sessions courtes pour être tronquées.
- Évaluation trop facile si la cible est déjà dans le préfixe.

## Décision attendue

Choisir officiellement :

- la cible principale ;
- la stratégie de cutoff ;
- les règles d'éligibilité des sessions.
