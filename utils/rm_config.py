"""
utils/rm_config.py
═══════════════════════════════════════════════════════════════════
RELATIONSHIP MANAGER (RM) CONFIGURATION
═══════════════════════════════════════════════════════════════════

TO ADD / CHANGE AN RM:
  Edit the RM_MAP dictionary below.
  Key   = exact project name as it appears in the Excel
  Value = RM full name

TO ADD A NEW PROJECT:
  Add a new line:  "RAGHAV NewProject": "RM Full Name",

RM RESPONSIBILITIES:
  • Sending demand notices to customers
  • Following up with customers
  • Collecting money from customers
  • Managing CRM pipeline for their assigned project(s)

NOTE:
  OCR (Own Contribution) and New Booking collection targets are set
  and collected by the SALES TEAM — CRM team only reports these figures.
  RMs are accountable for Spill Over collection and overall outstanding.
"""

# ── Edit below this line ───────────────────────────────────────────────────────

RM_MAP: dict[str, str] = {
    "RAGHAV Ananta":   "Siddhesh Sawant",
    "RAGHAV Parijat":  "Pratap Mali",
    "RAGHAV Vista":    "Priyanka Watulkar",
    "RAGHAV Avenue":   "Priyanka Watulkar",
    "RAGHAV Enclave":  "Priyanka Watulkar",
    "RAGHAV Utopia":   "Snigdha Gautam",
    "RAGHAV Paradise": "Pratap Mali",
}

# RM photos (optional — leave as empty string if not available)
RM_PHOTOS: dict[str, str] = {
    "Siddhesh Sawant":   "",
    "Pratap Mali":       "",
    "Priyanka Watulkar": "",
    "Snigdha Gautam":    "",
}

# RM colour palette (used consistently across charts)
RM_COLORS: dict[str, str] = {
    "Siddhesh Sawant":   "#1A3C6E",
    "Pratap Mali":       "#2E7D32",
    "Priyanka Watulkar": "#7B1FA2",
    "Snigdha Gautam":    "#E65100",
}

# ── Do not edit below this line ───────────────────────────────────────────────

def get_rm(project_name: str) -> str:
    """Return RM name for a project. Fuzzy-matches partial names."""
    # Exact match first
    if project_name in RM_MAP:
        return RM_MAP[project_name]
    # Partial match (case-insensitive)
    proj_lower = project_name.lower().strip()
    for key, rm in RM_MAP.items():
        if key.lower() in proj_lower or proj_lower in key.lower():
            return rm
    return "Unassigned"


def get_rm_projects() -> dict[str, list[str]]:
    """Return dict of {RM: [project1, project2, ...]}"""
    result: dict[str, list[str]] = {}
    for proj, rm in RM_MAP.items():
        result.setdefault(rm, []).append(proj)
    return result


def all_rms() -> list[str]:
    """Return sorted list of unique RM names."""
    return sorted(set(RM_MAP.values()))
