# Synthèse D'Audit Data Coveo

## Objectif

Ce document synthétise l'audit initial du dataset **Coveo SIGIR eCom 2021** et sert de référence pour les pages Streamlit `Dataset & Insights`, `Training & Validation` et `Impact & Limites`.

Rapports détaillés:

- `v2/results/coveo_data_audit.json`
- `v2/results/coveo_data_audit.md`

## Résumé Executive

Coveo est un excellent socle pour la v2: il contient de vraies sessions e-commerce anonymisées avec vues produit, ajouts panier, retraits, achats, recherches, timestamps et métadonnées produit. Il permet de construire un recommender plus crédible qu'une approche transactionnelle pure.

La principale limite est l'anonymisation: les produits, catégories, noms et images ne sont pas directement lisibles. L'app finale doit donc distinguer clairement:

- la couche ML, entraînée sur les signaux Coveo réels;
- la couche marketplace, reconstruite pour rendre la démonstration compréhensible.

## Fichiers Audités

| Fichier | Rôle |
| --- | --- |
| `v2/data/coveo/raw/browsing_train.csv` | Log principal de navigation et événements produit |
| `v2/data/coveo/raw/search_train.csv` | Recherches, résultats affichés, produits cliqués |
| `v2/data/coveo/raw/sku_to_content.csv` | Métadonnées produit, catégories, prix, vecteurs texte/image |

## Volumétrie

| Métrique | Valeur |
| --- | ---: |
| Lignes browsing | 36,079,307 |
| Sessions uniques | 4,934,699 |
| Produits uniques dans browsing | 57,483 |
| Événements produit | 10,431,611 |
| Lignes search | 819,516 |
| Sessions avec search | 550,100 |
| Produits dans metadata | 66,386 |

Cette volumétrie est suffisante pour construire et évaluer un recommender session-based sérieux.

## Structure Browsing

| Event type | Count |
| --- | ---: |
| `pageview` | 25,647,696 |
| `event_product` | 10,431,611 |

Les événements produit représentent environ 28.9% du browsing. Les pageviews peuvent enrichir le contexte, mais la première version du recommender doit se concentrer sur les interactions produit.

## Actions Produit

| Product action | Count |
| --- | ---: |
| `detail` | 9,707,890 |
| `add` | 329,557 |
| `remove` | 316,316 |
| `purchase` | 77,848 |

Interprétation:

- `detail` est le signal stable de départ;
- `add` est plus rare mais indique une intention forte;
- `purchase` est le signal business le plus fort mais le plus sparse;
- `remove` pourra aider plus tard à modéliser les corrections panier.

## Qualité Session

| Métrique | Valeur |
| --- | ---: |
| Sessions avec `detail` | 3,260,353 |
| Sessions avec `add` | 214,684 |
| Sessions avec `purchase` | 53,209 |
| Sessions avec `remove` | 57,441 |

Distribution des longueurs:

| Statistique | Événements/session |
| --- | ---: |
| Min | 1 |
| P25 | 2 |
| Médiane | 3 |
| P75 | 8 |
| P90 | 17 |
| P95 | 27 |
| Max | 206 |

La majorité des sessions est courte. Le protocole d'évaluation devra donc définir des règles d'éligibilité strictes pour éviter des préfixes vides ou des suffixes sans cible.

## Search

| Métrique | Valeur |
| --- | ---: |
| Lignes search | 819,516 |
| Sessions search uniques | 550,100 |
| Lignes avec résultats produits | 602,754 |
| Lignes avec produits cliqués | 179,495 |

Search sera utile après stabilisation du parser browsing pour:

- hard negatives;
- features de contexte d'intention;
- explications de recommandations;
- distinction produits affichés mais non cliqués.

## Métadonnées Produit

| Métrique | Valeur |
| --- | ---: |
| Produits metadata | 66,386 |
| Lignes avec vecteur description | 31,950 |
| Lignes avec vecteur image | 28,370 |
| Lignes avec price bucket | 32,038 |
| Lignes avec catégorie | 32,052 |

La couverture metadata est partielle mais utile. Le pipeline doit accepter les valeurs manquantes sans exclure trop de produits.

## Implications Modélisation

La cible initiale ne doit pas être purchase-only, car les achats sont rares. La progression recommandée est:

1. prédire les futures interactions `detail`;
2. ajouter la cible `add`;
3. évaluer `purchase` comme cible business forte;
4. éventuellement combiner les signaux dans un score de pertinence pondéré.

## Protocole D'Évaluation Recommandé

Le Plan 4 doit mettre en place:

1. tri par `session_id_hash` et timestamp;
2. découpe en `observed_prefix` et `future_suffix`;
3. features calculées uniquement sur le préfixe;
4. labels construits uniquement depuis le suffixe;
5. ranking de candidats;
6. évaluation top K.

## Métriques Recommandées

- `Recall@10`;
- `NDCG@10`;
- `HitRate@10`;
- `Precision@10`;
- `MAP@10`;
- couverture catalogue.

## Formulations App Réutilisables

Résumé dataset:

```text
Coveo SIGIR eCom 2021 contient 36M événements de navigation anonymisés sur 4.9M sessions, avec vues produit, ajouts panier, achats, recherches, timestamps et métadonnées produit.
```

Disclaimer marketplace:

```text
Le dataset source est anonymisé. Les noms et visuels produits affichés dans la marketplace sont reconstruits pour la démonstration; le moteur de recommandation utilise les signaux comportementaux et métadonnées Coveo.
```

Limite purchase:

```text
Les achats sont le signal business le plus fort, mais ils sont rares. Le premier modèle peut s'appuyer sur les futures interactions produit et ajouts panier, puis évaluer purchase comme cible de valeur.
```

## Décision Avant Plan 4

Le Plan 3 est terminé avec `v2/src/sessionize.py`. La prochaine étape est **Plan 4: définir le protocole d'évaluation** dans `v2/src/splitting.py`, en choisissant la cible initiale, la stratégie de cutoff et les règles d'éligibilité des sessions.
