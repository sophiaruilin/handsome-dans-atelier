"""Facts derived from the catalogue that the database doesn't store directly.

- affiliation: which residential college, graduate school, varsity team or family member a product is for
  (matched from its name and search tags), used by the website's "Affiliation" filter.
- fit: men's / women's / unisex, inferred from names like "Men's" or "Yale Mom". Almost everything
  is unisex, and the website shows unisex items under both men's and women's.
- Handsome Dan's Picks: a few products the mascot personally recommends, with a short note in his voice.
"""

from __future__ import annotations

import re
from typing import Literal

AffiliationGroup = Literal["college", "school", "team", "family"]
Fit = Literal["mens", "womens", "unisex"]

# (group, display name, match words). The first match wins, so specific names come first.
AFFILIATIONS: list[tuple[AffiliationGroup, str, tuple[str, ...]]] = [
    # Residential colleges
    ("college", "Benjamin Franklin", ("benjamin franklin", "benjamin-franklin")),
    ("college", "Berkeley", ("berkeley",)),
    ("college", "Branford", ("branford",)),
    ("college", "Davenport", ("davenport",)),
    ("college", "Grace Hopper", ("grace hopper", "grace-hopper")),
    ("college", "Jonathan Edwards", ("jonathan edwards", "jonathan-edwards")),
    ("college", "Morse", ("morse",)),
    ("college", "Pierson", ("pierson",)),
    ("college", "Saybrook", ("saybrook",)),
    ("college", "Timothy Dwight", ("timothy dwight", "timothy-dwight")),
    ("college", "Trumbull", ("trumbull",)),
    # Graduate and professional schools
    ("school", "School of Architecture", ("school of architecture", "school-of-architecture")),
    ("school", "School of Art", ("school of art", "school-of-art")),
    ("school", "Divinity School", ("divinity",)),
    ("school", "School of Engineering & Applied Science", ("school of engineering", "school-of-engineering")),
    ("school", "School of the Environment (Forest School)", ("forest school", "the-forest-school")),
    ("school", "Law School", ("law school", "yale-law-school")),
    ("school", "School of Management", ("school of management", "school-of-management")),
    ("school", "School of Medicine", ("school of medicine", "school-of-medicine")),
    ("school", "School of Music", ("school of music", "school-of-music")),
    ("school", "School of Nursing", ("school of nursing", "school-of-nursing")),
    ("school", "School of Public Health", ("school of public health", "school-of-public-health")),
    # Family
    ("family", "Mom", ("yale mom", "yale-mom", "mom hoodie")),
    ("family", "Dad", ("yale dad", "yale-dad", "dad hoodie", "dad shirt")),
    ("family", "Grandma", ("grandma",)),
    ("family", "Grandpa", ("grandpa",)),
    ("family", "Aunt", ("aunt",)),
    ("family", "Uncle", ("uncle",)),
    ("family", "Brother", ("yale brother", "yale-brother")),
    ("family", "Cousin", ("cousin",)),
    # Varsity teams
    ("team", "Baseball", ("baseball",)),
    ("team", "Basketball", ("basketball",)),
    ("team", "Diving", ("diving",)),
    ("team", "Fencing", ("fencing",)),
    ("team", "Field Hockey", ("field hockey", "field-hockey")),
    ("team", "Football", ("football", "the game", "yale bowl", "yale-bowl")),
    ("team", "Golf", ("golf",)),
    ("team", "Ice Hockey", ("hockey",)),
    ("team", "Lacrosse", ("lacrosse",)),
    ("team", "Crew", ("crew left chest", "crew-left-chest", "yale crew")),
    ("team", "Sailing", ("sailing",)),
    ("team", "Soccer", ("soccer",)),
    ("team", "Squash", ("squash",)),
    ("team", "Swimming", ("swimming",)),
    ("team", "Tennis", ("tennis",)),
    ("team", "Track & Field", ("track", "track-field")),
    ("team", "Volleyball", ("volleyball",)),
]

GROUP_LABELS: dict[AffiliationGroup, str] = {
    "college": "Residential Colleges",
    "school": "Graduate & Professional Schools",
    "team": "Varsity Teams",
    "family": "Family",
}

_WOMENS = re.compile(r"\b(women'?s|ladies|mom|grandma|aunt|sister)\b")
_MENS = re.compile(r"\b(men'?s|mens|dad|grandpa|uncle|brother)\b")


def affiliation(product_id: str, name: str, tags: list[str]) -> tuple[AffiliationGroup, str] | None:
    text = " ".join([product_id, name.lower(), *(t.lower() for t in tags)])
    for group, label, words in AFFILIATIONS:
        if any(w in text for w in words):
            return group, label
    return None


def fit(name: str, tags: list[str]) -> Fit:
    """Men's or women's only when the product says so; otherwise unisex."""
    text = " ".join([name.lower(), *(t.lower() for t in tags)])
    if _WOMENS.search(text):
        return "womens"
    if _MENS.search(text):
        return "mens"
    return "unisex"


# Handsome Dan knows a thing or two about looking handsome.
DAN_PICKS: dict[str, str] = {
    "basic-hoodie-big-yale": "The classic. Big YALE across the chest, so everyone knows where you belong. I'd wear it if I had arms that fit.",
    "champion-reverse-weave-crewneck": "Warm enough for the walk to Sterling, soft enough for a nap after. Ask me how I know.",
    "2025-yale-vs-harvard-t-shirt": "Wear it to The Game. Wear it the day after. Wear it until Harvard apologizes.",
    "district-vit-hoodie-vintage-bulldog": "A vintage bulldog on the front? I'm not saying it's me. I'm not saying it isn't.",
    "brooks-brothers-bomber-jacket-yale": "Dapper enough for the Yale Club, sturdy enough for Old Campus in January. Very handsome. Very Dan.",
    "yale-mom-hoodie": "For the one who drove you up I-95 with a minivan full of extension cords. She's earned it.",
    "yale-grandpa-crewneck": "Grandpa will wear this to every family dinner from now until forever. That's a five-biscuit gift.",
    "poly-twill-crewneck-arched-yale": "Cream and navy, like a proper Lawn Club afternoon. Pairs well with a tennis racquet and a smug grin.",
}


def dan_note(product_id: str) -> str | None:
    return DAN_PICKS.get(product_id)
