# Spécification De L'Application Streamlit V2

## Objectif

L'application finale doit servir de support de présentation professionnel pour un moteur de recommandation e-commerce. Elle doit être compréhensible par un décideur métier tout en restant crédible pour un évaluateur technique.

Elle doit guider l'utilisateur à travers:

1. Le problème business.
2. Le choix du dataset Coveo.
3. Le protocole de recommandation et d'évaluation.
4. La démonstration marketplace.
5. Les limites, risques et prochaines étapes.

Le message central: le moteur ML utilise les comportements réels anonymisés Coveo; les noms et visuels produits affichés dans la marketplace sont reconstruits pour la démonstration.

## Architecture Recommandée

La structure cible est:

```text
v2/src/
  app.py
  pages/
    1_Overview.py
    2_Dataset_and_Insights.py
    3_Training_and_Validation.py
    4_Marketplace_Demo.py
    5_Impact_and_Limitations.py
  app_components.py
  catalog.py
  recommendation.py
  visualization.py
```

Une implémentation en navigation sidebar dans `v2/src/app.py` reste acceptable si elle permet une expérience multipage claire.

## Ton Et UX

Le ton doit être business-friendly, factuel et transparent.

À éviter:

- présenter les scores comme des probabilités d'achat garanties;
- masquer les limites du dataset anonymisé;
- afficher uniquement des métriques techniques sans interprétation produit;
- laisser croire que les images ou noms produits viennent directement de Coveo.

À privilégier:

- "score de recommandation";
- "affinité relative";
- "candidats top-ranked";
- "validation offline";
- "impact business attendu";
- "couche marketplace reconstruite".

## Page 1: Vue D'Ensemble

Objectif: expliquer la valeur en moins de deux minutes.

Contenus:

- proposition de valeur;
- problème e-commerce traité;
- synthèse du fonctionnement;
- état d'avancement du projet;
- distinction `v1/` baseline et `v2/` Coveo.

Composants utiles:

- titre fort;
- cartes KPI: sessions, événements, produits, achats;
- mini schéma du pipeline;
- disclaimer court sur l'anonymisation.

## Page 2: Dataset & Insights

Objectif: justifier Coveo comme base du recommender.

Contenus:

- fichiers source `v2/data/coveo/raw/browsing_train.csv`, `search_train.csv`, `sku_to_content.csv`;
- volumes: 36M événements browsing, 4.9M sessions, 66k produits metadata;
- funnel comportemental: detail, add, remove, purchase;
- sessions courtes et rareté des achats;
- couverture metadata: catégorie, price bucket, vecteurs texte/image;
- limites: anonymisation, images non affichables, catégories hashées.

Visuels recommandés:

- distribution des longueurs de session;
- distribution des types d'événements;
- funnel detail/add/purchase;
- usage de search;
- couverture metadata.

## Page 3: Training & Validation

Objectif: montrer que le recommender est évalué sérieusement.

Contenus:

- formulation du problème en ranking session-produit;
- préfixe observé et suffixe futur;
- règles anti-leakage;
- stratégie de candidats;
- targets progressives: `detail`, puis `add`, puis `purchase`;
- baselines: random, popularité, session récente, co-visitation, co-cart;
- modèles supervisés: Logistic Regression, Random Forest, XGBoost si pertinents;
- métriques principales: `Recall@10`, `NDCG@10`, `HitRate@10`, `Precision@10`, `MAP@10`, couverture.

L'app doit préciser que les métriques sont offline et ne prouvent pas un uplift business sans test online.

## Page 4: Marketplace Demo

Objectif: rendre les recommandations concrètes.

Contenus:

- sélection d'un scénario de session;
- résumé du comportement observé;
- produits déjà vus ou ajoutés;
- recommandations top K;
- carte produit avec nom reconstruit, catégorie demo, prix affiché, score, explication;
- comparaison possible entre deux scénarios.

Explications possibles:

- populaire dans l'historique;
- souvent co-consulté avec les produits vus;
- souvent co-ajouté au panier;
- même catégorie que les produits observés;
- proche en contenu vectoriel;
- cohérent avec le contexte de recherche.

## Page 5: Impact & Limites

Objectif: relier la démonstration à une décision business.

Contenus:

- cas d'usage: homepage personalization, cart upsell, CRM, recommandations post-recherche;
- impact attendu: découverte produit, panier moyen, conversion, rétention;
- limites: dataset anonymisé, achats rares, validation offline, absence d'A/B test, couche visuelle reconstruite;
- roadmap production: tracking d'exposition, service de ranking, monitoring, A/B testing, feedback loop.

## Données App Attendues

Artefacts cibles:

```text
v2/results/coveo_data_audit.json
v2/results/recommender_metrics.csv
v2/data/coveo/processed/session_sample.parquet
v2/data/coveo/processed/evaluation_sessions.parquet
v2/data/coveo/processed/coveo_product_catalog_demo.csv
```

## Critères De Réussite

- Un décideur comprend le projet sans lire le code.
- Le protocole ML est crédible et sans fuite évidente.
- Les recommandations sont affichées sous forme produit, pas seulement en table brute.
- Les limites sont assumées.
- Le storytelling relie les résultats ML aux décisions business.
