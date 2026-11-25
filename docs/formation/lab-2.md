# Lab 2 — API et interface web

[Sommaire](README.md) · [← Lab 1](lab-1.md) · [Lab 3 →](lab-3.md)


**Durée** : 60 min · **Prérequis** : Lab 1, instance `llm-manuel` allumée · **Objectif** : placer une API devant le modèle et discuter avec lui depuis un navigateur.

## Tâche 1 — Installer Docker Compose et récupérer le code

Dans le terminal Session Manager, en `root` (retapez `sudo -i` si vous venez de vous reconnecter) :

1. Installez Docker Compose.

```bash
mkdir -p /usr/libexec/docker/cli-plugins
curl -fsSL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 \
  -o /usr/libexec/docker/cli-plugins/docker-compose
chmod +x /usr/libexec/docker/cli-plugins/docker-compose
docker compose version
```

*Attendu : `Docker Compose version v5.x.x` (v5.7.1 pendant le test).*

2. Supprimez le conteneur du Lab 1 et récupérez votre code. Remplacez `COMPTE`.

```bash
docker rm -f ollama
git clone https://github.com/COMPTE/llm-lab.git /opt/llm
cd /opt/llm && ls
```

*Attendu : `ls` montre `README.md`, `app`, `docker-compose.yml`, `infra`, `pipeline`, `tests`.*

## Tâche 2 — Configurer et démarrer la pile

1. Écrivez le fichier de configuration. Remplacez `MON-CODE` par votre code d'accès.

```bash
cat > /opt/llm/.env <<EOF
MODEL=llama3.2:3b
ACCESS_CODE=MON-CODE
APP_IMAGE=llm-app:local
EOF
```

2. Construisez l'image de l'API. *Attendu : la dernière ligne contient `naming to docker.io/library/llm-app:local done` ; comptez 15 secondes.*

```bash
cd /opt/llm
docker build -t llm-app:local /opt/llm/app
```

3. Vérifiez que l'image existe avant d'aller plus loin. *Attendu : une ligne `llm-app   local`, d'environ 170 Mo. Si la liste est vide, la construction a échoué : relisez le message d'erreur de l'étape 2 et recommencez-la.*

```bash
docker images llm-app
```

4. Démarrez les deux conteneurs. *Attendu : `Container llm-ollama-1 Started` et `Container llm-app-1 Started`.*

```bash
cd /opt/llm
docker compose up -d
```

5. Téléchargez le modèle dans le volume de la pile. Il est téléchargé une seconde fois, parce que ce volume n'est pas celui du Lab 1. *Attendu : `success`.*

```bash
docker compose exec ollama ollama pull llama3.2:3b
```

Si la commande répond `could not connect to ollama server`, Ollama n'a pas fini de démarrer : attendez 5 secondes et relancez-la.

6. Vérifiez l'état des services et de l'API.

```bash
docker compose ps
curl -s localhost/api/health
```

*Attendu : deux services `ollama` et `app` à l'état `running`, puis :*

```json
{"ok":true,"version":"dev","modele":"llama3.2:3b","modele_pret":true}
```

**Pourquoi `docker build` puis `docker compose up` ?** La commande habituelle `docker compose up -d --build` échoue sur Amazon Linux 2023 avec le message `compose build requires buildx 0.17.0 or later` : le Docker fourni par Amazon est trop ancien pour la construction intégrée à Compose. On construit donc l'image séparément. Le même message apparaît si vous lancez `docker compose up -d` alors que l'image `llm-app:local` n'existe pas : Compose tente alors de la construire lui-même.

## Tâche 3 — Tester depuis le navigateur

1. Dans la console EC2, cochez l'instance `llm-manuel` et copiez la valeur **Public IPv4 DNS**, de la forme `ec2-54-237-228-253.compute-1.amazonaws.com`.
2. Dans un nouvel onglet, ouvrez `http://ADRESSE-COPIÉE`. Tapez bien `http://` : le site n'a pas de certificat, et `https://` ne répondra pas.
3. *Attendu : une page « LLM Lab » dont l'en-tête affiche « version dev · llama3.2:3b · modèle prêt ».*
4. Saisissez votre code d'accès en haut à droite, posez une question courte, envoyez. *Attendu : après quelques secondes, la réponse s'écrit progressivement ; à la fin, la durée et le débit en caractères par seconde s'affichent dessous.*
5. Videz le champ du code et renvoyez une question. *Attendu : « Échec : code d'accès invalide ».*

Pour convertir le débit affiché en tokens par seconde, divisez-le par 4,4 : en français, un token de ce modèle vaut environ 4,4 caractères.

## Tâche 4 — Lire le code

Ouvrez `app/main.py` sur GitHub et répondez :

1. Quelles sont les trois routes de l'API ?
2. À quelle ligne le prompt système est-il ajouté ? Pourquoi le navigateur n'a-t-il pas le droit d'envoyer un message de rôle `system` ?
3. Quelles limites protègent le service contre une requête abusive ?

## Tâche 5 — Essayer un autre modèle (optionnel)

| Étiquette Ollama | Taille | Remarque |
| --- | --- | --- |
| `llama3.2:1b` | environ 1,3 Go | Presque deux fois plus rapide (4,4 tokens/s mesurés), qualité inférieure |
| `llama3.2:3b` | environ 2 Go | Valeur par défaut, environ 3 tokens/s |
| `gemma3:4b` | environ 3,3 Go | 2,2 tokens/s, un peu plus lent ; 2,9 Go en mémoire |
| `qwen2.5:7b` | environ 4,7 Go | 1,3 tokens/s, deux fois plus lent ; 5,1 Go en mémoire, cela tient sur une `t3.large` |

```bash
cd /opt/llm
docker compose exec ollama ollama pull llama3.2:1b
sed -i 's|^MODEL=.*|MODEL=llama3.2:1b|' .env && docker compose up -d
```

Posez la même question aux deux modèles et comparez la qualité et le débit. Les débits du tableau sont ceux d'une `t3.large` ; chaque téléchargement prend moins d'une minute. Remettez ensuite `MODEL=llama3.2:3b` de la même façon.

## Point de contrôle

- [ ] L'interface répond à une question depuis votre navigateur.
- [ ] Une requête sans code est refusée.
- [ ] Vous avez noté un débit en caractères par seconde.

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| `compose build requires buildx 0.17.0 or later` | L'image `llm-app:local` n'existe pas (construction sautée ou échouée), ou vous avez tapé `--build`. Lancez `docker build -t llm-app:local /opt/llm/app`, vérifiez avec `docker images llm-app`, puis `docker compose up -d` |
| `unable to prepare context: path "app" not found` | Vous n'êtes pas dans `/opt/llm` : utilisez le chemin complet `/opt/llm/app` |
| `no configuration file provided: not found` | Vous n'êtes pas dans `/opt/llm` : tapez `cd /opt/llm` et relancez la commande |
| La page ne charge pas | Vérifier `http://` et la règle du groupe de sécurité (port 80, source `0.0.0.0/0`) |
| En-tête : « modèle absent » | Relancer `docker compose exec ollama ollama pull llama3.2:3b` |
| Réponse « erreur du serveur de modèle » | `docker compose logs ollama --tail 30` ; modèle absent, ou mémoire insuffisante si le modèle est trop gros |

---

[Sommaire](README.md) · [← Lab 1](lab-1.md) · [Lab 3 →](lab-3.md)
