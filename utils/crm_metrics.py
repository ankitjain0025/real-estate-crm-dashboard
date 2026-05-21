"""
CRM Metrics computation helpers.
All values are in Indian Crores (Cr) unless stated otherwise.
"""
import pandas as pd


def collection_efficiency(collection: float, demand: float) -> float:
    """Collection / Demand * 100."""
    try:
        return round(collection / demand * 100, 2) if demand else 0.0
    except Exception:
        return 0.0


def overdue_summary(project_df: pd.DataFrame) -> pd.DataFrame:
    """
    Build a project-wise overdue/outstanding summary.
    Uses 'Outstanding (Cr)' column from project_df.
    """
    cols_needed = ["Project", "Outstanding (Cr)", "Pending Registrations",
                   "Pending Reg > 45 Days"]
    available = [c for c in cols_needed if c in project_df.columns]
    return project_df[available].copy()


def top_defaulters(project_df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Return projects sorted by outstanding (highest first)."""
    if "Outstanding (Cr)" not in project_df.columns:
        return project_df.head(n)
    return (
        project_df
        .sort_values("Outstanding (Cr)", ascending=False)
        .head(n)
        [["Project", "Outstanding (Cr)", "Actual Demand Raised (Cr)",
          "Collection Till Date (Cr)", "Pending Registrations"]]
        .reset_index(drop=True)
    )


def demand_vs_collection(project_df: pd.DataFrame) -> pd.DataFrame:
    """Return tidy dataframe for demand-vs-collection comparison."""
    cols = {
        "Project": "Project",
        "Actual Demand Raised (Cr)": "Demand (Cr)",
        "Collection Till Date (Cr)": "Collection (Cr)",
        "Outstanding (Cr)": "Outstanding (Cr)",
    }
    available = {k: v for k, v in cols.items() if k in project_df.columns}
    df = project_df[list(available.keys())].rename(columns=available).copy()
    df["Collection Eff %"] = df.apply(
        lambda r: collection_efficiency(r["Collection (Cr)"], r["Demand (Cr)"]),
        axis=1,
    )
    return df


def monthly_target_vs_achievement(project_df: pd.DataFrame) -> pd.DataFrame:
    """Monthly collection target vs achievement by project."""
    cols = {
        "Project": "Project",
        "Collection Target (Cr)": "Target (Cr)",
        "Collection Achievement (Cr)": "Achievement (Cr)",
        "Achievement %": "Achievement %",
        "CRM Forecast (Cr)": "Forecast (Cr)",
    }
    available = {k: v for k, v in cols.items() if k in project_df.columns}
    return project_df[list(available.keys())].rename(columns=available).copy()
