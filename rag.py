#!/usr/bin/env python3
import os
import re
import json
import math
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from collections import Counter

import numpy as np
from groq import groq_chat

RAG_DIR = os.path.dirname(os.path.abspath(__file__))
HACKERONE_DIR = os.path.join(RAG_DIR, "hackerone")
EMBEDDINGS_FILE = os.path.join(RAG_DIR, "rag_embeddings.json")
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
TOP_K = 3


@dataclass
class Chunk:
    id: int
    text: str
    source: str
    page: int
    tokens: List[str] = field(default_factory=list)
    vector: Optional[np.ndarray] = None


@dataclass
class RetrievalResult:
    chunks: List[Chunk]
    query: str
    scores: List[float]


STOP_WORDS = set(
    "le la les un une des du de la que qui dans pour sur avec ce cet cette ces "
    "est sont ont ete sera etre avait aurait pourront pourrait peuvent "
    "fait fais faire faisant ainsi aussi alors apres avant ailleurs beaucoup "
    "car cela ceux chez combien comme comment depuis dont elle elles en "
    "entre eux ici il ils je lui ma mais me meme mes moi mon ne ni nom "
    "notre nous ou par pas par ici peu plus quand que quel quelle quels "
    "quelles sa sans se ses si son sont sous ta te tes toi ton tous tout "
    "tres trop tu un une vos votre vous y ai aient ait avez"
    .split()
)

TOKEN_REGEX = re.compile(r"[a-zA-Z0-9]+")


def tokenize(text: str) -> List[str]:
    return [t.lower() for t in TOKEN_REGEX.findall(text) if t.lower() not in STOP_WORDS and len(t) > 1]


def extract_text_from_pdf(pdf_path: str) -> str:
    result = subprocess.run(
        ["mutool", "draw", "-F", "text", pdf_path],
        capture_output=True, text=True, timeout=120
    )
    return result.stdout


