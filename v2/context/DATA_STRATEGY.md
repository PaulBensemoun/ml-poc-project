# Stratégie Data V2

## Décision Dataset

Le dataset cible de la v2 est **Coveo SIGIR eCom 2021**. Il est prioritaire parce qu'il contient des sessions e-commerce réelles anonymisées avec vues produit, ajouts panier, retraits, achats, recherches, timestamps, catégories hashées, price buckets et vecteurs de contenu.

`Online Retail II` reste uniquement une baseline historique dans `v1/`.

## Sources

Fichiers raw:

- `v2/data/coveo/raw/browsing_train.csv`;
- `v2/data/coveo/raw/search_train.csv`;
- `v2/data/coveo/raw/sku_to_content.csv`.

Artefacts préparés:

- `v2/data/coveo/processed/session_sample.parquet`;
- futurs datasets d'évaluation dans `v2/data/coveo/processed/`.

## Règles De Parsing

- Charger les colonnes utiles sans lire inutilement tout le dataset en mémoire.
- Normaliser `session_id_hash`, `event_type`, `product_action`, `product_sku_hash`, `server_timestamp_epoch_ms` et `hashed_url`.
- Trier les événements par session et timestamp.
- Distinguer pageview, product detail, add, remove et purchase.
- Exclure les sessions sans ID des jeux d'évaluation.
- Conserver search et product content pour les phases de features avancées.

## Formulation Du Dataset ML

Chaque ligne d'entraînement ou d'évaluation représentera:

```text
session_id_hash, candidate_product_sku_hash, cutoff_event_index
```

La cible vaut `1` si le produit candidat apparaît dans le suffixe futur comme événement cible, et `0` sinon.

La progression recommandée est:

1. `detail` comme première cible stable;
2. `add` comme signal d'intention plus fort;
3. `purchase` comme cible business forte et plus rare;
4. score pondéré multi-signal si nécessaire.

## Anti-Leakage

- Les features session doivent être calculées uniquement à partir du préfixe observé.
- Les features produit globales doivent respecter le split temporel ou être documentées comme baseline offline.
- Le suffixe futur sert uniquement aux labels et métriques.
- Les candidats d'évaluation doivent inclure les produits cibles futurs sans utiliser leurs features futures.

## Features Cibles

### Session

- nombre d'événements observés;
- nombre d'interactions produit;
- nombre de produits uniques;
- durée observée;
- dernier type d'événement;
- présence d'une recherche;
- présence d'un ajout panier.

### Produit

- popularité detail/add/purchase;
- proxy de conversion;
- catégorie hashée;
- price bucket;
- disponibilité vecteur description;
- disponibilité vecteur image.

### Interaction Session-Produit

- candidat vu dans le préfixe;
- candidat ajouté dans le préfixe;
- même catégorie qu'un produit observé;
- score de co-visitation;
- score de co-cart;
- score de similarité contenu;
- présence dans résultats de recherche.

## Évaluation

Les métriques principales seront:

- `Recall@K`;
- `Precision@K`;
- `NDCG@K`;
- `MAP@K`;
- `HitRate@K`;
- couverture catalogue.

Les métriques de classification peuvent rester secondaires pour diagnostiquer des modèles pointwise, mais elles ne doivent pas porter la décision finale.

## Couche Demo

Coveo étant anonymisé, l'app utilisera une couche marketplace reconstruite avec noms, catégories lisibles, prix affichés et visuels de démonstration. Cette couche ne doit jamais être présentée comme donnée source.
