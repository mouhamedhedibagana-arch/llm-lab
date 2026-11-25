# Lab 7 — Ajouter une recherche documentaire (RAG)

[Sommaire](README.md) · [← Lab 6](lab-6.md) · [Lab 8 →](lab-8.md)


**Durée** : 60 min · **Prérequis** : Lab 6, assistant `eps-assistant` en service · **Objectif** : donner à l'assistant les documents de l'école au moment de chaque question, mesurer ce que cela change, puis mettre à jour ses connaissances sans réentraîner aucun modèle.

## Le principe

Au Lab 6, le modèle a **appris** les informations de l'école : pour en changer une, il faut le réentraîner. Le **RAG** (*Retrieval-Augmented Generation*, génération augmentée par la recherche) procède autrement : les informations restent dans un fichier texte, et l'application les **fournit** au modèle au moment de la question.

1. Au démarrage, l'application découpe le fichier `app/connaissances.md` en passages, un par paragraphe, et calcule pour chacun un **embedding** : un vecteur de nombres qui représente son sens. C'est un second modèle, `bge-m3`, qui fait ce calcul.
2. À chaque question, elle calcule l'embedding de la question et retient les 3 passages les plus proches, s'ils dépassent un **seuil de similarité** (0,45).
3. Elle ajoute ces passages au prompt système, avec la consigne de répondre à partir d'eux.

Le bas du schéma d'ensemble, en tête du sommaire de la formation, montre ce trajet étape par étape.

Le code est déjà dans votre dépôt, désactivé par défaut. Quatre réglages du fichier `.env` le pilotent :

| Réglage | Valeur par défaut | Rôle |
| --- | --- | --- |
| `RAG` | `0` | `1` active la recherche |
| `EMBED_MODEL` | `bge-m3` | Modèle d'embedding, servi par Ollama |
| `RAG_K` | `3` | Nombre de passages au plus |
| `RAG_SEUIL` | `0.45` | Similarité minimale d'un passage ; en dessous, il est écarté |

## Tâche 1 — Lire les connaissances et le code

1. Sur GitHub, ouvrez `app/connaissances.md`. *Attendu : un titre `##` par thème (« Identité et contact », « Formations », « Frais de scolarité 2026/2027 »…) et un paragraphe par information, 53 en tout. Les lignes qui commencent par `>` sont des notes, ignorées par l'application.*
2. Ouvrez `app/main.py` et repérez les fonctions `lire_passages`, `rechercher` et `consigne`. Répondez :
   - Quelle opération mathématique mesure la proximité entre la question et un passage ?
   - À quel endroit les passages sont-ils ajoutés aux messages envoyés au modèle ?
   - Que se passe-t-il si aucun passage ne dépasse le seuil ?

Si `app/connaissances.md` n'existe pas dans votre dépôt, voyez « Si ça bloque ».

## Tâche 2 — Installer le modèle d'embedding

Connectez-vous à l'instance `llm-lab` par Session Manager.

```bash
sudo -i
cd /opt/llm
docker compose exec ollama ollama pull bge-m3
docker compose exec ollama ollama list
```

*Attendu : un téléchargement d'environ 1,2 Go (11 secondes pendant le test), puis `success`. La liste montre `bge-m3:latest`, `eps-assistant:latest` et `llama3.2:3b`.*

## Tâche 3 — Activer le RAG avec le modèle d'origine

On commence avec `llama3.2:3b`, le modèle qui inventait l'adresse de l'école au Lab 6 : le RAG suffit-il, sans fine-tuning ?

1. Changez le modèle, activez la recherche, puis libérez la mémoire occupée par le modèle affiné du Lab 6.

```bash
sed -i 's|^MODEL=.*|MODEL=llama3.2:3b|' .env
grep -q '^RAG=' .env || echo 'RAG=1' >> .env
docker compose up -d --no-build
docker compose exec ollama ollama stop eps-assistant
```

*Attendu : `Container llm-app-1 Started`, et aucun message d'erreur.*

La dernière commande décharge `eps-assistant` de la mémoire, sans le supprimer. Sans elle, il y resterait 5 minutes, à côté de `llama3.2:3b` et de `bge-m3` : pendant le test, la mémoire utilisée est alors montée à 7,1 Go sur 7,8.

2. Attendez que l'application ait calculé les embeddings des 53 passages (52 secondes pendant le test), puis vérifiez son état.

```bash
sleep 60
docker compose logs app | grep index
curl -s localhost/api/health; echo
```

*Attendu : une ligne `{"evenement": "index", "passages": 53, "duree_s": 52.2}` ou proche, puis :*

