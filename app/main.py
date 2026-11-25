"""API du lab : relaie la conversation vers Ollama et sert l'interface web."""
import asyncio, json, logging, math, os, time
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://ollama:11434")
MODEL = os.environ.get("MODEL", "llama3.2:3b")
ACCESS_CODE = os.environ.get("ACCESS_CODE", "")
VERSION = os.environ.get("APP_VERSION", "dev")
SYSTEM = os.environ.get("SYSTEM_PROMPT",
                        "Tu es un assistant utile. Réponds en français, de façon concise.")
MAX_MESSAGES, MAX_CARACTERES = 20, 4000

ICI = os.path.dirname(__file__)
# Recherche documentaire (RAG) : désactivée par défaut, activée par RAG=1.
RAG = os.environ.get("RAG", "0").strip().lower() in ("1", "true", "oui", "yes")
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3")
RAG_FICHIER = os.environ.get("RAG_FICHIER", os.path.join(ICI, "connaissances.md"))
RAG_K = int(os.environ.get("RAG_K", "3"))                  # passages donnés au modèle
RAG_SEUIL = float(os.environ.get("RAG_SEUIL", "0.45"))      # similarité minimale d'un passage

logging.basicConfig(level=logging.INFO, format="%(message)s")


class Conversation(BaseModel):
    messages: list[dict]
    rag: bool | None = None          # None : réglage du serveur ; False : sans recherche (comparaison)


async def flux_ollama(messages):
    """Produit le texte généré, morceau par morceau."""
    corps = {"model": MODEL, "messages": messages, "stream": True}
    async with httpx.AsyncClient(timeout=None) as client:
        async with client.stream("POST", f"{OLLAMA_URL}/api/chat", json=corps) as r:
            r.raise_for_status()
            async for ligne in r.aiter_lines():
                if ligne:
                    yield json.loads(ligne).get("message", {}).get("content", "")


async def modeles_installes():
    async with httpx.AsyncClient(timeout=3) as client:
        r = await client.get(f"{OLLAMA_URL}/api/tags")
        # Ollama liste « nom:latest » pour un modèle créé sans étiquette.
        return {n for m in r.json().get("models", []) for n in (m["name"], m["name"].removesuffix(":latest"))}


async def modele_pret():
    try:
        return MODEL in await modeles_installes()
    except Exception:
        return False


async def embedding_pret():
    try:
        return EMBED_MODEL in await modeles_installes()
    except Exception:
        return False


# ---------- Recherche documentaire (RAG) ----------

def lire_passages(chemin):
    """Un passage par paragraphe ; « ## » donne le thème ; les lignes « > » sont des notes ignorées."""
    with open(chemin, encoding="utf-8") as f:
        texte = f.read().replace("\r\n", "\n")
    passages, theme = [], ""
    for bloc in texte.split("\n\n"):
        lignes = [l for l in bloc.strip().splitlines() if not l.startswith(">")]
        if lignes and lignes[0].startswith("#"):
            theme = lignes.pop(0).lstrip("#").strip()
        if lignes:
            passages.append({"numero": len(passages) + 1, "theme": theme, "texte": " ".join(" ".join(lignes).split())})
    return passages


def normaliser(v):
    n = math.sqrt(sum(x * x for x in v)) or 1.0
    return [x / n for x in v]


async def plonger(textes):
    """Vecteurs (embeddings) des textes, calculés par Ollama."""
    async with httpx.AsyncClient(timeout=600) as client:
        r = await client.post(f"{OLLAMA_URL}/api/embed", json={"model": EMBED_MODEL, "input": textes})
        r.raise_for_status()
        return [normaliser(v) for v in r.json()["embeddings"]]


_index = {"passages": [], "vecteurs": []}
_verrou = asyncio.Lock()


async def index():
    """Calcule une fois pour toutes les vecteurs des passages du fichier de connaissances."""
    async with _verrou:
        if not _index["vecteurs"]:
            debut = time.time()
            passages = lire_passages(RAG_FICHIER)
            vecteurs = await plonger([f"{p['theme']} : {p['texte']}" for p in passages])
            _index.update(passages=passages, vecteurs=vecteurs)
            logging.info(json.dumps({"evenement": "index", "passages": len(passages),
                                     "duree_s": round(time.time() - debut, 1)}))
    return _index


