# TODO
# PLAN — Triangulator (TP Techniques de Test 2025/2026)

##  Objectif du TP
Le but de ce TP est de réfléchir et de mettre en place un ensemble de tests pour vérifier que le microservice **Triangulator** fonctionne correctement.  
Ce service doit calculer la **triangulation** d’un ensemble de points 2D à partir de données binaires récupérées depuis un autre composant appelé **PointSetManager**.  

L’idée est donc de tester la fiabilité, la justesse et la performance du service avant même d’écrire tout le code.  
Ce document sert donc de plan de tests, c’est-à-dire une sorte de feuille de route pour savoir **quoi tester, pourquoi et comment**.

---

##  1. Les principales parties à tester

Le projet est composé de plusieurs fichiers Python.  
Pour chaque partie, j’ai essayé d’imaginer quels tests seraient utiles et pourquoi.

---

### A. Conversion binaire (fichier `binary.py`)

Ces fonctions servent à convertir les ensembles de points et de triangles en **format binaire**, car c’est ainsi que les composants communiquent entre eux.

**Pourquoi les tester ?**  
Parce qu’une petite erreur dans la conversion pourrait casser tous les échanges entre services.

**Ce que je veux vérifier :**
- que l’encodage et le décodage fonctionnent bien dans les deux sens (encode → decode → même résultat),
- que les erreurs sont bien détectées (par exemple un buffer trop court, des coordonnées invalides…),
- que les indices des triangles sont valides.

**Exemples de cas de test :**
| Méthode | Ce que je teste | Cas envisagés |
|----------|----------------|---------------|
| `encode_pointset()` | Encodage correct | 0 point, plusieurs points, doublons, NaN/Inf |
| `decode_pointset()` | Décodage correct | buffer tronqué, nombre de points invalide |
| `encode_triangles()` | Indices valides | indice hors bornes → erreur |
| `decode_triangles()` | Reconstruction complète | buffer incomplet → erreur |

---

### B. Calcul de la triangulation (fichier `algo.py`)

C’est le cœur du service : il calcule les triangles à partir des points.

**Pourquoi les tester ?**  
Pour s’assurer que le calcul est juste, même dans des cas limites.

**Cas à tester :**
| Cas | Résultat attendu |
|------|------------------|
| Moins de 3 points | Aucun triangle |
| 3 points non colinéaires | 1 triangle |
| Points colinéaires | 0 triangle |
| Polygone convexe (5 points) | n-2 triangles |
| Points très proches | Pas de triangle "dégénéré" |

Ces tests permettent de vérifier la justesse de l’algorithme sans forcément avoir encore toute l’implémentation.

---

### C. Communication réseau (fichier `client.py`)

Cette partie sert à récupérer les points auprès du **PointSetManager** via une requête HTTP.

**Pourquoi les tester ?**  
Parce que si le service amont ne répond pas correctement, il faut que notre programme sache gérer les erreurs sans planter.

**Cas envisagés :**
| Cas | Résultat attendu |
|------|------------------|
| ID valide | Retourne le PointSet en binaire |
| ID inexistant | Erreur propre (exception ou 404) |
| Service indisponible / timeout | Erreur gérée (pas de crash) |

---

### D. Routes de l’API Flask (fichier `app.py`)

C’est l’API que les clients externes vont utiliser.  
Elle doit répondre correctement aux requêtes et renvoyer les bons codes HTTP.

**Tests envisagés :**
| Endpoint | Ce que je veux vérifier | Résultat attendu |
|-----------|--------------------------|------------------|
| `/healthz` | Vérifie que le service est disponible | 200 + "ok" |
| `/triangulate/<id>` | Test complet de la triangulation | 200 si ok, 422 si données invalides, 502 si erreur serveur |
| Mauvaise méthode HTTP | Ex: POST au lieu de GET | 405 |

---

### E. Tests de performance

Ces tests seront faits à part, car ils peuvent être longs.  
Le but est de mesurer si le service reste rapide quand on augmente le nombre de points.

| Fonction | Données | Temps visé |
|-----------|----------|------------|
| `encode_pointset()` / `decode_pointset()` | 10 000 points | < 1 seconde |
| `triangulate_fan()` | 4 000 points | < 2 secondes |

---

### F. Qualité et couverture

Pour finir, il faut vérifier que le code est bien écrit et bien couvert par les tests.

| Outil | Objectif |
|--------|-----------|
| **pytest** | Exécuter tous les tests |
| **coverage** | Vérifier le taux de couverture (objectif : ~85%) |
| **ruff** | Vérifier la qualité du code (aucune erreur) |
| **pdoc3** | Générer la documentation automatique |

---

##  2. Résumé des cas de test prévus

| Cas | Fichier concerné | Objectif | Résultat attendu |
|------|------------------|-----------|------------------|
| 0 point | binary.py / algo.py | Cas limite | Aucun triangle |
| 3 points | algo.py | Cas minimal | 1 triangle |
| Points colinéaires | algo.py | Cas dégénéré | 0 triangle |
| Buffer tronqué | binary.py | Détection d’erreur | Exception |
| Valeurs NaN / Inf | binary.py | Données invalides | Exception |
| API `/healthz` | app.py | Vérifier disponibilité | 200 + "ok" |
| API `/triangulate/<id>` | app.py | Vérifier comportement complet | 200 / 422 / 502 |
| Mauvaise méthode HTTP | app.py | Vérifier REST | 405 |

---

##  3. Organisation prévue du projet

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
