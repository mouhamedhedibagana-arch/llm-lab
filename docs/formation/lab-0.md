# Lab 0 — Démarrer le Learner Lab et préparer le dépôt

[Sommaire](README.md) · [Lab 1 →](lab-1.md)


**Durée** : 30 min · **Prérequis** : invitation AWS Academy acceptée, compte GitHub · **Objectif** : ouvrir la console AWS dans la bonne région et posséder votre copie du code.

## Tâche 1 — Ouvrir la console AWS

1. Connectez-vous à AWS Academy et ouvrez le cours **AWS Academy Learner Lab**.
2. Cliquez **Modules**, puis **Launch AWS Academy Learner Lab**. À la première ouverture, acceptez les conditions d'utilisation.
3. Cliquez **Start Lab**, en haut à droite. *Attendu : le point à côté de « AWS » passe du rouge au vert en 1 à 3 minutes.*
4. Notez le budget affiché en haut de la page (« Used $0 of $50 ») et le temps de session restant (4 heures).
5. Cliquez sur **AWS**, à côté du point vert. *Attendu : la console AWS s'ouvre dans un nouvel onglet. Si rien ne s'ouvre, autorisez les fenêtres surgissantes pour ce site.*
6. En haut à droite de la console, vérifiez que la région est **United States (N. Virginia)**, c'est-à-dire `us-east-1`. Sinon, sélectionnez-la dans la liste.

## Tâche 2 — Créer votre dépôt GitHub

1. Ouvrez le dépôt modèle indiqué par l'enseignant.
2. Cliquez **Use this template**, puis **Create a new repository**.
3. Dans **Repository name**, saisissez `llm-lab`. Choisissez **Public**. Cliquez **Create repository**. *Attendu : votre dépôt `COMPTE/llm-lab` contient les dossiers `app`, `infra`, `pipeline` et `tests`.*
4. Cliquez le bouton vert **Code** et copiez l'adresse HTTPS dans un fichier de notes : `https://github.com/COMPTE/llm-lab.git`.

Le dépôt doit être **public** : l'instance le clonera sans mot de passe au Lab 2 et au Lab 4.

## Tâche 3 — Ouvrir CloudShell

1. Dans la console AWS, cliquez l'icône **CloudShell** (un terminal, dans la barre du haut). *Attendu : un terminal s'ouvre en bas de page en moins d'une minute.*
2. Tapez la commande suivante.

```bash
aws sts get-caller-identity
```

*Attendu : un bloc de ce type. Le champ `Arn` contient `voclabs`.*

```json
{
    "UserId": "AROA...:user1234567=Votre_Nom",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/voclabs/user1234567=Votre_Nom"
}
```

3. Notez le numéro `Account` à 12 chiffres.

## Point de contrôle

- [ ] La console est en `us-east-1`.
- [ ] Le dépôt `COMPTE/llm-lab` existe et il est public.
- [ ] Le numéro de compte AWS est noté.

**À retenir.** À la fin de la session, le Learner Lab arrête vos instances mais conserve vos ressources. Pour reprendre : **Start Lab**, puis redémarrez l'instance depuis la console EC2.

---

[Sommaire](README.md) · [Lab 1 →](lab-1.md)