```json
{"ok":true,"version":"...","modele":"llama3.2:3b","modele_pret":true,"rag":true,"embedding":"bge-m3","embedding_pret":true,"passages":53}
```

Si `passages` vaut 0, l'index n'est pas encore prêt : attendez 30 secondes et relancez `curl`. L'index est recalculé à chaque redémarrage de l'application.

## Tâche 4 — Voir ce que la recherche trouve

La route `/api/recherche` montre les passages retenus pour une question, avec leur similarité. Remplacez `MON-CODE`.

```bash
CODE=MON-CODE
voir() {
  curl -s -G localhost/api/recherche --data-urlencode "q=$1" --data-urlencode "k=3" \
    -H "x-access-code: $CODE" | python3 -m json.tool --no-ensure-ascii
}
voir "Combien coûte le cycle ingénieur ?"
```

*Attendu : trois passages, du plus proche au moins proche. Le premier est le numéro 24, « Frais de scolarité 2026/2027 », avec une similarité d'environ 0,72.*

Essayez ensuite :

```bash
voir "Y a-t-il un club de robotique ?"
voir "Explique le cloud en une phrase."
```

*Attendu : pour le club, le passage 43 en tête (0,634 pendant le test). Pour le cloud, aucune similarité ne dépasse 0,45 (0,339 au plus pendant le test) : l'application ne donnera aucun passage au modèle, qui répondra avec ses connaissances générales.*

## Tâche 5 — Discuter avec l'assistant augmenté

1. Rechargez l'interface web. *Attendu : l'en-tête affiche « llama3.2:3b · modèle prêt · RAG prêt ».*
2. Posez ces questions. Sous chaque réponse, une ligne « Sources » liste les passages utilisés, avec leur similarité ; survolez-en un pour lire son texte. Comptez 30 à 70 secondes par réponse : le prompt s'allonge des passages, et le modèle d'origine écrit des réponses plus longues que le modèle affiné.

| Question | Réponse attendue | Sources attendues |
| --- | --- | --- |
| Où se trouve l'école ? | Route Ceinture Sahloul, Entrée Kalaa Sghira, 4021 Sousse | [2], [8], [1] |
| Combien coûte le cycle ingénieur pour un étudiant tunisien ? | 7 849 DT par an, en trois tranches | [24], [23], [26] |
| Y a-t-il un club de robotique ? | Le Club Polyrobots | [43], [42] |
| Explique le cloud en une phrase. | Une réponse générale | Aucune ligne « Sources » |

3. Comparez avec le Lab 6 : le modèle d'origine, qui inventait l'adresse, la donne maintenant juste, sans aucun entraînement.

## Tâche 6 — Mesurer, et comparer avec le fine-tuning

Le script `evaluer.py` peut interroger l'application elle-même, une fois avec la recherche et une fois sans. Il tourne dans le conteneur de l'API, et joint l'application par son nom de service, `app`.

```bash
docker compose run --rm -v /opt/llm/finetune:/f -w /f app \
  python evaluer.py --api http://app:8000 --code $CODE --n 5
```

*Attendu, après 5 à 6 minutes : deux lignes. La version avec RAG doit avoir un rappel nettement plus haut. Sortie obtenue pendant le test :*

```
llama3.2:3b avec RAG         rappel moyen  72.3 % · réponses à plus de 80 % : 2/5 · 40 s par réponse · 200 s
llama3.2:3b sans RAG         rappel moyen  43.0 % · réponses à plus de 80 % : 0/5 · 26 s par réponse · 129 s
```

Recommencez avec le modèle affiné du Lab 6, pour obtenir les quatre combinaisons :

```bash
sed -i 's|^MODEL=.*|MODEL=eps-assistant|' .env
docker compose up -d --no-build
docker compose exec ollama ollama stop llama3.2:3b
sleep 60
docker compose run --rm -v /opt/llm/finetune:/f -w /f app \
  python evaluer.py --api http://app:8000 --code $CODE --n 5
```

*Attendu, après 3 à 4 minutes : deux lignes. Pendant le test, le modèle affiné a obtenu 100 % avec et sans RAG sur ces 5 questions.*

Reportez vos quatre rappels dans un tableau : modèle d'origine ou affiné, avec ou sans RAG. Pour comparaison, voici les rappels obtenus sur les 58 questions pendant la préparation :

