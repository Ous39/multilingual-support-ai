from __future__ import annotations

import re

from app.models import Language

FRENCH_MARKERS = {
    "bonjour", "comment", "pourquoi", "argent", "compte", "paiement", "retirer",
    "envoyer", "bloqué", "aide", "merci", "frais", "annuler", "transaction",
}
WOLOF_MARKERS = {
    "naka", "jërëjëf", "xaalis", "yónnee", "jot", "sama", "ndimbal", "waaw",
    "déedéet", "lan", "lu", "mën", "duma", "fay", "kàddu", "baat",
}


def detect_language(text: str) -> Language:
    tokens = set(re.findall(r"[\wÀ-ÿ]+", text.lower()))
    fr_score = len(tokens & FRENCH_MARKERS)
    wo_score = len(tokens & WOLOF_MARKERS)
    if wo_score > fr_score and wo_score > 0:
        return "wo"
    if fr_score > 0:
        return "fr"
    return "en"
