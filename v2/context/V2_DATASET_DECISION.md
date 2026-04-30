# Décision Dataset V2

## Décision

Le coeur de la v2 doit utiliser **Coveo SIGIR eCom 2021**.

Cette décision maximise la crédibilité du recommender: Coveo apporte des sessions, des vues détail, des ajouts panier, des achats, des recherches, des timestamps, des catégories, des price buckets et des vecteurs de contenu. C'est plus proche d'un environnement e-commerce réel qu'un dataset transactionnel pur.

`Online Retail II` reste dans `v1/` comme baseline historique. Il ne doit plus structurer la v2.

## Pourquoi Coveo

| Critère | Coveo |
| --- | --- |
| Sessions | Oui |
| Vues produit | Oui |
| Ajouts panier | Oui |
| Achats | Oui |
| Recherche | Oui |
| Timestamps | Oui |
| Catégories | Oui, hashées |
| Prix | Oui, par bucket |
| Texte produit | Oui, vecteurs |
| Image produit | Oui, vecteurs |
| Noms produits lisibles | Non |
| Photos brutes | Non |

Coveo est donc meilleur pour défendre la logique ML. Sa faiblesse principale est l'anonymisation, qui sera traitée par une couche marketplace de démonstration.

## Limites D'Online Retail II

Online Retail II contient des achats mais pas les signaux amont d'une session:

- pas de vues produit;
- pas de recherche;
- pas d'ajout panier;
- pas d'abandon;
- pas d'impressions;
- pas de métadonnées produit riches;
- pas de contexte session.

Il reste utile pour expliquer la baseline v1: classification client-produit, métriques classiques et modèle transactionnel. Mais il ne répond pas au cas d'usage cible: recommander pendant une session active.

## Alternatives Considérées

| Dataset | Points forts | Limites |
| --- | --- | --- |
| Online Retail II | Simple, transactions réelles, historique déjà exploité | Pas de sessions ni signaux amont |
| Coveo SIGIR eCom 2021 | Sessions, vues, carts, achats, recherches, metadata | Anonymisé, pas de visuels bruts |
| RetailRocket | Événements e-commerce, item properties | Moins riche pour la présentation |
| H&M Personalized Fashion | Catalogue visuel riche | Projet plus lourd, autre domaine |
| Amazon Reviews | Metadata très riche | Pas un log direct de sessions e-commerce |

Verdict: Coveo est le meilleur compromis pour un projet ML recommender défendable.

## Fichiers Coveo

```text
v2/data/coveo/raw/browsing_train.csv
v2/data/coveo/raw/search_train.csv
v2/data/coveo/raw/sku_to_content.csv
```

## Couche Marketplace Demo

La future table de présentation sera construite dans:

```text
v2/data/coveo/processed/coveo_product_catalog_demo.csv
```

Colonnes proposées:

- `product_sku_hash`;
- `demo_product_name`;
- `demo_category`;
- `price_bucket`;
- `display_price`;
- `image_url`;
- `image_source`;
- `description_short`;
- `is_demo_ready`.

Cette table sert à rendre la démo lisible. Elle ne remplace pas les données source et doit être explicitement présentée comme reconstruite.

## Formulation Recommandée Pour L'App

> Le moteur de recommandation utilise Coveo SIGIR eCom 2021, un dataset de sessions e-commerce réelles anonymisées. Les noms et visuels affichés dans la marketplace sont reconstruits pour la démonstration; les recommandations sont calculées à partir des signaux comportementaux et métadonnées produit du dataset source.

## Impact Sur La Roadmap

1. Parser `browsing_train.csv`.
2. Définir le protocole `observed_prefix` / `future_suffix`.
3. Construire candidats et labels.
4. Ajouter features search et product content.
5. Évaluer avec métriques de ranking.
6. Construire la marketplace demo.
7. Présenter les résultats et limites dans Streamlit.
