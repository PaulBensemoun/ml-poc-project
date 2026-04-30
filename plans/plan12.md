# Plan 12 — Finaliser le storytelling et la livraison

## Objectif

Transformer le projet final en livrable clair, défendable et valorisant.

## Message final à défendre

> Ce projet démontre un moteur de recommandation session-based réaliste, entraîné sur des comportements e-commerce anonymisés réels, évalué avec des métriques de ranking, et présenté via une interface marketplace reconstruite pour la démonstration.

## Actions

1. Mettre à jour `README.md` :
   - objectif du projet ;
   - choix du dataset Coveo ;
   - différence avec la v1 `Online Retail II` ;
   - architecture du projet ;
   - instructions d'installation ;
   - instructions d'entraînement ;
   - instructions de lancement Streamlit.
2. Mettre à jour les documents `context/` si le code final diverge.
3. Ajouter une section "Dataset disclosure" :
   - données anonymisées ;
   - noms/images reconstruits pour la démo ;
   - ML fondé sur vrais signaux comportementaux.
4. Ajouter une section "Model evaluation" :
   - protocole session truncation ;
   - baselines ;
   - métriques ranking ;
   - modèle final.
5. Ajouter une section "Business value" :
   - product discovery ;
   - cart conversion ;
   - cross-sell ;
   - personalization.
6. Ajouter une section "Limitations" :
   - offline evaluation ;
   - pas d'A/B test réel ;
   - données anonymisées ;
   - couche visuelle reconstruite ;
   - contraintes de performance locale.
7. Ajouter une section "Next steps" :
   - scoring temps réel ;
   - monitoring ;
   - retraining ;
   - A/B testing ;
   - calibration ;
   - deep/session models.
8. Préparer des captures d'écran de l'app si utile.
9. Vérifier que les commandes principales fonctionnent.
10. Nettoyer les fichiers obsolètes ou les marquer comme v1.

## Fichiers concernés

- `README.md`
- `context/`
- `plans/`
- `src/app.py`
- `results/recommender_metrics.csv`

## Livrables

- README final.
- Documentation alignée avec le code.
- Story produit claire.
- App présentable.
- Limites bien assumées.

## Critères de validation

- Un lecteur externe comprend le projet sans explication orale.
- Le choix Coveo est clairement justifié.
- Le protocole ML est défendable.
- Les métriques principales sont visibles.
- La couche visuelle demo est assumée et crédible.

## Risques

- README trop technique.
- Présentation trop marketing sans honnêteté ML.
- Incohérence entre docs et code final.

## Décision attendue

Définir l'angle final de présentation :

- projet ML recommender sérieux ;
- app visuelle comme preuve produit ;
- limites explicites et assumées ;
- potentiel entreprise clairement expliqué.
