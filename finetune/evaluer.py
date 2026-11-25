"""Compare des modèles, ou l'application avec et sans RAG, sur test.jsonl (questions jamais vues à l'entraînement).

Pour chaque question, on mesure le « rappel » : la part des mots importants de la réponse
de référence (mots de 4 lettres ou plus, nombres) que l'on retrouve dans la réponse.

Deux façons de l'utiliser :
  python evaluer.py MODELE [MODELE ...] [--url http://localhost:11434]   interroge Ollama directement
  python evaluer.py --api http://localhost --code CODE                   passe par l'application,
                                                                         avec puis sans recherche (RAG)
Options communes : --n 20 (nombre de questions), --sortie evaluation.json
"""
import argparse
import json
import re
import time
import unicodedata
import urllib.request

p = argparse.ArgumentParser()
p.add_argument("modeles", nargs="*")
p.add_argument("--url", default="http://localhost:11434", help="adresse d'Ollama")
p.add_argument("--api", help="adresse de l'application, pour l'évaluer avec et sans RAG")
p.add_argument("--code", default="", help="code d'accès de l'application")
p.add_argument("--donnees", default="test.jsonl")
p.add_argument("--n", type=int, default=0, help="nombre de questions (0 = toutes)")
p.add_argument("--sortie", default="evaluation.json")
args = p.parse_args()
if not args.modeles and not args.api:
    p.error("indiquez au moins un modèle, ou --api")


def mots(texte):
    texte = unicodedata.normalize("NFKD", texte.lower()).encode("ascii", "ignore").decode()
    texte = re.sub(r"(?<=\d)[   ](?=\d)", "", texte)          # « 7 849 » -> « 7849 »
    return {m for m in re.findall(r"[a-z0-9@._-]+", texte) if len(m) >= 4 or m.isdigit()}


def poster(url, corps, entetes=None):
    req = urllib.request.Request(url, data=json.dumps(corps).encode(),
                                 headers={"content-type": "application/json", **(entetes or {})})
    return urllib.request.urlopen(req, timeout=900)


def demander_ollama(modele, messages):
    corps = {"model": modele, "messages": messages, "stream": False, "options": {"temperature": 0, "num_predict": 200}}
    with poster(f"{args.url}/api/chat", corps) as r:
        rep = json.load(r)
    debit = rep.get("eval_count", 0) / max(rep.get("eval_duration", 1) / 1e9, 1e-9)
    return rep["message"]["content"].strip(), [], debit


def demander_api(rag, messages):
    """Seule la question part : l'application ajoute elle-même son prompt système et, si RAG, les passages."""
    corps = {"messages": [m for m in messages if m["role"] == "user"], "rag": rag}
    with poster(f"{args.api}/api/chat", corps, {"x-access-code": args.code}) as r:
        sources = [s["numero"] for s in json.loads(r.headers.get("x-sources") or "[]")]
        return r.read().decode("utf-8").strip(), sources, None


with open(args.donnees, encoding="utf-8") as f:
    tests = [json.loads(ligne)["messages"] for ligne in f]
if args.n:
    tests = tests[:args.n]

if args.api:
    with urllib.request.urlopen(f"{args.api}/api/health", timeout=10) as r:
        sante = json.load(r)
    if not sante.get("rag"):
        print("Attention : RAG désactivé dans l'application (RAG=1 manquant) : les deux lignes seront équivalentes.")
    variantes = [(f"{sante['modele']} avec RAG", lambda m: demander_api(None, m)),
                 (f"{sante['modele']} sans RAG", lambda m: demander_api(False, m))]
else:
    variantes = [(m, lambda msgs, m=m: demander_ollama(m, msgs)) for m in args.modeles]

resultats = []
for nom, demander in variantes:
    debut, rappels, debits = time.time(), [], []
    for msgs in tests:
        reference = msgs[-1]["content"]
        reponse, sources, debit = demander(msgs[:-1])
        debits.append(debit)
        attendus = mots(reference)
        rappel = len(attendus & mots(reponse)) / len(attendus)
        rappels.append(rappel)
        resultats.append({"variante": nom, "question": msgs[1]["content"], "reference": reference,
                          "reponse": reponse, "sources": sources, "rappel": round(rappel, 2)})
    duree = time.time() - debut
    vitesse = (f"{sum(debits) / len(debits):.1f} tokens/s" if debits[0] is not None
               else f"{duree / len(rappels):.0f} s par réponse")
    print(f"{nom:28s} rappel moyen {100 * sum(rappels) / len(rappels):5.1f} % · "
          f"réponses à plus de 80 % : {sum(r >= 0.8 for r in rappels)}/{len(rappels)} · "
          f"{vitesse} · {duree:.0f} s", flush=True)

with open(args.sortie, "w", encoding="utf-8") as f:
    json.dump(resultats, f, ensure_ascii=False, indent=1)
print(f"Détail des réponses dans {args.sortie}")
