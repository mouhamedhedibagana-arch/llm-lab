# Lab 8 — Mesurer, superviser, nettoyer

[Sommaire](README.md) · [← Lab 7](lab-7.md)


**Durée** : 45 min · **Prérequis** : Lab 7 · **Objectif** : chiffrer la performance et le coût du service, vérifier qu'il survit à un redémarrage, puis tout supprimer.

## Tâche 1 — Mesurer la latence, seul puis à plusieurs

Dans CloudShell, avec votre adresse et votre code :

```bash
URL=http://ADRESSE-DE-L-INSTANCE
CODE=MON-CODE
appel() {
  curl -s -o /dev/null -w "%{time_total} s\n" $URL/api/chat \
    -H "x-access-code: $CODE" -H "content-type: application/json" \
    -d '{"messages":[{"role":"user","content":"Donne trois usages du cloud."}]}'
}
appel                          # une requête seule
appel & appel & appel & wait   # trois requêtes en même temps
```

Après les labs 6 et 7, c'est l'assistant affiné qui répond, avec le RAG : ses réponses sont plus courtes, donc vos durées seront plus faibles que celles indiquées ci-dessous, mesurées avec `llama3.2:3b` seul.

*Attendu : une durée pour l'appel seul, puis trois durées échelonnées. Soyez patient : la série complète prend 3 à 4 minutes. Valeurs du test : 66 s seul ; 54 s, 110 s et 160 s à trois.*

Notez vos quatre durées. Les trois requêtes simultanées ne sont pas traitées en même temps : comment le voyez-vous dans les chiffres ?

## Tâche 2 — Lire les journaux et les métriques

1. Sur l'instance (Session Manager) :

```bash
cd /opt/llm && sudo docker compose logs app --tail 10
```

*Attendu : une ligne JSON par requête, de ce type :*

```json
{"evenement": "chat", "version": "ccf4a22", "modele": "llama3.2:3b", "caracteres": 631, "duree_s": 66.3}
```

2. Console EC2 > instance `llm-lab` > onglet **Monitoring**. Repérez sur **CPU utilization** les pics qui correspondent à vos requêtes. Les points sont espacés de 5 minutes.

## Tâche 3 — Calculer le coût

1. Relevez le budget consommé sur la page du Learner Lab (la valeur se met à jour avec retard).
2. Avec le tarif horaire de l'instance (0,083 $ pour `t3.large`) et la durée d'un appel seul mesurée à la tâche 1, calculez le coût de 1 000 réponses si l'instance ne sert qu'une requête à la fois. Exemple avec 66 s : 1 000 × 66 s = 18,3 heures, soit environ 1,50 $.
3. Calculez combien d'heures d'instance il vous reste avec le crédit restant.

## Tâche 4 — Simuler une fin de session

1. Console EC2 > `llm-lab` > **Instance state** > **Stop instance**. *Attendu : état **Stopped** en 30 à 60 secondes.*
2. **Instance state** > **Start instance**. *Attendu : état **Running** en 20 secondes environ.*
3. Dans la console EC2, relevez le nouveau **Public IPv4 DNS**. Attention : la sortie `Url` de la pile CloudFormation affiche encore l'ancienne adresse, qui ne répond plus.
4. Ouvrez la nouvelle adresse. *Attendu, moins d'une minute après le démarrage : l'interface répond, le modèle est « prêt », et l'exécuteur GitHub repasse **Idle** sans intervention.*

## Tâche 5 — Nettoyer

1. GitHub > **Settings** > **Actions** > **Runners** > menu `...` de l'exécuteur > **Remove runner** > **Force remove this runner**.
2. Dans CloudShell :

```bash
aws cloudformation delete-stack --stack-name llm-lab
aws cloudformation wait stack-delete-complete --stack-name llm-lab
aws ecr delete-repository --repository-name llm-app --force
aws ec2 describe-instances --query "Reservations[].Instances[].State.Name"
```

*Attendu : la deuxième commande rend la main après 30 à 60 secondes ; la dernière ne liste que des états `terminated`, ou rien.*

3. Console EC2 > **Security Groups** : supprimez le groupe créé au Lab 1, dont le nom commence par `launch-wizard` (cochez-le > **Actions** > **Delete security groups**). Ne touchez pas au groupe `default`.
4. Page du Learner Lab > **End Lab**.

## Point de contrôle

- [ ] Vous donnez trois chiffres : latence seul, latence à trois, coût de 1 000 réponses.
- [ ] Le service a redémarré seul après un arrêt.
- [ ] Plus aucune instance, pile ni dépôt ECR.

## Questions de synthèse

1. Pourquoi la latence augmente-t-elle avec trois requêtes simultanées ? Citez deux façons d'y remédier hors Learner Lab.
2. Qu'est-ce qui manque à ce service pour être mis en production ? Attendu : HTTPS, authentification par utilisateur, journaux centralisés, haute disponibilité, GPU.

---

[Sommaire](README.md) · [← Lab 7](lab-7.md)