def chunk_text(text: str, source: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[Chunk]:
    paragraphs = re.split(r"\n\s*\n", text)
    chunks = []
    current_text = ""
    chunk_id = 0
    page = 1

    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if re.match(r"^\s*\d+\s*$", para):
            continue

        page_match = re.search(r"page\s*(\d+)|(\d+)\s*/\s*\d+", para, re.IGNORECASE)
        if page_match:
            p = page_match.group(1) or page_match.group(2)
            if p:
                try:
                    page = int(p)
                except ValueError:
                    pass

        current_text += para + "\n"

        while len(current_text) >= chunk_size:
            slice_text = current_text[:chunk_size]
            last_space = slice_text.rfind(" ")
            if last_space > chunk_size // 2:
                slice_text = slice_text[:last_space]

            tokens = tokenize(slice_text)
            chunks.append(Chunk(id=chunk_id, text=slice_text.strip(), source=source, page=page, tokens=tokens))
            chunk_id += 1

            overlap_start = max(0, len(slice_text) - overlap)
            current_text = current_text[overlap_start:]

    if current_text.strip():
        tokens = tokenize(current_text)
        chunks.append(Chunk(id=chunk_id, text=current_text.strip(), source=source, page=page, tokens=tokens))

    return chunks


def build_vocabulary(all_chunks: List[Chunk]) -> dict:
    vocab = {}
    for chunk in all_chunks:
        for token in chunk.tokens:
            if token not in vocab:
                vocab[token] = len(vocab)
    return vocab


def tfidf_vectorize(tokens: List[str], vocab: dict, idf: Optional[dict] = None) -> np.ndarray:
    vec = np.zeros(len(vocab))
    if not tokens:
        return vec

    counter = Counter(tokens)
    max_freq = max(counter.values())

    for token, count in counter.items():
        if token in vocab:
            tf = count / max_freq
            if idf:
                vec[vocab[token]] = tf * idf.get(token, 1.0)
            else:
                vec[vocab[token]] = tf

    return vec


def compute_idf(chunks: List[Chunk], vocab: dict) -> dict:
    n_docs = len(chunks)
    doc_freq = Counter()
    for chunk in chunks:
        unique_tokens = set(chunk.tokens)
        for token in unique_tokens:
            if token in vocab:
                doc_freq[token] += 1

    idf = {}
    for token, freq in doc_freq.items():
        idf[token] = math.log(n_docs / (1 + freq)) + 1
    return idf


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


class RAGSystem:
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.chunks: List[Chunk] = []
        self.vocab: dict = {}
        self.idf: dict = {}
        self.embeddings: np.ndarray = np.array([])
        self.ready = False

    def load_documents(self, directory: str = HACKERONE_DIR):
        print(f"Chargement des documents depuis {directory}...")
        all_chunks = []

        for root, dirs, files in os.walk(directory):
            for fname in files:
                if fname.lower().endswith(".pdf"):
                    pdf_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(pdf_path, directory)
                    print(f"  Extraction: {rel_path}")
                    try:
                        text = extract_text_from_pdf(pdf_path)
                        chunks = chunk_text(text, rel_path, self.chunk_size, self.overlap)
                        all_chunks.extend(chunks)
                        print(f"    -> {len(chunks)} chunks extraits")
                    except subprocess.TimeoutExpired:
                        print(f"    -> TIMEOUT (ignore)")
                    except Exception as e:
                        print(f"    -> Erreur: {e}")

        self.chunks = all_chunks
        print(f"\nTotal: {len(self.chunks)} chunks")
        return len(self.chunks)

    def build_index(self):
        print("Construction de l'index vectoriel...")
        self.vocab = build_vocabulary(self.chunks)
        print(f"  Vocabulaire: {len(self.vocab)} termes uniques")

        self.idf = compute_idf(self.chunks, self.vocab)

        vectors = []
        for chunk in self.chunks:
            vec = tfidf_vectorize(chunk.tokens, self.vocab, self.idf)
            vectors.append(vec)

        self.embeddings = np.array(vectors)
        print(f"  Matrice d'embedding: {self.embeddings.shape}")
        self.ready = True

    def save_index(self, path: str = EMBEDDINGS_FILE):
        data = {
            "chunk_size": self.chunk_size,
            "overlap": self.overlap,
            "vocab": list(self.vocab.keys()),
            "idf": {k: self.idf.get(k, 1.0) for k in self.vocab.keys()},
            "chunks": [
                {"id": c.id, "text": c.text, "source": c.source, "page": c.page, "tokens": c.tokens}
                for c in self.chunks
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        np.save(path.replace(".json", "_vectors.npy"), self.embeddings)
        print(f"Index sauvegarde: {path}")

    def load_index(self, path: str = EMBEDDINGS_FILE):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.chunk_size = data["chunk_size"]
        self.overlap = data["overlap"]
        self.vocab = {word: i for i, word in enumerate(data["vocab"])}
        self.idf = {word: data["idf"].get(word, 1.0) for word in data["vocab"]}
        self.chunks = [
            Chunk(id=c["id"], text=c["text"], source=c["source"], page=c["page"], tokens=c["tokens"])
            for c in data["chunks"]
        ]
        self.embeddings = np.load(path.replace(".json", "_vectors.npy"))
        self.ready = True
        print(f"Index charge: {len(self.chunks)} chunks, vocabulaire: {len(self.vocab)} termes")

    def retrieve(self, query: str, k: int = TOP_K) -> RetrievalResult:
        if not self.ready:
            raise RuntimeError("Index non initialise. Appelle load_documents() + build_index() d'abord.")

        query_tokens = tokenize(query)
        query_vec = tfidf_vectorize(query_tokens, self.vocab, self.idf)

        similarities = []
        for i, chunk_vec in enumerate(self.embeddings):
            sim = cosine_similarity(query_vec, chunk_vec)
            similarities.append((i, sim))

        similarities.sort(key=lambda x: x[1], reverse=True)
        top_k = similarities[:k]

        result_chunks = []
        scores = []
        for idx, sim in top_k:
            if sim > 0.01:
                result_chunks.append(self.chunks[idx])
                scores.append(sim)

        return RetrievalResult(chunks=result_chunks, query=query, scores=scores)

    def generate(self, query: str, k: int = TOP_K) -> str:
        results = self.retrieve(query, k)

        if not results.chunks:
            return groq_chat([
                {"role": "system", "content": "Tu es un assistant specialise en cybersecurite. "
                 "Reponds en francais de maniere concise."},
                {"role": "user", "content": f"Question: {query}\n\n(Aucun document pertinent trouve dans la base.)"}
            ])

        context_parts = []
        for i, (chunk, score) in enumerate(zip(results.chunks, results.scores)):
            context_parts.append(
                f"[Document {i+1}] Source: {chunk.source} (page {chunk.page})\n"
                f"Pertinence: {score:.2%}\n{chunk.text[:1000]}"
            )

        context = "\n\n---\n\n".join(context_parts)

        messages = [
            {"role": "system", "content": "Tu es un analyste en cybersecurite qui repond aux questions "
             "en se basant uniquement sur les documents fournis en contexte. "
             "Si les documents ne contiennent pas la reponse, dis-le clairement. "
             "Reponds en francais de maniere structuree."},
            {"role": "user", "content": f"Contexte (rapports de bug bounty HackerOne):\n\n{context}\n\n"
             f"---\n\nQuestion: {query}\n\n"
             "Reponds en te basant sur les documents fournis. Cite les sources pertinentes."}
        ]

        return groq_chat(messages)


def main():
    import sys
    rag = RAGSystem()

    if os.path.exists(EMBEDDINGS_FILE):
        rag.load_index()
    else:
        count = rag.load_documents()
        if count == 0:
            print("Aucun document trouve.")
            return
        rag.build_index()
        rag.save_index()

    print("\n" + "=" * 70)
    print("  RAG THREAT INTELLIGENCE — Recherche semantique dans les rapports HackerOne")
    print("  Tape 'exit' pour quitter.")
    print("=" * 70)

    while True:
        try:
            query = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if query.lower() in ("exit", "quit", "q"):
            break
        if not query:
            continue
        if query.lower() == "stats":
            print(f"  Chunks: {len(rag.chunks)}, Vocabulaire: {len(rag.vocab)} termes")
            continue

        print(f"\n  Recherche: \"{query}\"")
        results = rag.retrieve(query)
        if results.chunks:
            print(f"  {len(results.chunks)} documents pertinents trouves:")
            for i, (chunk, score) in enumerate(zip(results.chunks, results.scores)):
                preview = chunk.text[:120].replace("\n", " ")
                print(f"    [{i+1}] (pertinence: {score:.2%}) {chunk.source} p.{chunk.page}: \"{preview}...\"")
        else:
            print("  Aucun document pertinent trouve.")

        print("\n  Generation de la reponse...")
        response = rag.generate(query)
        print(f"\n  REPONSE:\n{'-'*70}\n{response}\n{'-'*70}")


if __name__ == "__main__":
    main()
