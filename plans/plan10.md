# Plan 10 — Construire la couche marketplace demo

## Objectif

Créer une couche visuelle crédible pour présenter les recommandations dans une interface type marketplace.

## Principe important

Coveo est anonymisé. Les noms produits et images ne doivent pas être présentés comme les vrais assets du retailer. Ils constituent une couche de démonstration reconstruite.

L'app devra afficher clairement :

> Les produits et visuels affichés sont reconstruits pour la démonstration. Le moteur ML utilise les vrais signaux comportementaux anonymisés du dataset Coveo.

## Actions

1. Créer un fichier :

```text
data/coveo_product_catalog_demo.csv
```

2. Créer ou compléter :

```text
src/catalog.py
```

3. Définir les colonnes :
   - `product_sku_hash`
   - `demo_product_name`
   - `demo_category`
   - `price_bucket`
   - `display_price`
   - `image_url`
   - `image_source`
   - `description_short`
   - `is_demo_ready`
4. Définir une stratégie de catégories lisibles :
   - mapper les catégories hashées vers des catégories demo ;
   - ou créer des clusters de produits ;
   - ou utiliser des catégories génériques réalistes.
5. Définir une stratégie d'images :
   - images générées localement ;
   - placeholders par catégorie ;
   - images libres de droit si utilisées.
6. Créer un subset demo-ready :
   - top produits recommandés ;
   - produits issus des scénarios ;
   - produits avec score élevé ;
   - produits visuellement présentables.
7. Ajouter une logique fallback :
   - si pas d'image, image neutre ;
   - si pas de nom, nom générique ;
   - si pas de catégorie, catégorie `Other`.

## Fichiers concernés

- `data/coveo_product_catalog_demo.csv`
- `src/catalog.py`
- `src/app.py`
- futurs fichiers `src/pages/`

## Livrables

- Catalogue demo lisible.
- Images ou placeholders disponibles.
- Fonctions de jointure modèle -> produit affichable.
- Disclaimer prêt pour l'app.

## Critères de validation

- Chaque recommandation affichée peut être transformée en carte produit.
- Les champs nécessaires à l'UI sont disponibles.
- La source des images est claire.
- L'app ne prétend pas que les visuels sont les vrais produits Coveo.

## Risques

- Couche visuelle trop artificielle.
- Trop peu de produits demo-ready.
- Confusion entre données source et reconstruction UI.

## Décision attendue

Définir le niveau de réalisme visuel :

- placeholders sobres ;
- images générées par catégorie ;
- images libres de droit ;
- combinaison des trois.
