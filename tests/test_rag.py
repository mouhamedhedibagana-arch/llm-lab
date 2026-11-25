"""Tests de la recherche documentaire (RAG), avec de faux embeddings : ils tournent sans Ollama."""
import json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "app"))
os.environ.setdefault("ACCESS_CODE", "secret")
import main
import pytest
from fastapi.testclient import TestClient

CONNAISSANCES = """# Connaissances de test

> Cette note n'est pas un passage.

## Contact

L'école se trouve à Sousse, adresse : route de test.

## Frais

Les frais du cycle ingénieur sont de 100 DT par an.

## Clubs

Le club de robotique s'appelle Polyrobots.
"""

MOTS = ["adresse", "frais", "robotique"]


def vecteur(texte):
    """Faux embedding : un compteur de mots-clés, plus une petite composante commune."""
    texte = texte.lower()
    return main.normaliser([float(texte.count(m)) for m in MOTS] + [0.01])


async def faux_plonger(textes):
    return [vecteur(t) for t in textes]


recu = {}


async def faux_flux(messages):
    recu["messages"] = messages
    yield "ok"


async def faux_pret():
    return True


@pytest.fixture
def client(tmp_path, monkeypatch):
    fichier = tmp_path / "connaissances.md"
    fichier.write_text(CONNAISSANCES, encoding="utf-8")
    monkeypatch.setattr(main, "RAG", True)
    monkeypatch.setattr(main, "RAG_FICHIER", str(fichier))
    monkeypatch.setattr(main, "plonger", faux_plonger)
    monkeypatch.setattr(main, "flux_ollama", faux_flux)
    monkeypatch.setattr(main, "modele_pret", faux_pret)
    monkeypatch.setattr(main, "embedding_pret", faux_pret)
    monkeypatch.setattr(main, "_index", {"passages": [], "vecteurs": []})
    return TestClient(main.app)


BON = {"x-access-code": main.ACCESS_CODE}


def question(texte, **extra):
    return {"messages": [{"role": "user", "content": texte}], **extra}


def test_lecture_des_passages(tmp_path):
    fichier = tmp_path / "c.md"
    fichier.write_text(CONNAISSANCES, encoding="utf-8")
    passages = main.lire_passages(str(fichier))
    assert [p["theme"] for p in passages] == ["Contact", "Frais", "Clubs"]
    assert not any("note" in p["texte"] for p in passages)


def test_rag_donne_le_bon_passage_au_modele(client):
    r = client.post("/api/chat", json=question("Quels sont les frais ?"), headers=BON)
    assert r.status_code == 200
    assert "100 DT" in recu["messages"][0]["content"]
    sources = json.loads(r.headers["x-sources"])
    assert sources[0]["theme"] == "Frais"


def test_rag_ignore_les_passages_sous_le_seuil(client):
    r = client.post("/api/chat", json=question("Bonjour"), headers=BON)
    assert json.loads(r.headers["x-sources"]) == []
    assert recu["messages"][0]["content"] == main.SYSTEM


def test_rag_desactivable_par_requete(client):
    r = client.post("/api/chat", json=question("Quels sont les frais ?", rag=False), headers=BON)
    assert json.loads(r.headers["x-sources"]) == []
    assert recu["messages"][0]["content"] == main.SYSTEM


def test_recherche_protegee_et_triee(client):
    assert client.get("/api/recherche", params={"q": "robotique"}).status_code == 401
    r = client.get("/api/recherche", params={"q": "club de robotique"}, headers=BON).json()
    assert r["passages"][0]["theme"] == "Clubs"
    scores = [p["score"] for p in r["passages"]]
    assert scores == sorted(scores, reverse=True)
