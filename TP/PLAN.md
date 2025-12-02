# PLAN — Triangulator (TP Techniques de Test 2025/2026)

---

## Objectif du TP

Le but de ce TP est de mettre en place une **démarche de tests** permettant de valider le bon fonctionnement du micro-service **Triangulator**.

Ce service a pour rôle de calculer une **triangulation** d’un ensemble de points en 2D, reçus depuis un autre composant appelé **PointSetManager**, sous forme de **données binaires**.

L’objectif principal n’est pas de coder rapidement l’algorithme, mais de **définir et construire des tests pertinents avant toute implémentation** selon une démarche **Test First / TDD**.

Ce plan de tests décrit donc :

- ce qui doit être testé,
- pourquoi ces tests sont nécessaires,
- comment ils seront organisés.

---

## 1. Parties principales à tester

Le projet est divisé en plusieurs modules.  
Pour chacun, des tests spécifiques sont prévus afin de couvrir tous les aspects du fonctionnement du service.

---

## A. Tests du format binaire — `binary.py`

Les fonctions de ce fichier assurent la conversion entre :

- une représentation Python des points/triangles,
- et leur **format binaire compact**, utilisé lors des échanges réseau.

### Pourquoi les tester ?

Une erreur à ce niveau aurait un impact sur **toute la chaîne de traitement** :  
données incorrectes → triangulation fausse → réponse erronée au client.

### Points contrôlés

- Bon fonctionnement de l’**encodeur / décodeur en aller-retour**
- Détection des **buffers incomplets ou corrompus**
- Rejet des données invalides
- Validation des indices de sommets de triangles

### Exemples de cas testés

| Méthode | Objectif |
|---------|----------|
| `encode_pointset()` | Cas normal, 0 point, nombreux points, doublons, valeurs NaN / Inf |
| `decode_pointset()` | Taille incohérente, buffer tronqué |
| `encode_triangles()` | Indices hors bornes ou négatifs |
| `decode_triangles()` | Reconstruction des sommets / triangles |

---

---

## B. Tests de l’algorithme — `algo.py`

Ce module effectue le calcul de la triangulation.

### Pourquoi les tester ?

C’est la partie **fonctionnelle principale** du service :  
Les résultats doivent être corrects quelle que soit la configuration des points.

### Cas étudiés

| Situation | Résultat attendu |
|-------------|------------------|
| Moins de 3 points | 0 triangle |
| 3 points non colinéaires | 1 triangle |
| Points colinéaires | 0 triangle |
| Polygone convexe (≥5 points) | n-2 triangles |
| Coordonnées négatives | Fonctionnement normal |
| Points dupliqués | Pas d’erreur système |
| Triangles très petits | Stabilité numérique |

Ces tests permettent de **décrire les comportements cibles de l’algorithme** indépendamment de son implémentation actuelle.

---

---

## C. Tests du client HTTP — `client.py`

Cette couche réalise la communication avec le `PointSetManager`.

### Objectifs

- Tester la récupération correcte des données
- Simuler des erreurs réseau
- Vérifier que les erreurs sont **correctement remontées**

### Cas couverts

| Cas | Comportement attendu |
|-------|----------------------|
| ID valide | Retour binaire correct |
| ID introuvable | Erreur propagée proprement |
| Service indisponible | Exception maîtrisée |
| Timeout | Pas de crash système |

Ces tests utilisent le **mocking** pour simuler les réponses externes.

---

---

## D. Tests de l’API Flask — `app.py`

Ces tests vérifient le comportement du service du point de vue d’un client HTTP.

### Endpoints contrôlés

| Route | Vérification | Code attendu |
|-------|----------------|---------------|
| `/healthz` | Disponibilité du service | 200 + `"ok"` |
| `/triangulate/<id>` | Chaîne complète (fetch + decode + algo + encode) | 200 |
| Données invalides | Gestion propre | 422 |
| Erreur service amont | Robustesse | 502 |
| Méthode différente de GET | Conformité REST | 405 |
| Données corrompues | Sécurité | 422 ou 500 |

---

---

## E. Tests de performance

Ces tests sont séparés du reste (`pytest.mark.perf`) car les calculs peuvent être longs.

### Objectifs

- Vérifier que :
  - la conversion binaire est rapide même avec de grandes quantités de points,
  - l’algorithme reste performant pour des jeux de données réalistes.

### Scénarios envisagés

| Fonction | Charge test | Seuil |
|-----------|--------------|-------|
| `encode_pointset()` / `decode_pointset()` | 10 000 points | < 1 s |
| `triangulate_fan()` | 4 000 points | < 2 s |
| Chaîne complète | 500 points | < 3 s |

---

---

## F. Qualité de code et couverture

Outre la validité fonctionnelle, le code doit respecter des standards de qualité.

| Outil | Rôle |
|--------|------|
| **pytest** | Exécution de tous les tests |
| **coverage** | Mesure de la couverture (>80% visé) |
| **ruff** | Respect des règles de style |
| **pdoc3** | Génération de la documentation |

---

---

## 2. Synthèse des tests

| Cas | Module | Objectif |
|------|--------|-----------|
| 0 point | `binary.py`, `algo.py` | Cas limite |
| 3 points | `algo.py` | Cas minimal |
| Colinéarité | `algo.py` | Cas dégénéré |
| Buffer tronqué | `binary.py` | Validation données |
| NaN / Inf | `binary.py` | Rejet entrées invalides |
| `/healthz` | `app.py` | Disponibilité |
| `/triangulate/<id>` | `app.py` | Workflow complet |
| ID invalide / méthode incorrecte | `app.py` | Robustesse API |
| Gros volumes | `binary.py`, `algo.py` | Performance |

---

---

## 3. Organisation du projet

```text
triangulator-tp/
├─ src/
│  └─ triangulator/
│     ├─ app.py
│     ├─ binary.py
│     ├─ algo.py
│     └─ client.py
├─ tests/
│  ├─ unit/
│  │  ├─ test_binary.py
│  │  └─ test_algo.py
│  ├─ api/
│  │  └─ test_api.py
│  └─ perf/
│     └─ test_perf.py
├─ PLAN.md
├─ README.md
├─ RETEX.md
├─ requirements.txt
├─ dev_requirements.txt
└─ pyproject.toml
