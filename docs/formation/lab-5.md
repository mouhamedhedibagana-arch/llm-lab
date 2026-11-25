# Lab 5 — Pipeline CI/CD

[Sommaire](README.md) · [← Lab 4](lab-4.md) · [Lab 6 →](lab-6.md)


**Durée** : 75 min · **Prérequis** : Lab 4, pile `llm-lab` en service · **Objectif** : chaque `git push` sur `main` lance les tests, construit une image dans ECR, la déploie et vérifie la version en service.

Le pipeline a deux étages. Les tests tournent sur une machine de GitHub, sans aucun accès à AWS. Le déploiement tourne sur un exécuteur (« runner ») installé sur votre instance : il hérite des droits du rôle de l'instance, donc aucune clé AWS n'est stockée dans GitHub.

## Tâche 1 — Installer l'exécuteur GitHub sur l'instance

1. GitHub > votre dépôt `llm-lab` > **Settings** > **Actions** > **Runners** > **New self-hosted runner**. Choisissez **Linux** et **x64**. Gardez la page ouverte.
2. Connectez-vous à l'instance `llm-lab` par Session Manager, puis prenez l'identité `ec2-user`.

```bash
sudo -iu ec2-user
```

*Attendu : l'invite devient `[ec2-user@ip-... ~]$`.*

3. Copiez-collez, une par une, les commandes du bloc **Download** de la page GitHub. La commande de vérification qui contient `shasum -a 256 -c` répond `shasum: command not found` : ce programme n'existe pas sur Amazon Linux 2023. Ignorez cette erreur, ou remplacez `shasum -a 256 -c` par `sha256sum -c` pour obtenir `OK`.
4. Copiez-collez la commande `./config.sh --url ... --token ...` du bloc **Configure**. Validez chaque question par Entrée pour garder les valeurs par défaut. *Attendu : `Connected to GitHub`, `Runner successfully added` et `Settings Saved`.*
5. Installez l'exécuteur comme service, pour qu'il redémarre avec l'instance.

```bash
sudo ./svc.sh install ec2-user
sudo ./svc.sh start
```

*Attendu : une ligne `Active: active (running)`. Sur la page **Runners** de GitHub, l'exécuteur apparaît avec l'état **Idle**.*

N'exécutez pas la commande `./run.sh` proposée par GitHub : le service la remplace.

## Tâche 2 — Activer le pipeline

1. GitHub > ouvrez `pipeline/ci-cd.yml` > bouton **Copy raw file**.
2. Revenez à la racine du dépôt > **Add file** > **Create new file**. Dans le nom, tapez `.github/workflows/ci-cd.yml` : chaque `/` crée un dossier. Collez le contenu.
3. Cliquez **Commit changes...**, puis **Commit changes**, directement sur `main`.
4. Onglet **Actions** : ouvrez l'exécution en cours. *Attendu : la tâche `test` passe au vert en 25 à 35 secondes, puis `deploy` en 15 secondes environ. Dépliez sa dernière étape : elle affiche « Version abc1234 en service », où `abc1234` est l'identifiant de votre commit.*
5. Rechargez l'interface web. *Attendu : l'en-tête affiche la même version à 7 caractères que le pipeline.*

## Tâche 3 — Livrer une modification

1. GitHub > `app/static/index.html` > crayon **Edit this file**.
2. Remplacez `<h1>LLM Lab</h1>` par `<h1>LLM Lab de PRÉNOM</h1>`, puis **Commit changes**.
3. Suivez l'onglet **Actions**, puis rechargez la page web. *Attendu, environ une minute après le commit : le nouveau titre et un nouveau numéro de version, sans aucune commande sur l'instance.*
4. Console ECR > `llm-app`. *Attendu : une image par commit déployé, étiquetée par son identifiant, en plus de `v1`.*

## Tâche 4 — Voir le pipeline bloquer une erreur

1. Notez la version affichée par l'interface web.
2. Dans `app/main.py`, remplacez `MAX_MESSAGES, MAX_CARACTERES = 20, 4000` par `MAX_MESSAGES, MAX_CARACTERES = 20, 400000`, puis **Commit changes**.
3. Onglet **Actions**. *Attendu : `test` échoue (croix rouge) et `deploy` est ignoré (icône grise). Dans le journal de `test` :*

```
FAILED tests/test_api.py::test_message_trop_long - AssertionError: assert 200 == 422
1 failed, 11 passed
```

4. Rechargez la page web. *Attendu : la version en service n'a pas changé.*
5. Remettez `4000`, validez, et vérifiez que le pipeline repasse au vert et déploie une nouvelle version.

## Tâche 5 — Revenir à une version précédente

1. Onglet **Actions** > ouvrez l'exécution verte de la tâche 2 > **Re-run all jobs** > **Re-run jobs**.
2. Rechargez la page web. *Attendu : l'ancien titre « LLM Lab » et l'ancien numéro de version sont de retour.*
3. Relancez de la même façon l'exécution la plus récente pour revenir à la dernière version. *Attendu : le titre « LLM Lab de PRÉNOM » revient.*

## Point de contrôle

- [ ] L'exécuteur est **Idle** dans GitHub.
- [ ] Un commit sur `main` a changé la version affichée par l'interface.
- [ ] Un commit qui casse un test n'a pas été déployé.

## Questions de synthèse

1. Quelle étape du pipeline est de l'intégration continue, laquelle du déploiement continu ?
2. Pourquoi ne pas avoir collé les identifiants AWS du Learner Lab dans les secrets GitHub ?
3. La dernière étape interroge `/api/health`. Que se passerait-il sans elle si le conteneur ne démarrait pas ?

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| `deploy` reste en attente (« Waiting for a runner ») | Instance arrêtée, ou service absent : `sudo ./svc.sh status` dans le dossier `actions-runner` |
| `config.sh` : jeton expiré | Le jeton dure 1 heure : recharger la page **New self-hosted runner** |
| `Must not run with sudo` | Vous êtes `root` : tapez `exit`, puis `sudo -iu ec2-user` |
| `permission denied` sur le socket Docker | L'exécuteur doit être installé pour `ec2-user` : `sudo ./svc.sh uninstall`, puis reprendre l'étape 5 |
| `RepositoryNotFoundException` | Le dépôt ECR `llm-app` du Lab 3 a été supprimé : le recréer |

---

[Sommaire](README.md) · [← Lab 4](lab-4.md) · [Lab 6 →](lab-6.md)
