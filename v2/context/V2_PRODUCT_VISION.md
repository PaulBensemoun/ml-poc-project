# Vision Produit V2

## Résumé Executive

La v2 doit être présentée comme un prototype professionnel de recommandation e-commerce. L'objectif n'est pas seulement de montrer qu'un modèle fonctionne, mais de démontrer comment un moteur de recommandation peut soutenir des objectifs business: personnalisation, découverte produit, conversion panier, cross-sell, upsell et pilotage marketing.

Le coeur du projet est un recommender session-based entraîné et évalué sur **Coveo SIGIR eCom 2021**. L'application Streamlit finale doit servir de support de présentation à un décideur: elle doit raconter le problème, justifier le choix data, expliquer le protocole ML, afficher les résultats et rendre les recommandations compréhensibles via une marketplace de démonstration.

## Proposition De Valeur

> Recommander les produits les plus pertinents pendant une session e-commerce en exploitant les vues produit, recherches, ajouts panier, achats, timestamps et métadonnées produit.

Le système répond à quatre questions:

- Quels produits recommander maintenant dans cette session?
- Pourquoi ces produits sont-ils pertinents?
- Quelle approche de ranking fonctionne le mieux?
- Comment ce moteur pourrait-il être intégré dans un parcours e-commerce réel?

## Public Cible

### Décideur métier

Il doit comprendre rapidement la valeur du projet: impact potentiel sur la conversion, le panier moyen, la découverte produit et les campagnes CRM.

### Évaluateur technique

Il doit voir que le dataset, le protocole d'évaluation, les métriques et les limites sont solides et documentés.

### Équipe produit ou marketing

Elle doit pouvoir se projeter dans des usages opérationnels: recommandations homepage, suggestions panier, relance CRM, découverte catalogue ou personnalisation de session.

## Expérience Application

L'application finale doit ressembler à un petit produit interne, pas à un notebook. Les pages recommandées sont:

1. **Vue d'ensemble**
   - Objectif business.
   - Proposition de valeur.
   - Architecture simplifiée.
   - État d'avancement.

2. **Dataset & Insights**
   - Pourquoi Coveo a été choisi.
   - Volume et structure des données.
   - Signaux disponibles et limites.
   - Funnel vues, ajouts panier, achats.

3. **Training & Validation**
   - Formulation du problème en ranking.
   - Découpage session: préfixe observé et suffixe futur.
   - Baselines et modèles.
   - Métriques de recommandation.

4. **Marketplace Demo**
   - Sélection d'un scénario de session.
   - Résumé du comportement observé.
   - Cartes produits recommandées.
   - Scores et explications.

5. **Impact & Limites**
   - Cas d'usage business.
   - Limites offline.
   - Risques et mitigations.
   - Roadmap vers une mise en production.

## Principes Produit

### Crédibilité avant décoration

La marketplace demo doit être lisible et convaincante, mais la narration doit rester honnête. Les noms et images affichés sont reconstruits pour la présentation parce que Coveo est anonymisé.

### Recommender ML d'abord

La valeur principale vient du protocole de recommandation, des signaux session et des métriques de ranking. La couche visuelle sert à rendre la démonstration compréhensible.

### Ranking plutôt que classification

Le succès d'un recommender se mesure par la présence des bons produits dans les premiers rangs, pas seulement par accuracy/F1. Les métriques principales doivent être `Recall@K`, `NDCG@K`, `HitRate@K`, `Precision@K`, `MAP@K` et couverture catalogue.

### Validation réaliste

Le protocole doit simuler une situation réelle: observer le début d'une session, recommander des produits, puis vérifier si les produits futurs de la session apparaissent dans le top K.

### Explicabilité

Chaque recommandation doit pouvoir être justifiée par un ou plusieurs signaux: popularité, co-visitation, co-cart, similarité de catégorie, contexte de recherche, similarité contenu ou comportement récent de session.

## Critères De Succès

### Succès technique

- Le choix Coveo est documenté et justifié.
- Le protocole évite les fuites de données.
- Les baselines sont incluses avant les modèles avancés.
- Les résultats sont évalués avec des métriques de ranking.
- Le modèle final est choisi selon performance, vitesse, stabilité et explicabilité.

### Succès produit

- Un décideur comprend la valeur en moins de deux minutes.
- La marketplace demo montre des recommandations différentes selon le scénario.
- L'app explique les scores sans surpromettre.
- Les limites sont visibles et assumées.

### Succès business

- Le projet relie les recommandations à des cas d'usage concrets: homepage personalization, cart upsell, CRM, découverte catalogue.
- Le storytelling permet de discuter d'impact business sans prétendre mesurer un uplift réel sans A/B test.

## Périmètre

La v2 reste un prototype local. Elle ne prétend pas inclure streaming temps réel, feature store, A/B testing online ou MLOps complet. En revanche, l'architecture et les documents doivent permettre d'expliquer comment ces éléments seraient ajoutés dans une phase de production.
