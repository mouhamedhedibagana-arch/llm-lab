# Lab 6 — Spécialiser l'assistant pour Polytechnique Sousse

[Sommaire](README.md) · [← Lab 5](lab-5.md) · [Lab 7 →](lab-7.md)


**Durée** : 45 à 60 min · **Prérequis** : Lab 5, pile `llm-lab` en service · **Objectif** : remplacer le modèle généraliste par un modèle affiné sur les informations de l'École Polytechnique de Sousse, le déployer sur votre instance et mesurer le gain.

## Le principe

Un modèle généraliste ne connaît pas votre école : interrogé sur son adresse ou ses frais, il invente. Le **fine-tuning** lui fait apprendre ces informations à partir d'exemples question-réponse. La méthode utilisée, **LoRA**, n'entraîne que 0,75 % des paramètres du modèle.

L'entraînement demande une carte graphique, que le Learner Lab n'offre pas. Il a donc été fait en dehors d'AWS, et vous partez du résultat : un fichier `eps-assistant-q4_k_m.gguf` de 2 Go, mis à disposition par l'enseignant sur Google Drive. Pour l'entraîner vous-même sur votre poste, suivez la partie B du « Guide local » (`docs/guide-local-fine-tuning.md` dans votre dépôt).

[![Ouvrir dans Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/nevermind78/llm-lab/blob/main/finetune/fine_tuning_colab.ipynb)

**Votre propre assistant, sur le sujet de votre choix** : ouvrez le notebook [Google Colab](https://colab.research.google.com/github/nevermind78/llm-lab/blob/main/finetune/fine_tuning_colab.ipynb) (`finetune/fine_tuning_colab.ipynb`). Il entraîne le modèle sur la carte graphique gratuite de Colab, dépose le fichier GGUF dans votre Google Drive, puis affiche les commandes de ce lab adaptées à votre modèle : votre identifiant Drive à la tâche 2, votre nom de modèle à la tâche 3, votre prompt système à la tâche 4.

Mesures faites pendant la préparation, sur 58 questions jamais vues à l'entraînement :

| Modèle | Informations retrouvées | Réponses correctes à plus de 80 % |
| --- | --- | --- |
| `llama3.2:3b` (modèle actuel) | 20 % | 0 sur 58 |
| `eps-assistant` (modèle affiné) | 87 % | 49 sur 58 |

## Tâche 1 — Interroger le modèle actuel

1. Ouvrez votre interface web (adresse **Public IPv4 DNS** de l'instance `llm-lab`, en `http://`) et saisissez votre code d'accès.
2. Posez la question : « Quelle est l'adresse de l'École Polytechnique de Sousse ? » *Attendu : une adresse inventée. Pendant la préparation, le modèle a répondu « Rue de la République, 8018 Sousse », qui est fausse.*
3. Notez la réponse : vous la comparerez à la tâche 4.

## Tâche 2 — Télécharger le modèle affiné sur l'instance

1. Console EC2 > instance `llm-lab` > **Connect** > **Session Manager** > **Connect**, puis passez administrateur et placez-vous dans le dossier de l'application.

```bash
sudo -i
cd /opt/llm
ls finetune
```

*Attendu : `ls` liste notamment `creer_modele.sh`, `env-eps.exemple`, `evaluer.py` et `test.jsonl`. Si vous lisez `No such file or directory`, votre dépôt est antérieur à l'ajout du fine-tuning : voyez « Si ça bloque ».*

2. Téléchargez le fichier depuis Google Drive. La variable `ID` est l'identifiant du fichier : la partie du lien de partage située entre `/d/` et `/view`.

```bash
ID=1kQEEPJPb_2AB_degK7UmEkbb0wXiBhPh
curl -L -o /tmp/eps-assistant.gguf \
  "https://drive.usercontent.google.com/download?id=$ID&export=download&confirm=t"
```

*Attendu : une barre de progression, puis le retour à l'invite. Pendant le test, le téléchargement a pris 25 secondes.*

3. Vérifiez le fichier.

```bash
ls -lh /tmp/eps-assistant.gguf
head -c 4 /tmp/eps-assistant.gguf; echo
```

*Attendu : une taille de `1.9G`, puis le mot `GGUF`. Si vous lisez une petite taille et `<!do` ou `<htm`, vous avez reçu une page web au lieu du modèle : voyez « Si ça bloque ».*

## Tâche 3 — Créer le modèle dans Ollama

1. Copiez le fichier et le script de création dans le conteneur Ollama, puis lancez le script.

```bash
docker compose cp /tmp/eps-assistant.gguf ollama:/tmp/eps-assistant.gguf
docker compose cp finetune/creer_modele.sh ollama:/tmp/creer_modele.sh
docker compose exec ollama sh /tmp/creer_modele.sh
```

*Attendu, après 30 secondes environ : deux lignes `Copied ...`, puis `success` et la liste des modèles :*

```
NAME                    ID              SIZE      MODIFIED
eps-assistant:latest    450ac550a2b6    2.0 GB    Less than a second ago
llama3.2:3b             a80c4f17acd5    2.0 GB    ...
```

2. Supprimez la copie devenue inutile, puis vérifiez l'espace disque.

```bash
rm /tmp/eps-assistant.gguf
df -h /
```

*Attendu : une ligne `/dev/nvme0n1p1   30G   12G   19G  40% /` ou proche : il reste largement de la place.*

Le script `creer_modele.sh` reprend le gabarit de prompt de `llama3.2:3b`. C'est ce même gabarit qui a servi pendant l'entraînement : sans lui, le modèle affiné répondrait mal.

## Tâche 4 — Basculer l'application sur le modèle affiné

1. Changez le modèle dans le fichier de configuration et ajoutez le prompt système de l'assistant de l'école, sans toucher au code d'accès ni à l'image.

```bash
sed -i 's|^MODEL=.*|MODEL=eps-assistant|' .env
grep -q '^SYSTEM_PROMPT=' .env || grep '^SYSTEM_PROMPT=' finetune/env-eps.exemple >> .env
cat .env
```

*Attendu : quatre lignes : `MODEL=eps-assistant`, votre `ACCESS_CODE`, l'`APP_IMAGE` déployée par le pipeline, et `SYSTEM_PROMPT="Tu es l'assistant de Polytechnique Sousse ..."`.*

2. Redémarrez l'API avec cette configuration et vérifiez-la.

```bash
docker compose up -d --no-build
curl -s localhost/api/health
```

*Attendu : `Container llm-app-1 Started`, puis `{"ok":true,"version":"...","modele":"eps-assistant","modele_pret":true}`. La version n'a pas changé : l'image est la même, seule la configuration a changé.*

3. Rechargez l'interface web et posez ces questions. *Attendu : l'en-tête affiche « eps-assistant · modèle prêt », et les réponses ci-dessous. Comptez environ 25 secondes par réponse : c'est ce qui a été mesuré pendant le test.*

| Question | Réponse attendue |
| --- | --- |
| Quelle est l'adresse de l'École Polytechnique de Sousse ? | Route Ceinture Sahloul, Entrée Kalaa Sghira, 4021 Sousse, Tunisie |
| Combien coûte le cycle ingénieur pour un étudiant tunisien ? | 7 849 DT par an en 2026/2027, en trois tranches de 3 250, 2 700 et 1 899 DT |
| Quels sont les parcours en génie informatique ? | Génie Logiciel, Data Science & IA, Business Intelligence, Cybersécurité, Internet of Things |
| Explique le cloud en une phrase. | Une réponse générale correcte : le modèle n'a pas oublié le reste |

## Tâche 5 — Mesurer le gain

Le script `evaluer.py` pose les mêmes questions de test aux deux modèles et calcule le **rappel** : la part des mots importants de la réponse de référence retrouvés dans la réponse du modèle. On le lance dans le conteneur de l'API, qui contient déjà Python.

```bash
docker compose run --rm -v /opt/llm/finetune:/f -w /f app \
  python evaluer.py llama3.2:3b eps-assistant --url http://ollama:11434 --n 5
```

*Attendu, après 4 minutes environ : deux lignes de ce type. Le rappel du modèle de base varie selon les questions tirées ; le modèle affiné doit le dépasser nettement. Sortie obtenue pendant le test :*

```
llama3.2:3b                  rappel moyen  41.8 % · réponses à plus de 80 % : 0/5 · 2.6 tokens/s · 165 s
eps-assistant                rappel moyen 100.0 % · réponses à plus de 80 % : 5/5 · 2.8 tokens/s · 71 s
Détail des réponses dans evaluation.json
```

Notez les deux rappels. Le détail des réponses est dans `/opt/llm/finetune/evaluation.json` : lisez-le avec `cat finetune/evaluation.json`.

Pendant l'évaluation, les deux modèles sont chargés en même temps : la mémoire utilisée a culminé à 5,6 Go sur 7,8 pendant le test. Vous pouvez le vérifier pendant que le script tourne, dans un second onglet Session Manager, avec `free -h`.

## Tâche 6 — Chercher les limites

Le modèle affiné n'est pas fiable à 100 %. Posez-lui ces questions dans l'interface : elles l'ont mis en défaut pendant la préparation.

| Question | Ce qui s'est passé pendant la préparation |
| --- | --- |
| Est-ce qu'il y a un internat à l'EPS ? | Il a affirmé qu'un foyer existe, alors qu'il devait dire qu'il ne sait pas |
| Quelles sont les dates limites des tranches ? | Il a inventé des dates, sept lors d'un essai et quatre lors d'un autre, au lieu des deux vraies (31 décembre et 31 mars) |
| J'ai une licence, puis-je intégrer le cycle ingénieur ? | Il a répondu sur le Master 1, une question voisine |

## Tâche 7 — Vérifier que le pipeline garde le modèle

1. Sur GitHub, modifiez `app/static/index.html` : remplacez votre titre par `<h1>Assistant Polytechnique Sousse</h1>`, puis **Commit changes**.
2. Suivez l'onglet **Actions** jusqu'au vert, puis rechargez l'interface. *Attendu : le nouveau titre, un nouveau numéro de version, et toujours « eps-assistant » dans l'en-tête.*

Le pipeline ne remplace que l'image (`APP_IMAGE`) dans `.env` : le choix du modèle et le prompt système restent ceux de l'instance.

## Point de contrôle

- [ ] L'en-tête de l'interface affiche « eps-assistant · modèle prêt ».
- [ ] L'assistant donne la bonne adresse de l'école.
- [ ] Vous donnez deux chiffres : le rappel du modèle de base et celui du modèle affiné.
- [ ] Vous avez trouvé au moins une question où le modèle affiné invente.

## Questions de synthèse

1. Pourquoi évaluer sur des formulations différentes de celles de l'entraînement ?
2. Le modèle affiné pèse 2 Go, comme le modèle de base, et répond à la même vitesse. Pourquoi ?
3. Où sont rangés le modèle et le choix du modèle : dans l'image ECR, sur le disque de l'instance, ou dans le dépôt GitHub ? Que se passe-t-il si la pile CloudFormation est recréée ?
4. Les frais changeront l'an prochain. Que faudra-t-il refaire ? Citez une approche qui éviterait de réentraîner le modèle. Attendu : une recherche documentaire (RAG), qui fournit au modèle le texte à jour au moment de la question.

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| Le fichier téléchargé fait quelques Ko et commence par `<!do` ou `<htm` | Le fichier Drive n'est pas partagé publiquement, ou Google refuse le téléchargement (« Trop d'utilisateurs ont téléchargé ce fichier ») : prévenez l'enseignant, ou réessayez plus tard |
| `curl: (23) Failure writing output` ou `No space left on device` | Disque plein : `df -h /`, puis `docker image prune -f` pour retirer les anciennes images du pipeline |
| `docker compose` : `no configuration file provided` | Vous n'êtes pas dans `/opt/llm` : `cd /opt/llm` |
| `ls finetune` : `No such file or directory` | Votre dépôt a été créé avant l'ajout du fine-tuning. Récupérez les quatre fichiers utiles depuis le dépôt modèle : `mkdir -p finetune && cd finetune && for f in creer_modele.sh env-eps.exemple evaluer.py test.jsonl; do curl -fsSLO https://raw.githubusercontent.com/nevermind78/llm-lab/main/finetune/$f; done && cd ..` |
| `creer_modele.sh` : « Fichier ... introuvable dans le conteneur » | Refaites la première copie de la tâche 3 |
| En-tête : « eps-assistant · modèle absent » | Le modèle n'a pas été créé : `docker compose exec ollama ollama list`, puis refaites la tâche 3. Si `ollama list` montre bien `eps-assistant:latest` et que l'assistant répond, c'est votre `app/main.py` qui date d'avant le correctif : sur GitHub, dans `app/main.py`, remplacez `return any(m["name"] == MODEL for m in r.json().get("models", []))` par `return any(MODEL in (m["name"], m["name"].removesuffix(":latest")) for m in r.json().get("models", []))`, puis **Commit changes** : le pipeline déploie la correction |
| Réponses incohérentes ou qui ne s'arrêtent pas | Le modèle a été créé sans gabarit de prompt : refaites la tâche 3 avec `creer_modele.sh`, pas avec un `Modelfile` écrit à la main |
| `evaluer.py` : `Connection refused` | Gardez `--url http://ollama:11434` : dans le conteneur, Ollama ne s'appelle pas `localhost` |

---

[Sommaire](README.md) · [← Lab 5](lab-5.md) · [Lab 7 →](lab-7.md)
