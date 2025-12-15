# RETEX — Retour d’expérience détaillé

## Contexte général

Ce projet s’inscrit dans une démarche de **développement orienté tests (Test First / TDD)** appliquée à un micro-service de triangulation. Contrairement à une approche classique où l’algorithme est implémenté en premier, l’objectif ici était de **concevoir les tests avant l’implémentation**, puis de faire évoluer ces tests en fonction des choix algorithmiques réels et des contraintes rencontrées.

Le retour d’expérience présenté ci-dessous couvre l’ensemble du processus, depuis les premiers tests naïfs jusqu’à l’implémentation finale basée sur la **triangulation de Delaunay (algorithme de Bowyer-Watson)**.

---

## 1. Phase initiale : tests avant implémentation

### Objectif

Lors des premières séances, l’objectif était de **définir ce que devait faire le système**, indépendamment de la manière dont il serait implémenté.

Les tests ont donc été écrits alors que :

* les fonctions de triangulation renvoyaient des valeurs vides ou factices,
* les codecs binaires levaient des `NotImplementedError`,
* l’API Flask ne faisait que répondre partiellement.

Cette phase a permis de **formaliser les exigences fonctionnelles** du projet.

---

## 2. Évolution des tests unitaires de l’algorithme (`test_algo.py`)

### 2.1 Version initiale (approche naïve)

Au départ, l’algorithme envisagé était une triangulation simple de type **fan** (triangulation en éventail). Les premiers tests vérifiaient uniquement :

* moins de 3 points → aucun triangle,
* 3 points → 1 triangle,
* polygone convexe → `n - 2` triangles.

Ces tests étaient suffisants pour une implémentation simple, mais ils se sont révélés **trop restrictifs**.

---

### 2.2 Problèmes rencontrés

Lorsque l’algorithme a commencé à être implémenté et testé sur des cas plus réalistes, plusieurs limites sont apparues :

* dépendance forte à l’ordre des points,
* triangles qui se chevauchent sur des formes concaves,
* résultats incorrects pour des points non triés,
* instabilité numérique sur certains jeux de données.

Ces échecs ont été **mis en évidence directement par les tests**, ce qui a motivé un changement d’approche.

---

### 2.3 Passage à la triangulation de Delaunay

Le choix s’est porté sur l’algorithme de **Bowyer-Watson**, permettant de construire une triangulation de Delaunay.

Ce changement a eu un impact direct sur les tests :

* certains tests supposant strictement `n - 2` triangles ont dû être ajustés,
* l’ordre d’entrée des points n’est plus un critère de validité,
* la robustesse géométrique est devenue un critère central.

#### Exemple d’évolution d’un test

* **Avant** : `test_many_points` vérifiait uniquement `len(tris) == n - 2`.
* **Après** : le test vérifie que :

  * des triangles sont produits,
  * les indices sont valides,
  * aucune régression topologique n’apparaît.

Ainsi, les tests sont passés d’une logique **quantitative** à une logique **qualitative et structurelle**.

---

## 3. Évolution des tests du codec binaire (`test_binary.py`)

### 3.1 Tests initiaux

Les premiers tests validaient uniquement le principe de **round-trip** :

```
encode → decode → données identiques
```

Cela permettait de vérifier que la représentation binaire était cohérente.

---

### 3.2 Renforcement progressif

Avec l’avancement du projet, les tests ont été enrichis pour couvrir des cas critiques :

* gestion des listes vides,
* gestion d’un seul point,
* rejet explicite des valeurs `NaN` et `Inf`,
* détection des buffers tronqués ou incohérents,
* validation stricte des indices de triangles.

Ces évolutions ont conduit à une implémentation plus défensive du codec, avec des exceptions explicites plutôt que des erreurs silencieuses.

---

## 4. Évolution des tests d’API (`test_api.py`)

### 4.1 Approche initiale

Les premiers tests d’API se limitaient à :

* vérifier la présence des routes,
* tester les codes HTTP de base (`200`, `404`).

---

### 4.2 Introduction du mocking

Pour découpler totalement les tests du réseau et du serveur externe, l’utilisation de `patch` a été généralisée.

Cela a permis de :

* simuler des réponses valides,
* simuler des erreurs amont (timeouts, données corrompues),
* vérifier la traduction correcte des erreurs en codes HTTP (`422`, `502`, `504`).

Cette étape a marqué le passage d’un simple test de routes à de véritables **tests d’intégration contrôlés**.

---

## 5. Tests de performance et impact sur l’implémentation

Les tests de performance ont joué un rôle déterminant dans l’évolution de l’algorithme.

### 5.1 Version initiale

Les premières implémentations présentaient des temps d’exécution trop élevés sur des jeux de données moyens (500+ points). Les tests échouaient systématiquement.

### 5.2 Optimisations guidées par les tests

Les tests ont permis d’identifier :

* des parcours inutiles de listes,
* des suppressions coûteuses,
* des structures de données inadaptées.

Le remplacement de certaines listes par des dictionnaires (ex. comptage d’arêtes) a permis de réduire significativement les temps d’exécution.

Les tests de performance sont ainsi devenus un **outil de validation algorithmique**, et non un simple indicateur.

---

## 6. Bilan global

Ce projet a montré que :

* les tests permettent de **révéler les limites d’un algorithme**,
* ils guident les choix de conception,
* ils sécurisent les refactorisations importantes,
* ils forcent à formaliser les cas limites dès le départ.

Le passage à la triangulation de Delaunay n’aurait pas été justifié sans l’échec répété des tests sur l’approche naïve. À l’inverse, l’implémentation finale est aujourd’hui stable précisément parce qu’elle est soutenue par une batterie de tests cohérente et évolutive.

Ce retour d’expérience confirme que les tests ne sont pas une étape finale, mais un **outil central du processus de développement logiciel**.
