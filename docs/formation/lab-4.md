# Lab 4 — Tout recréer avec CloudFormation

[Sommaire](README.md) · [← Lab 3](lab-3.md) · [Lab 5 →](lab-5.md)


**Durée** : 60 min · **Prérequis** : Lab 3 · **Objectif** : remplacer les manipulations des labs 1 et 2 par un fichier, `infra/stack.yaml`, qui reconstruit le service sans intervention.

## Tâche 1 — Détruire ce qui a été fait à la main

1. Console EC2 > cochez `llm-manuel` > **Instance state** > **Terminate (delete) instance** > confirmez. *Attendu : état **Terminated** en moins d'une minute. Le dépôt ECR n'est pas touché.*

## Tâche 2 — Déployer la pile

1. Ouvrez **CloudShell** et clonez votre dépôt. Remplacez `COMPTE`.

```bash
git clone https://github.com/COMPTE/llm-lab.git && cd llm-lab
```

2. Déployez la pile. Remplacez `COMPTE` et `MON-CODE`.

```bash
aws cloudformation deploy --stack-name llm-lab \
  --template-file infra/stack.yaml \
  --parameter-overrides AccessCode=MON-CODE \
      RepoUrl=https://github.com/COMPTE/llm-lab.git
```

*Attendu après 40 secondes environ : `Successfully created/updated stack - llm-lab`.*

3. Affichez l'adresse du service.

```bash
aws cloudformation describe-stacks --stack-name llm-lab \
  --query "Stacks[0].Outputs" --output table
```

*Attendu : deux lignes, `InstanceId` et `Url`.*

## Tâche 3 — Suivre l'installation automatique

La pile est « créée » dès que l'instance démarre, mais le script de démarrage travaille encore : Docker, clonage du dépôt, construction de l'image, téléchargement d'Ollama et du modèle. Pendant le test, le service était prêt **4 minutes 30** après la création de la pile.

1. Console EC2 > instance `llm-lab` > **Connect** > **Session Manager** > **Connect**.
2. Suivez le journal.

```bash
sudo tail -f /var/log/llm-lab-setup.log
```

*Attendu : le journal défile, puis se termine par les lignes `verifying sha256 digest`, `writing manifest` et `success`. Quittez avec Ctrl+C.*

3. Ouvrez l'`Url` de la tâche 2 dans le navigateur et posez une question. *Attendu : même comportement qu'au Lab 2, sans avoir tapé une seule commande d'installation.*

## Tâche 4 — Lire le modèle et la console

1. Console **CloudFormation** > pile `llm-lab` > onglets **Events**, **Resources**, **Parameters**, **Outputs**.
2. Ouvrez `infra/stack.yaml` sur GitHub et retrouvez, pour chaque geste du Lab 1, la ligne qui le remplace.

| Geste du Lab 1 | Ligne du modèle |
| --- | --- |
| Instance type `t3.large` | `InstanceType: !Ref InstanceType` |
| Allow HTTP traffic | `WebSecurityGroup`, port 80 |
| 30 GiB gp3 | `BlockDeviceMappings` |
| IAM instance profile | `IamInstanceProfile: LabInstanceProfile` |
| Commandes tapées en `root` | `UserData` |

3. Dans `UserData`, repérez la ligne `until docker compose exec -T ollama ollama list; do sleep 2; done`. À quoi sert-elle ? Indice : relisez la remarque de l'étape 5, tâche 2 du Lab 2.

## Tâche 5 — Changer un paramètre (optionnel)

On passe l'instance sur une `m7i.large`, environ 1,5 fois plus rapide, en modifiant un seul paramètre de la pile.

1. Dans CloudShell, depuis le dossier `llm-lab` de la tâche 2 :

```bash
aws cloudformation deploy --stack-name llm-lab --template-file infra/stack.yaml \
  --parameter-overrides InstanceType=m7i.large
```

*Attendu, après 1 à 2 minutes : `Successfully created/updated stack - llm-lab`. Les paramètres que vous ne citez pas, comme le code d'accès et l'adresse du dépôt, gardent leur valeur.*

2. Console **CloudFormation** > pile `llm-lab` > onglet **Events**. *Attendu : `LlmInstance` passe à `UPDATE_IN_PROGRESS`, puis `UPDATE_COMPLETE`. Pour changer le type, CloudFormation arrête l'instance, la modifie et la redémarre ; le détail n'apparaît pas dans les événements.*
3. Relisez la sortie de la pile.

```bash
aws cloudformation describe-stacks --stack-name llm-lab \
  --query "Stacks[0].Outputs" --output table
```

*Attendu : une nouvelle `Url`. L'adresse publique change à chaque redémarrage ; ici, la sortie est à jour, parce que c'est CloudFormation qui a redémarré l'instance.*

4. Ouvrez la nouvelle adresse. *Attendu : l'interface répond environ 2 minutes après le lancement de la commande, sans aucune intervention sur l'instance : les conteneurs redémarrent seuls.*
5. Revenez à une `t3.large` avec la même commande et `InstanceType=t3.large` : les durées des fiches suivantes sont données pour ce type, et une `m7i.large` coûte environ 20 % de plus par heure.

## Point de contrôle

- [ ] La pile `llm-lab` est à l'état `CREATE_COMPLETE` ou `UPDATE_COMPLETE`.
- [ ] L'interface répond à l'adresse donnée par la sortie `Url`.
- [ ] L'instance `llm-manuel` est supprimée.

## Questions de synthèse

1. Le modèle ne crée aucun rôle IAM. Pourquoi, dans le Learner Lab ?
2. Le code d'accès est déclaré `NoEcho`. Que cache cette option, et que ne cache-t-elle pas ? Indice : `sudo cat /opt/llm/.env` sur l'instance.
3. Citez deux avantages d'une pile par rapport aux gestes du Lab 1.

## Si ça bloque

| Symptôme | Remède |
| --- | --- |
| Pile en `ROLLBACK_COMPLETE` | Lire la première ligne rouge de l'onglet **Events** ; supprimer la pile avant de relancer |
| La page répond mais l'en-tête dit « modèle absent » après 10 minutes | Lire la fin de `/var/log/llm-lab-setup.log` ; relancer à la main `cd /opt/llm && sudo docker compose exec ollama ollama pull llama3.2:3b` |
| La page ne répond pas après 10 minutes | Lire `/var/log/llm-lab-setup.log` : une erreur de clonage signale un dépôt privé ou une URL fausse |
| `Parameter validation failed` sur `AccessCode` | Le code doit compter au moins 6 caractères |

---

[Sommaire](README.md) · [← Lab 3](lab-3.md) · [Lab 5 →](lab-5.md)
