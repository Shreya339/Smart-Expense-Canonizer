import json
import math
from typing import List, Tuple, Optional
from sqlmodel import select
from .models import MerchantEmbedding
from .db import get_session
from .config import OPENAI_API_KEY

# ==============================
# OpenAI Embedding Client
# ==============================
try:
    from openai import OpenAI
    openai_client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None
except Exception:
    openai_client = None


# ==============================
# Cosine Similarity
# ==============================
def cosine(a: List[float], b: List[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0

    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))

    if na == 0 or nb == 0:
        return 0.0

    return dot / (na * nb)


# ==============================
# Create embedding
# ==============================
def embed_text(text: str) -> Optional[List[float]]:
    if not openai_client:
        return None

    try:
        emb = openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=[text]
        )
        return emb.data[0].embedding

    except Exception:
        return None


# ==============================
# Find nearest merchant
# ==============================
def find_similar(embedding: List[float]) -> Tuple[Optional[MerchantEmbedding], float]:

    with get_session() as s:
        rows = s.exec(select(MerchantEmbedding)).all()

        best = None
        best_sim = 0.0

        for r in rows:
            vec = json.loads(r.embedding_json)
            sim = cosine(vec, embedding)

            if sim > best_sim:
                best_sim = sim
                best = r

        return best, best_sim


# ==============================
# UPSERT Merchant Memory
# ==============================
def upsert_merchant(name: str, embedding: Optional[List[float]], category: Optional[str], overridden=False):

    with get_session() as s:
        row = s.exec(
            select(MerchantEmbedding)
            .where(MerchantEmbedding.merchant_name == name)
        ).first()

        if not row:
            row = MerchantEmbedding(
                merchant_name=name,
                embedding_json=json.dumps(embedding or []),
                category_label=category,
                num_seen=1,
                num_overrides=1 if overridden else 0
            )
            s.add(row)

        else:
            row.num_seen += 1

            if overridden:
                row.num_overrides += 1

            if category:
                row.category_label = category

            if embedding:
                row.embedding_json = json.dumps(embedding)

        s.commit()


# ==============================
# DRIFT TRACKING
# ==============================
from collections import deque
import numpy as np

_recent = deque(maxlen=200)
_centroid = None


def _update_centroid(vec):
    global _centroid

    if vec is None:
        return

    _recent.append(vec)

    if len(_recent) == 0:
        return

    arr = np.array(_recent)
    _centroid = arr.mean(axis=0)


def compute_and_track_embedding(text: str):
    """
    Wrapper around embed_text() that ALSO:
      • updates centroid
      • detects embedding drift
      • returns (embedding, drift_flag)
    """

    vec = embed_text(text)

    drift_flag = False

    try:
        global _centroid

        if vec is not None and _centroid is not None:
            sim = np.dot(vec, _centroid) / (np.linalg.norm(vec) * np.linalg.norm(_centroid))

            if sim < 0.65:
                drift_flag = True

        _update_centroid(vec)

    except Exception:
        pass

    return vec, drift_flag
