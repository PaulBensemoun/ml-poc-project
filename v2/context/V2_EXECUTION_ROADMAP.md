# Roadmap D'Exécution V2

## Objectif

Cette roadmap transforme la vision Coveo en séquence d'implémentation maîtrisée. Le projet doit avancer comme un chantier ML professionnel: chaque étape produit un artefact vérifiable, documenté et utile pour la présentation finale.

## Décision Directrice

- `v1/` conserve Online Retail II comme baseline historique.
- `v2/` devient le projet principal Coveo.
- Le coeur ML utilise les sessions anonymisées Coveo.
- La couche marketplace est reconstruite pour la présentation.
- Les métriques principales sont des métriques de ranking.
- L'app finale doit parler à un décideur métier autant qu'à un profil technique.

## État Actuel

| Étape | Statut | Artefacts |
| --- | --- | --- |
| Baseline v1 | Conservée | `v1/src/`, `v1/scripts/`, `v1/results/model_metrics.csv` |
| Plan 1 | Terminé | Données Coveo dans `v2/data/coveo/raw/` |
| Plan 2 | Terminé | Audit `v2/results/coveo_data_audit.*` |
| Plan 3 | Terminé | Parser `v2/src/sessionize.py` et sample parquet |
| Plan 4 | Prochaine étape | Protocole d'évaluation `v2/src/splitting.py` |

## Phase 1: Data Acquisition Et Audit

Objectif: sécuriser la base data Coveo.

Livrables:

- fichiers raw dans `v2/data/coveo/raw/`;
- script `v2/scripts/audit_coveo_data.py`;
- rapports `v2/results/coveo_data_audit.json` et `v2/results/coveo_data_audit.md`;
- synthèse dans `v2/context/COVEO_DATA_AUDIT_SUMMARY.md`.

Statut: terminé.

## Phase 2: Session Parsing

Objectif: transformer `browsing_train.csv` en événements normalisés et sessions triées.

Livrables:

- `v2/src/sessionize.py`;
- fonctions utilitaires de session;
- support `max_rows` et `sample_sessions`;
- sample `v2/data/coveo/processed/session_sample.parquet`.

Statut: terminé.

Points de vigilance pour la suite:

- le mode `max_rows` peut couper des sessions;
- les sessions sans ID doivent être exclues des jeux d'évaluation;
- `build_session_index` est utile pour sample, mais pas pour charger 36M lignes en mémoire.

## Phase 3: Protocole D'Évaluation

Objectif: définir comment évaluer un recommender session-based sans fuite de données.

Module cible:

```text
v2/src/splitting.py
```

Tâches:

1. Construire `observed_prefix` et `future_suffix`.
2. Définir les stratégies de cutoff:
   - N premiers événements;
   - pourcentage de session;
   - avant premier add-to-cart;
   - avant premier purchase.
3. Définir les targets:
   - futur `detail`;
   - futur `add`;
   - futur `purchase`.
4. Établir les règles d'éligibilité:
   - préfixe non vide;
   - au moins une interaction produit observée;
   - au moins un produit cible futur;
   - pas de target déjà rendue triviale par le préfixe si le protocole l'interdit.
5. Générer splits train/validation/test reproductibles.

Critère de sortie: un dataset d'évaluation session-produit prêt pour candidats et features.

## Phase 4: Candidate Generation

Objectif: construire des candidats réalistes par session.

Module cible:

```text
v2/src/candidates.py
```

Sources de candidats:

- popularité globale;
- produits vus dans le préfixe;
- co-visitation;
- co-cart;
- même catégorie quand disponible;
- produits issus des recherches;
- produits similaires via vecteurs texte/image.

Le set candidat d'évaluation doit toujours inclure les produits cibles futurs.

## Phase 5: Feature Engineering

Objectif: produire une table session-produit exploitable par des rankers.

Module cible:

```text
v2/src/features.py
```

Familles de features:

- session: longueur, nombre d'interactions produit, durée, dernier événement;
- produit: popularité, add count, purchase count, catégorie, price bucket;
- interaction: vu dans la session, ajouté au panier, même catégorie, co-visitation, co-cart;
- recherche: montré, cliqué, non cliqué;
- contenu: similarité texte/image.

Critère de sortie: aucune feature ne doit dépendre du suffixe futur.

## Phase 6: Modèles Et Métriques

Modules cibles:

```text
v2/src/recommender_metrics.py
v2/src/recommendation.py
v2/scripts/train_recommenders.py
v2/scripts/evaluate_recommenders.py
```

Baselines requises:

- random ranking;
- popularité globale;
- session récente;
- co-visitation;
- co-cart.

Modèles supervisés possibles:

- Logistic Regression;
- Random Forest;
- XGBoost;
- item-item co-occurrence.

Métriques:

- `Recall@5`, `Recall@10`;
- `Precision@5`, `Precision@10`;
- `NDCG@10`;
- `MAP@10`;
- `HitRate@10`;
- couverture catalogue.

Sortie attendue:

```text
v2/results/recommender_metrics.csv
```

## Phase 7: Catalogue De Démonstration

Objectif: rendre les produits anonymisés compréhensibles dans l'app.

Module cible:

```text
v2/src/catalog.py
```

Artefact cible:

```text
v2/data/coveo/processed/coveo_product_catalog_demo.csv
```

Champs recommandés:

- `product_sku_hash`;
- `demo_product_name`;
- `demo_category`;
- `price_bucket`;
- `display_price`;
- `image_url`;
- `image_source`;
- `description_short`;
- `is_demo_ready`.

Cette couche doit être présentée comme reconstruite pour la démonstration.

## Phase 8: Application Streamlit

Objectif: construire une app orientée présentation business.

Modules cibles:

```text
v2/src/app.py
v2/src/pages/
v2/src/app_components.py
v2/src/visualization.py
```

Pages:

- Vue d'ensemble;
- Dataset & Insights;
- Training & Validation;
- Marketplace Demo;
- Impact & Limites.

Critère de sortie: un décideur peut comprendre le problème, la solution, les résultats et les limites sans ouvrir le code.

## Phase 9: Documentation Finale

Objectif: rendre le projet autonome et défendable.

Tâches:

- maintenir `README.md` en français professionnel;
- documenter comment lancer audit, session parsing, entraînement et app;
- expliquer le choix Coveo;
- expliquer le protocole d'évaluation;
- présenter limites et prochaine phase production.

## Priorités Avant Plan 4

1. Garder `v2/src/sessionize.py` comme source session stable.
2. Créer `v2/src/splitting.py`.
3. Choisir officiellement target initiale, cutoff et règles d'éligibilité.
4. Sauvegarder les artefacts du protocole dans `v2/data/coveo/processed/`.
5. Documenter les décisions dans l'app et les context docs.