async def rechercher(question, k=RAG_K):
    """Les k passages les plus proches de la question, du plus proche au moins proche."""
    idx = await index()
    q = (await plonger([question]))[0]
    scores = [sum(a * b for a, b in zip(q, v)) for v in idx["vecteurs"]]
    ordre = sorted(range(len(scores)), key=scores.__getitem__, reverse=True)[:k]
    return [dict(idx["passages"][i], score=round(scores[i], 3)) for i in ordre]


def consigne(passages):
    refs = "\n".join(f"[{p['numero']}] {p['theme']} : {p['texte']}" for p in passages)
    return ("\n\nInformations de référence, tirées des documents de l'école :\n" + refs +
            "\n\nRéponds à partir de ces informations. Si elles ne contiennent pas la réponse, "
            "dis que tu ne sais pas et renvoie vers le service admission.")


_taches = set()


@asynccontextmanager
async def cycle_de_vie(_app):
    """Au démarrage, prépare l'index en arrière-plan pour que la première question ne l'attende pas."""
    async def essai():
        try:
            await index()
        except Exception as e:                            # modèle d'embedding pas encore installé
            logging.info(json.dumps({"evenement": "index_reporte", "raison": type(e).__name__}))
    if RAG:
        tache = asyncio.create_task(essai())
        _taches.add(tache)
        tache.add_done_callback(_taches.discard)
    yield


app = FastAPI(title="LLM Lab", lifespan=cycle_de_vie)


# ---------- Routes ----------

def valider(messages):
    if not messages or len(messages) > MAX_MESSAGES:
        raise HTTPException(422, f"entre 1 et {MAX_MESSAGES} messages")
    for m in messages:
        if m.get("role") not in ("user", "assistant") or not isinstance(m.get("content"), str):
            raise HTTPException(422, "message invalide")
        if len(m["content"]) > MAX_CARACTERES:
            raise HTTPException(422, f"message de plus de {MAX_CARACTERES} caractères")
    return [{"role": m["role"], "content": m["content"]} for m in messages]


def verifier_code(code):
    if ACCESS_CODE and code != ACCESS_CODE:
        raise HTTPException(401, "code d'accès invalide")


@app.get("/")
def accueil():
    return FileResponse(os.path.join(ICI, "static", "index.html"))


@app.get("/api/health")
async def health():
    etat = {"ok": True, "version": VERSION, "modele": MODEL, "modele_pret": await modele_pret(), "rag": RAG}
    if RAG:
        etat.update(embedding=EMBED_MODEL, embedding_pret=await embedding_pret(), passages=len(_index["passages"]))
    return etat


@app.get("/api/recherche")
async def recherche(q: str, k: int = 5, x_access_code: str = Header(default="")):
    """Montre les passages que la recherche trouve pour une question, avec leur similarité."""
    verifier_code(x_access_code)
    try:
        return {"question": q, "seuil": RAG_SEUIL, "passages": await rechercher(q[:MAX_CARACTERES], max(1, min(k, 20)))}
    except (httpx.HTTPError, OSError) as e:
        raise HTTPException(503, f"recherche impossible ({type(e).__name__}) : vérifiez que {EMBED_MODEL} est installé")


@app.post("/api/chat")
async def chat(conv: Conversation, x_access_code: str = Header(default="")):
    verifier_code(x_access_code)
    messages = valider(conv.messages)
    systeme, sources = SYSTEM, []
    if RAG and conv.rag is not False:
        question = next(m["content"] for m in reversed(messages) if m["role"] == "user")
        try:
            sources = [p for p in await rechercher(question) if p["score"] >= RAG_SEUIL]
        except (httpx.HTTPError, OSError) as e:
            raise HTTPException(503, f"recherche impossible ({type(e).__name__}) : vérifiez que {EMBED_MODEL} est installé")
        if sources:
            systeme += consigne(sources)
    messages = [{"role": "system", "content": systeme}] + messages

    async def generer():
        debut, n = time.time(), 0
        try:
            async for morceau in flux_ollama(messages):
                n += len(morceau)
                yield morceau
        except httpx.HTTPError as e:
            yield f"\n[erreur du serveur de modèle : {type(e).__name__}]"
        logging.info(json.dumps({"evenement": "chat", "version": VERSION, "modele": MODEL,
                                 "sources": [p["numero"] for p in sources],
                                 "caracteres": n, "duree_s": round(time.time() - debut, 1)}))

    entete = json.dumps([{k: p[k] for k in ("numero", "theme", "score", "texte")} for p in sources])
    return StreamingResponse(generer(), media_type="text/plain; charset=utf-8", headers={"X-Sources": entete})
