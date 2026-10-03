"""Centralized, versioned SOV Semantic Concept Taxonomy and Alias Dictionary.

Defines:
1. Core SOV concepts and their explicit multi-word and single-word aliases.
2. Ambiguous terms classified into broad signal families with reduced confidence.
3. Negative guard patterns to prevent false positives (e.g., 'statement' matching 'state').
"""

from typing import Any, Final

TAXONOMY_VERSION: Final[str] = "1.0.0"

# Core Definitive SOV Concepts and their canonical aliases
CORE_CONCEPT_ALIASES: Final[dict[str, list[str]]] = {
    # --- Reference / Location Identity ---
    "ref": [
        "ref",
        "reference",
        "reference id",
        "reference number",
        "ref no",
        "ref id",
        "property id",
        "location id",
        "loc id",
        "location number",
        "site id",
    ],
    "addr": [
        "address",
        "street",
        "street address",
        "mailing address",
        "property address",
    ],
    "city": [
        "city",
        "municipality",
    ],
    "state": [
        "state",
        "province",
        "region",
    ],
    "zip": [
        "zip",
        "zip code",
        "zipcode",
        "postal",
        "postal code",
        "postcode",
    ],
    "county": [
        "county",
    ],
    "country": [
        "country",
        "nation",
    ],
    # --- Property Values ---
    "val_bldg": [
        "building value",
        "building cost",
        "bldg value",
        "bldg cost",
        "structure value",
        "structure cost",
    ],
    "val_cont": [
        "contents",
        "contents value",
        "contents cost",
        "bpp",
        "business personal property",
    ],
    "val_bi": [
        "bi",
        "business interruption",
        "business interruption value",
        "time element",
        "time element value",
    ],
    "val_tiv": [
        "tiv",
        "total insured value",
        "total value",
    ],
    # --- Property Characteristics ---
    "occ": [
        "occupancy",
        "occupancy type",
        "tenant",
        "property use",
    ],
    "const": [
        "construction",
        "construction type",
        "const",
        "const type",
    ],
    "stories": [
        "stories",
        "storeys",
        "floors",
        "number of stories",
        "number of floors",
    ],
    "yr_built": [
        "year built",
        "year constructed",
        "built",
        "construction year",
    ],
    "sprinkler": [
        "sprinkler",
        "sprinklers",
        "sprinklered",
        "fire sprinkler",
        "fire sprinklers",
    ],
}

# Ambiguous Standalone Terms that provide directional signal but do NOT warrant definitive mapping
AMBIGUOUS_TERMS: Final[dict[str, dict[str, Any]]] = {
    "site": {
        "concept": "location_signal",
        "confidence": 0.60,
        "description": "Ambiguous location signal (could be address or ref)",
    },
    "location": {
        "concept": "location_signal",
        "confidence": 0.60,
        "description": "Ambiguous location signal (could be address or ref)",
    },
    "property": {
        "concept": "location_signal",
        "confidence": 0.50,
        "description": "Ambiguous property identifier or general description",
    },
    "building": {
        "concept": "building_signal",
        "confidence": 0.50,
        "description": "Ambiguous building token (lacks 'value' or 'cost' qualifier)",
    },
    "value": {
        "concept": "value_signal",
        "confidence": 0.50,
        "description": "Ambiguous value token without asset specification",
    },
    "cost": {
        "concept": "value_signal",
        "confidence": 0.50,
        "description": "Ambiguous cost token without asset specification",
    },
    "use": {
        "concept": "use_signal",
        "confidence": 0.50,
        "description": "Ambiguous use token without property qualifier",
    },
}

# Negative Guard Patterns: Cell strings that contain these words are guarded
# from triggering false matches on specific concepts
NEGATIVE_GUARDS: Final[dict[str, list[str]]] = {
    "state": ["statement", "status", "estate"],
    "val_bldg": ["building number", "building id", "building name"],
    "val_tiv": ["motivation"],
    "ref": ["reference manual", "reference rate"],
}
