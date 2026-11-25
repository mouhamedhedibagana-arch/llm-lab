# Lab 3 — Image conteneur dans Amazon ECR

[Sommaire](README.md) · [← Lab 2](lab-2.md) · [Lab 4 →](lab-4.md)


**Durée** : 45 min · **Prérequis** : Lab 2 · **Objectif** : publier l'image de l'API dans un registre privé, avec une étiquette de version, et faire tourner le service depuis cette image.

## Tâche 1 — Créer le dépôt d'images

Dans le terminal de l'instance, en `root` :

```bash
export AWS_DEFAULT_REGION=us-east-1
aws ecr create-repository --repository-name llm-app
```

*Attendu : un JSON contenant `repositoryUri`, de la forme `123456789012.dkr.ecr.us-east-1.amazonaws.com/llm-app`.*

## Tâche 2 — S'authentifier, construire, pousser

1. Connectez Docker au registre.

```bash
COMPTE=$(aws sts get-caller-identity --query Account --output text)
REGISTRE=$COMPTE.dkr.ecr.us-east-1.amazonaws.com
aws ecr get-login-password | docker login --username AWS --password-stdin $REGISTRE
```

*Attendu : `Login Succeeded`.*

2. Construisez l'image avec l'étiquette `v1` et poussez-la.

```bash
docker build -t $REGISTRE/llm-app:v1 --build-arg APP_VERSION=v1 /opt/llm/app
docker push $REGISTRE/llm-app:v1
```

*Attendu : chaque couche affiche `Pushed`, puis une ligne `v1: digest: sha256:... size: ...`.*

Les variables `COMPTE` et `REGISTRE` disparaissent si vous fermez le terminal : en cas de reconnexion, retapez les deux premières lignes de l'étape 1.

## Tâche 3 — Servir depuis l'image du registre

```bash
cd /opt/llm
sed -i "s|^APP_IMAGE=.*|APP_IMAGE=$REGISTRE/llm-app:v1|" .env
docker compose up -d --no-build
curl -s localhost/api/health
```

*Attendu : `{"ok":true,"version":"v1","modele":"llama3.2:3b","modele_pret":true}`. Rechargez la page web : l'en-tête affiche « version v1 ».*

## Tâche 4 — Inspecter dans la console

1. Console AWS > **Elastic Container Registry** > **Repositories** > `llm-app`.
2. Relevez l'étiquette, la taille de l'image et sa date. *Attendu : une image `v1` d'environ 60 Mo.*

## Point de contrôle

- [ ] Le dépôt ECR `llm-app` contient l'image `v1`.
- [ ] `/api/health` renvoie la version `v1`.

## Questions de synthèse

1. Aucune clé AWS n'a été saisie : d'où viennent les droits de pousser dans ECR ? Indice : `aws sts get-caller-identity` sur l'instance.
2. Pourquoi une étiquette `v1` plutôt que `latest` ?
3. Le modèle de 2 Go n'est pas dans l'image. Où est-il, et quel est l'avantage ?

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| `AccessDenied` sur `ecr:CreateRepository` | Prévenir l'enseignant |
| `no basic auth credentials` au `push` | Relancer la commande `docker login` : le jeton dure 12 heures |
| `sed` ne change rien, la version reste `dev` | La variable `REGISTRE` est vide : retapez l'étape 1 de la tâche 2 |

---

[Sommaire](README.md) · [← Lab 2](lab-2.md) · [Lab 4 →](lab-4.md)
