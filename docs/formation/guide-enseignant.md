# Guide de l'enseignant

[Sommaire](README.md)


## Préparation

- [ ] Dans le portail AWS Academy, créer une classe du cours **AWS Academy Learner Lab**. Elle apparaît dans **My Active Classes** après un délai (le lendemain pendant la préparation).
- [ ] Pour utiliser vous-même le lab : ouvrir la classe, puis **Student View** dans l'écran Vocareum. Ne pas cliquer **Unpublish Assignment**.
- [ ] Créer un dépôt GitHub public avec le contenu du kit, **sans** le dossier `.github` : les étudiants créent le fichier du pipeline au Lab 5. Cocher **Settings** > **Template repository**.
- [ ] Partager le fichier `eps-assistant-q4_k_m.gguf` sur Google Drive avec l'accès **Tous les utilisateurs disposant du lien**, rôle **Lecteur**. Vérifier dans CloudShell que la commande de la tâche 2 du Lab 6 télécharge bien 1,9 Go commençant par `GGUF`. Si le lien de partage change, remplacer l'identifiant `ID` dans le Lab 6.
- [ ] Dérouler une fois le [notebook Colab](https://colab.research.google.com/github/nevermind78/llm-lab/blob/main/finetune/fine_tuning_colab.ipynb) avec `SOURCE = "eps"`, pour connaître ses durées et ses éventuels messages avant de le proposer aux étudiants.
- [ ] Demander aux étudiants de créer leur compte GitHub avant la première séance.
- [ ] Prévenir les étudiants : à la connexion à AWS Academy, copier-coller le code de vérification reçu par e-mail. Plusieurs saisies fausses bloquent le compte, et le support met du temps à le débloquer.

## Découpage conseillé

| Séance | Fiches | Durée |
| --- | --- | --- |
| 1 | Lab 0, Lab 1, Lab 2 | 2 h 30 |
| 2 | Lab 3, Lab 4 | 1 h 45 |
| 3 | Lab 5, Lab 6 | 2 h 15 |
| 4 | Lab 7, Lab 8 | 1 h 45 |

Une session Learner Lab dure 4 heures. Entre deux séances, les étudiants font **Start Lab**, redémarrent leur instance et relèvent sa nouvelle adresse dans la console EC2. Si la séance 2 s'arrête après le Lab 3, l'instance `llm-manuel` peut rester arrêtée jusqu'à la suivante. Chaque séance tient dans une session Learner Lab de 4 heures.

## Pièges connus

| Piège | Parade |
| --- | --- |
| L'étudiant croit le service en panne parce que la réponse tarde | Annoncer le débit dès le début : 3 tokens par seconde, 30 secondes pour une phrase |
| L'étudiant ouvre `https://` au lieu de `http://` | Le dire à voix haute au Lab 2 ; le service n'a pas de certificat |
| L'adresse publique change à chaque démarrage | Toujours la relire dans la console EC2, pas dans la sortie de la pile |
| Dépôt GitHub créé en privé | Le `git clone` du Lab 4 échoue : repasser le dépôt en public |
| Modèle trop gros pour 8 Gio | Rester sur un modèle de 4 Go au plus en `t3.large` |
| Exécuteur auto-hébergé sur un dépôt public | Le pipeline ne se déclenche que sur `main` : ne pas y ajouter de déclencheur `pull_request`, qui laisserait un inconnu exécuter du code sur l'instance |
| Google Drive bloque le téléchargement quand trop de personnes récupèrent le même fichier en peu de temps | Faire télécharger le modèle par groupes, ou prévoir une seconde copie du fichier sous un autre lien |
| Dépôt d'étudiant créé à partir du modèle avant le 24 novembre 2026 | Il n'a pas le code du RAG : la fiche du Lab 7 donne la procédure de récupération, dans « Si ça bloque » |
| Surcoût des instances T3 | Les `t3` sont en mode « unlimited » dans le Learner Lab : un usage intensif du processeur est facturé en supplément. Une `m7i.large` n'a pas ce mécanisme |

## Aller plus vite

- **Bedrock est refusé** dans ce Learner Lab, pour le rôle étudiant comme pour `LabRole` : ce n'est pas une option.
- **`m7i.large`** est autorisée et génère environ 1,5 fois plus vite que `t3.large`, pour un tarif horaire supérieur d'environ 20 %. C'est un simple paramètre de la pile.
- **`llama3.2:1b`** double à peu près le débit, au prix de la qualité.
- Forcer deux fils d'exécution (`num_thread: 2`) n'apporte que 15 % : les 2 vCPU sont un seul cœur physique.

## Évaluation suggérée

| Preuve | Points |
| --- | --- |
| Capture de l'interface avec une version issue du pipeline | 4 |
| Historique Actions : un déploiement vert, un test rouge non déployé | 3 |
| Capture de l'assistant affiné (en-tête « eps-assistant ») et rappels avant/après | 3 |
| RAG : une réponse avec ses sources, les quatre rappels, et la réponse sur la session TEF après modification | 4 |
| Réponses aux questions de synthèse des labs 1 à 8 | 3 |
| Trois mesures du Lab 8 et preuve de nettoyage | 3 |

---

[Sommaire](README.md)
