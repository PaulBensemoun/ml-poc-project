# Projet ML Recommender E-commerce

Ce dépôt contient un projet de recommandation e-commerce structuré comme un travail d'ingénierie ML professionnel. L'objectif final est de présenter à un décideur métier un moteur de recommandation crédible, entraîné sur des sessions e-commerce réelles anonymisées, avec une application Streamlit claire, honnête et orientée impact business.

## Positionnement

La version active du projet est `v2/`. Elle utilise le dataset **Coveo SIGIR eCom 2021** pour construire un recommender session-based capable de classer les produits les plus pertinents pendant une session de navigation.

La version `v1/` est conservée comme baseline historique basée sur **Online Retail II**. Elle reste utile pour expliquer le point de départ et les limites d'une approche transactionnelle, mais elle ne pilote plus l'architecture cible.

## Structure Du Dépôt

```text
ml-poc-project/
├── v1/          # Baseline historique Online Retail II
│   ├── src/     # Pipeline classification client-produit
│   ├── scripts/ # Scripts d'entraînement et d'exécution v1
│   ├── models/  # Modèles v1 sérialisés
│   └── results/ # Métriques v1
└── v2/          # Projet principal Coveo
    ├── src/     # Modules du recommender session-based
    ├── scripts/ # Scripts d'audit et de préparation
    ├── data/
    │   └── coveo/
    │       ├── raw/       # browsing_train.csv, search_train.csv, sku_to_content.csv
    │       └── processed/ # Artefacts préparés pour le pipeline
    ├── results/ # Audits, métriques et rapports v2
    ├── context/ # Cadrage produit, data, ML et app
    └── plans/   # Plans d'exécution de la v2
```

## v2: Recommender Coveo

Le dataset Coveo contient environ 36M événements de navigation, 4.9M sessions, des vues produit, des ajouts panier, des achats, des interactions de recherche, des timestamps et des métadonnées produit. C'est une base solide pour simuler le cas d'usage réel: observer le début d'une session puis recommander les produits qui seront probablement consultés, ajoutés au panier ou achetés ensuite.

Fichiers source attendus:

| Fichier | Rôle |
| --- | --- |
| `v2/data/coveo/raw/browsing_train.csv` | Événements de navigation et actions produit |
| `v2/data/coveo/raw/search_train.csv` | Recherches, résultats affichés, produits cliqués |
| `v2/data/coveo/raw/sku_to_content.csv` | Métadonnées produit, catégories, prix, vecteurs texte/image |

## État Actuel

| Étape | Statut | Livrable |
| --- | --- | --- |
| Plan 1 | Terminé | Dataset Coveo placé dans `v2/data/coveo/raw/` |
| Plan 2 | Terminé | Audit dans `v2/results/coveo_data_audit.*` |
| Plan 3 | Terminé | Parser de sessions `v2/src/sessionize.py` |
| Plan 4 | Prochaine étape | Protocole d'évaluation `v2/src/splitting.py` |

## Commandes Utiles

Installer les dépendances:

```bash
pip install -r requirements.txt
```

Réexécuter l'audit Coveo:

```bash
python v2/scripts/audit_coveo_data.py
```

Tester le parser de sessions sur un échantillon:

```bash
python v2/src/sessionize.py --max-rows 500000 --save
```

Lancer la baseline v1:

```bash
python v1/scripts/main.py
```

## Principes De Présentation

- Les scores affichés dans l'app seront des scores de ranking, pas des probabilités d'achat garanties.
- Les noms, visuels et catégories lisibles de la marketplace seront reconstruits pour la démonstration, car Coveo est anonymisé.
- Les métriques principales seront des métriques de recommandation: `Recall@K`, `NDCG@K`, `HitRate@K`, `Precision@K`, `MAP@K` et couverture catalogue.
- Les limites seront explicitement présentées: dataset anonymisé, achats rares, validation offline, absence d'A/B test réel.
