"""
utils/rm_config.py
═══════════════════════════════════════════════════════════════════
RELATIONSHIP MANAGER (RM) CONFIGURATION
═══════════════════════════════════════════════════════════════════

TO ADD / CHANGE AN RM:  Edit RM_MAP below.
TO ADD A NEW PROJECT:   Add:  "RAGHAV NewProject": "RM Full Name",

RM RESPONSIBILITIES:
  • Sending demand notices to customers
  • Following up with customers
  • Collecting money from customers
  • Accountable for Spill Over collection and overall outstanding

NOTE: OCR (Own Contribution) and New Booking targets are Sales team
      responsibility. CRM team only reports these figures.
"""

RM_MAP: dict[str, str] = {
    "RAGHAV Ananta":   "Siddhesh Sawant",
    "RAGHAV Parijat":  "Pratap Mali",
    "RAGHAV Vista":    "Priyanka Watulkar",
    "RAGHAV Avenue":   "Priyanka Watulkar",
    "RAGHAV Enclave":  "Priyanka Watulkar",
    "RAGHAV Utopia":   "Snigdha Gautam",
    "RAGHAV Paradise": "Pratap Mali",
}

RM_COLORS: dict[str, str] = {
    "Siddhesh Sawant":   "#1A3C6E",
    "Pratap Mali":       "#2E7D32",
    "Priyanka Watulkar": "#7B1FA2",
    "Snigdha Gautam":    "#E65100",
}

RM_PHOTOS: dict[str, str] = {
    "Siddhesh Sawant":   "",
    "Pratap Mali":       "",
    "Priyanka Watulkar": "",
    "Snigdha Gautam":    "",
}

def _normalise(name: str) -> str:
    """Strip newlines, collapse multiple spaces, lowercase."""
    import re
    return re.sub(r'\s+', ' ', str(name).replace('\n', ' ')).strip().lower()

def get_rm(project_name: str) -> str:
    """Return RM for a project. Handles newlines and double spaces from Excel."""
    proj_norm = _normalise(project_name)
    for key, rm in RM_MAP.items():
        if _normalise(key) == proj_norm:
            return rm
    # Fuzzy: check if normalised key is contained in normalised project or vice versa
    for key, rm in RM_MAP.items():
        key_norm = _normalise(key)
        if key_norm in proj_norm or proj_norm in key_norm:
            return rm
    return "Unassigned"

def get_rm_projects() -> dict[str, list[str]]:
    result: dict[str, list[str]] = {}
    for proj, rm in RM_MAP.items():
        result.setdefault(rm, []).append(proj)
    return result

def all_rms() -> list[str]:
    return sorted(set(RM_MAP.values()))