| | Sans RAG | Avec RAG |
| --- | --- | --- |
| `llama3.2:3b` (modèle d'origine) | 19 % | 59 % |
| `eps-assistant` (modèle affiné) | 89 % | 90 % |

Attention à la lecture de ces chiffres : le rappel compte les mots de la réponse de référence. Le modèle affiné a appris ces phrases mot pour mot, alors que le modèle d'origine reformule les passages qu'on lui donne. Ouvrez `finetune/evaluation.json` : une réponse juste mais reformulée y obtient un rappel moyen.

## Tâche 7 — Mettre à jour les connaissances sans réentraîner

L'école annonce sur son site une session d'examens de langue. L'assistant ne la connaît pas encore.

1. Dans l'interface, demandez : « Quand a lieu la session TEF Canada organisée à l'école ? » *Attendu : l'assistant ne sait pas, ou invente une date.*
2. Sur GitHub, ouvrez `app/connaissances.md`, cliquez le crayon **Edit**, et ajoutez à la fin du fichier, en laissant une ligne vide avant chaque bloc :

```markdown
## Événements

L'école organise une session d'examens TEF, TEF Canada, TEFAQ et DFP le 14 novembre 2026, de 8 h à 16 h.
```

3. Cliquez **Commit changes**, puis suivez l'onglet **Actions** jusqu'au vert (environ une minute pendant le test).
4. Vérifiez sur l'instance que l'application a relu le fichier. *Attendu : `"passages":54`. Si la valeur est 0, l'index est en cours de calcul : attendez une minute.*

```bash
curl -s localhost/api/health; echo
```

5. Reposez la question dans l'interface. *Attendu : une réponse comme « La session TEF Canada se tiendra le 14 novembre 2026, de 8 h à 16 h. », avec la source [54] « Événements » (similarité 0,72 pendant le test).*

Aucun modèle n'a été réentraîné : il a suffi de modifier un fichier texte et de laisser le pipeline redéployer.

## Point de contrôle

- [ ] L'en-tête de l'interface affiche « RAG prêt ».
- [ ] Une réponse sur les frais affiche ses sources, avec le passage [24].
- [ ] Vous donnez les rappels avec et sans RAG.
- [ ] L'assistant connaît la session TEF après votre modification de `connaissances.md`.

## Questions de synthèse

1. Comparez le fine-tuning du Lab 6 et le RAG : que faut-il refaire quand les frais changent ? Lequel des deux permet de citer ses sources ?
2. À quoi sert le seuil de 0,45 ? Que se passerait-il avec un seuil de 0 ? Avec un seuil de 0,9 ?
3. L'application ne cherche qu'à partir de la dernière question. Que se passe-t-il si l'on demande « Combien coûte le cycle ingénieur ? », puis « Et pour un étudiant étranger ? » ? Comment l'améliorer ?
4. Demandez « Est-ce qu'il y a un internat à l'EPS ? ». Aucun passage n'en parle, et pourtant le modèle peut inventer. Pourquoi la consigne ne suffit-elle pas ?

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| `app/connaissances.md` n'existe pas dans votre dépôt, ou `/api/health` ne contient pas `"rag"` | Votre dépôt a été créé avant l'ajout du RAG. Dans CloudShell : `git clone https://github.com/COMPTE/llm-lab.git && cd llm-lab`, `git remote add modele https://github.com/nevermind78/llm-lab.git`, `git fetch modele`, `git checkout modele/main -- app tests finetune docker-compose.yml`, `git config user.name "PRÉNOM"`, `git config user.email "COMPTE@users.noreply.github.com"`, `git commit -m "Récupérer le RAG"`, `git push`. Au mot de passe, collez un jeton GitHub (**Settings** > **Developer settings** > **Personal access tokens**, droit `repo`) |
| En-tête : « RAG sans embedding » | `bge-m3` n'est pas installé : refaites la tâche 2 |
| `"passages":0` après une minute | `docker compose logs app --tail 20` : la ligne `index_reporte` indique que l'index a échoué ; posez une question pour le relancer |
| Réponse « Échec : recherche impossible » | Ollama ne répond pas ou `bge-m3` est absent : `docker compose exec ollama ollama list` |
| `python3: No module named json.tool` ou caractères `é` | Retirez `--no-ensure-ascii` ; les accents s'afficheront codés, sans autre conséquence |
| `evaluer.py` : `Connection refused` | Gardez `--api http://app:8000` : dans le conteneur, l'application ne s'appelle pas `localhost` |
| Réponses très lentes, ou « erreur du serveur de modèle » | Mémoire saturée par trois modèles chargés : `docker compose exec ollama ollama ps`, puis `docker compose exec ollama ollama stop NOM` pour le modèle inutilisé, et `free -h` |
| Après le commit, `passages` vaut toujours 53 | Le pipeline n'a pas fini, ou a échoué : onglet **Actions**. Vérifiez aussi la ligne vide avant `## Événements` |

---

[Sommaire](README.md) · [← Lab 6](lab-6.md) · [Lab 8 →](lab-8.md)
