# Standards Engineering V2

## Objectif

Ces règles cadrent la v2 Coveo comme un projet ML professionnel. Elles remplacent les contraintes héritées du socle initial et servent de garde-fous pour garder le pipeline crédible, reproductible et présentable à un décideur métier.

## Structure

- Le code historique Online Retail II reste dans `v1/`.
- Le projet principal Coveo reste dans `v2/`.
- Les nouveaux modules de recommandation doivent être créés dans `v2/src/`.
- Les scripts d'audit, préparation ou entraînement v2 doivent être placés dans `v2/scripts/`.
- Les artefacts préparés doivent aller dans `v2/data/coveo/processed/`.
- Les rapports et métriques v2 doivent aller dans `v2/results/`.

## Principes ML

- Ne jamais utiliser le suffixe futur d'une session pour calculer les features du préfixe observé.
- Séparer explicitement `observed_prefix`, `future_suffix`, candidats et labels.
- Évaluer avec des métriques de ranking: `Recall@K`, `NDCG@K`, `HitRate@K`, `Precision@K`, `MAP@K` et couverture.
- Conserver les métriques de classification uniquement comme diagnostic secondaire.
- Inclure au moins une baseline simple et défendable avant tout modèle avancé.
- Documenter toute stratégie de negative sampling et distinguer random negatives et hard negatives.

## Données Coveo

- Traiter `v2/data/coveo/raw/browsing_train.csv` comme la source principale du comportement session.
- Intégrer `search_train.csv` après stabilisation du protocole browsing.
- Utiliser `sku_to_content.csv` pour les features produit et la couche de similarité lorsque la couverture le permet.
- Ne pas présenter les noms, catégories lisibles ou images de la demo comme des assets originaux Coveo.
- Mentionner clairement que Coveo est anonymisé.

## Qualité Et Reproductibilité

- Tous les échantillonnages doivent accepter un `seed`.
- Les traitements lourds doivent supporter un mode sample ou `max_rows`.
- Les chemins doivent être définis relativement à `v2/` ou centralisés dans `v2/src/config.py`.
- Les sorties intermédiaires doivent être nommées explicitement et réutilisables.
- Les fonctions doivent rester simples, testables et compatibles avec pandas/scikit-learn.

## Présentation Business

- L'app finale doit expliquer la valeur métier avant de détailler la technique.
- Les scores doivent être appelés `score de recommandation`, `score d'affinité` ou `score de ranking`, sauf calibration explicite.
- Les limites doivent être visibles: achats rares, validation offline, anonymisation, absence d'A/B test.
- La démonstration marketplace doit soutenir l'histoire produit sans masquer les hypothèses ML.
