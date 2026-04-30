# Plan 11 — Refaire l'app Streamlit multi-pages

## Objectif

Transformer l'application Streamlit en vraie démo interactive multi-pages, orientée produit et crédibilité ML.

## Architecture cible

```text
src/
  app.py
  pages/
    1_Overview.py
    2_Dataset_and_Insights.py
    3_Training_and_Validation.py
    4_Marketplace_Demo.py
    5_Impact_and_Limitations.py
```

Si la structure multipage Streamlit pose problème, utiliser une navigation via sidebar dans `v2/src/app.py`.

## Pages à créer

### 1. Overview

Objectif :

- expliquer le contexte business ;
- expliquer pourquoi le projet est devenu session-based ;
- préciser que Coveo est le dataset cible ;
- présenter le disclaimer sur la couche visuelle.

### 2. Dataset & Insights

Objectif :

- présenter Coveo ;
- montrer les événements : detail, add, purchase ;
- montrer les sessions ;
- montrer les recherches ;
- expliquer l'anonymisation ;
- afficher les premiers graphiques d'audit.

### 3. Training & Validation

Objectif :

- expliquer le protocole de session truncation ;
- montrer les features ;
- comparer les baselines ;
- comparer les modèles ;
- justifier le modèle final.

### 4. Marketplace Demo

Objectif :

- choisir un scénario de session ;
- afficher le préfixe observé ;
- afficher les produits recommandés ;
- montrer les cartes produit ;
- expliquer chaque recommandation.

### 5. Impact & Limitations

Objectif :

- expliquer la valeur business ;
- présenter les limites ;
- expliquer ce qu'il faudrait pour une mise en production ;
- parler d'A/B testing, monitoring et retraining.

## Actions

1. Refactoriser `v2/src/app.py`.
2. Créer les pages ou une navigation sidebar.
3. Créer des composants UI réutilisables :

```text
src/app_components.py
src/visualization.py
```

4. Ajouter les caches :
   - `@st.cache_data` pour les données ;
   - `@st.cache_resource` pour les modèles.
5. Intégrer les résultats :
   - `v2/results/recommender_metrics.csv`;
   - recommandations pré-calculées si nécessaire.
6. Intégrer le catalogue demo.
7. Ajouter le disclaimer visuel sur les pages pertinentes.

## Fichiers concernés

- `v2/src/app.py`
- `v2/src/pages/`
- `v2/src/app_components.py`
- `v2/src/visualization.py`
- `v2/src/catalog.py`
- `v2/results/recommender_metrics.csv`

## Livrables

- App multi-pages.
- Visualisations d'audit.
- Page training/validation claire.
- Page marketplace interactive.
- Disclaimer explicite.

## Critères de validation

- L'app se lance localement.
- Chaque page a un objectif clair.
- Le storytelling est compréhensible sans lire le code.
- La page demo ressemble à une expérience marketplace crédible.
- La partie ML reste techniquement honnête.

## Risques

- App lente si elle recalcule trop de choses.
- Trop de logique dans `app.py`.
- Demo visuelle trop déconnectée du modèle.

## Décision attendue

Choisir l'architecture finale :

- vraie structure `v2/src/pages/` ;
- ou sidebar dans `v2/src/app.py` si plus compatible avec l'environnement Streamlit installé.
