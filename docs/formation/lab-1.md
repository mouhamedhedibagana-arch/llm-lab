# Lab 1 — Servir un LLM à la main sur EC2

[Sommaire](README.md) · [← Lab 0](lab-0.md) · [Lab 2 →](lab-2.md)


**Durée** : 60 min · **Prérequis** : Lab 0 · **Objectif** : lancer une instance, y installer un serveur de modèle et obtenir une première réponse. Tout est fait à la main, pour comprendre ce que les labs suivants automatiseront.

## Tâche 1 — Lancer l'instance

1. Dans la console AWS, tapez `EC2` dans la barre de recherche et ouvrez le service **EC2**.
2. Cliquez **Launch instance**.
3. **Name** : `llm-manuel`.
4. **Application and OS Images** : laissez **Amazon Linux 2023 AMI** et l'architecture **64-bit (x86)**.
5. **Instance type** : choisissez `t3.large` (2 vCPU, 8 Gio de mémoire).
6. **Key pair (login)** : choisissez **Proceed without a key pair**.
7. **Network settings** : cochez **Allow HTTP traffic from the internet** et décochez **Allow SSH traffic from**.
8. **Configure storage** : remplacez 8 par `30` GiB et gardez **gp3**.
9. Dépliez **Advanced details**. Dans **IAM instance profile**, choisissez `LabInstanceProfile`.
10. Cliquez **Launch instance**, puis **View all instances**. *Attendu : `llm-manuel` passe à l'état **Running** en 20 à 60 secondes.*

## Tâche 2 — Se connecter sans clé SSH

1. Cochez l'instance `llm-manuel`, cliquez **Connect**, ouvrez l'onglet **Session Manager**, puis cliquez **Connect**. Si le bouton est grisé, patientez 2 minutes et rechargez la page : l'agent de l'instance n'a pas encore démarré.
2. Dans le terminal qui s'ouvre, passez administrateur.

```bash
sudo -i
```

*Attendu : l'invite devient `[root@ip-... ~]#`.*

## Tâche 3 — Installer Docker et le serveur de modèle

1. Installez Docker et Git, puis démarrez Docker.

```bash
dnf install -y docker git
systemctl enable --now docker
```

*Attendu : la première commande se termine par `Complete!`.*

2. Lancez Ollama, le logiciel qui fait tourner le modèle.

```bash
docker run -d --name ollama -p 127.0.0.1:11434:11434 -v ollama:/root/.ollama ollama/ollama
```

*Attendu : Docker télécharge une image d'environ 5 Go, puis affiche un long identifiant. Comptez 2 à 3 minutes.*

3. Vérifiez que le conteneur tourne.

```bash
docker ps
```

*Attendu : une ligne `ollama` avec l'état `Up`.*

## Tâche 4 — Télécharger le modèle et l'interroger

1. Téléchargez le modèle.

```bash
docker exec ollama ollama pull llama3.2:3b
```

*Attendu : une barre de progression pour environ 2 Go, puis `success`. Le téléchargement a pris 20 secondes pendant le test.*

2. Posez une première question.

```bash
time curl -s localhost:11434/api/chat -d '{
  "model": "llama3.2:3b", "stream": false,
  "messages": [{"role": "user", "content": "Explique le cloud en une phrase."}]
}'
```

*Attendu : après 20 à 30 secondes sans rien à l'écran, un bloc JSON dont le champ `message.content` contient une phrase en français. Notez la durée `real`.*

3. Dans ce même JSON, relevez deux nombres : `eval_count` (le nombre de tokens générés) et `eval_duration` (la durée en nanosecondes). Calculez le débit : `eval_count / (eval_duration / 1 000 000 000)`. *Attendu : environ 3 tokens par seconde.*

## Tâche 5 — Observer la machine

1. Lancez les trois commandes suivantes.

```bash
docker exec ollama ollama ps
free -h
docker stats --no-stream
```

*Attendu : `ollama ps` indique le modèle `llama3.2:3b`, une taille de 2,6 Go et `100% CPU`. `free -h` montre environ 4,5 Gio dans la colonne `available`.*

2. Relancez la requête de la tâche 4 et comparez la durée. Le premier appel charge le modèle en mémoire (6,5 secondes pendant le test), les suivants non. Après 5 minutes sans requête, Ollama décharge le modèle.

## Point de contrôle

- [ ] L'instance a le profil `LabInstanceProfile` et aucun port 22 ouvert.
- [ ] `curl` renvoie une réponse du modèle.
- [ ] Vous savez dire combien de mémoire le modèle occupe et quel est son débit en tokens par seconde.

## Questions de synthèse

1. Pourquoi le port 11434 est-il lié à `127.0.0.1` et non ouvert sur Internet ?
2. Qu'est-ce qui a permis la connexion sans mot de passe ni clé ?
3. Que se passerait-il avec une instance `t3.medium` (4 Gio de mémoire) ?

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| Onglet Session Manager : « not connected » | Vérifier le profil IAM dans **Actions** > **Security** > **Modify IAM role**, puis redémarrer l'instance |
| Lancement refusé pour le type d'instance | Choisir une taille « large » au plus |
| `pull` très lent ou interrompu | Relancer la même commande : le téléchargement reprend |
| `curl` ne rend rien pendant 30 secondes | C'est normal : avec `"stream": false`, la réponse arrive d'un bloc à la fin |

Laissez l'instance allumée pour le Lab 2.

---

[Sommaire](README.md) · [← Lab 0](lab-0.md) · [Lab 2 →](lab-2.md)
