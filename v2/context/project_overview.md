# Synthèse Executive Du Projet

## Objectif

Construire un moteur de recommandation e-commerce session-based, crédible sur le plan ML et présentable à un décideur métier via une application Streamlit professionnelle.

## Problème Business

Un site e-commerce doit recommander les bons produits pendant que l'utilisateur navigue, parfois avec très peu de signaux disponibles. Le projet vise à améliorer la découverte produit, la conversion panier et la valeur du panier moyen en exploitant les signaux observés au début d'une session.

## Formulation ML

Le problème est formulé comme une tâche de ranking:

> Étant donné le début d'une session, classer les produits candidats selon leur probabilité relative d'être consultés, ajoutés au panier ou achetés plus tard dans la même session.

Les scores produits seront présentés comme des scores de pertinence ou d'affinité, pas comme des probabilités d'achat garanties.

## Dataset Principal

La v2 utilise **Coveo SIGIR eCom 2021** comme socle de recommandation.

Fichiers source:

- `v2/data/coveo/raw/browsing_train.csv`
- `v2/data/coveo/raw/search_train.csv`
- `v2/data/coveo/raw/sku_to_content.csv`

Signaux clés:

- identifiants de session anonymisés;
- timestamps;
- vues détail produit;
- ajouts panier;
- retraits panier;
- achats;
- recherches, résultats affichés et produits cliqués;
- catégories hashées;
- price buckets;
- vecteurs de description et d'image.

`Online Retail II` est conservé uniquement dans `v1/` comme baseline historique.

## Livrables Cibles

- Un pipeline de recommandation session-based sur Coveo.
- Un protocole d'évaluation offline sans fuite temporelle.
- Des baselines robustes: popularité, session récente, co-visitation, co-cart.
- Des modèles de ranking supervisés ou hybrides si le temps le permet.
- Des métriques de recommandation: `Recall@K`, `NDCG@K`, `HitRate@K`, `Precision@K`, `MAP@K`, couverture catalogue.
- Une application Streamlit orientée décision: problème business, dataset, protocole, résultats, marketplace demo et limites.

## Positionnement De L'App

La couche marketplace affichera des noms, visuels et catégories reconstruits pour rendre les produits compréhensibles. Cette couche est une aide à la présentation, pas une donnée source Coveo. La logique ML reste fondée sur les événements réels anonymisés et les métadonnées produit disponibles.
