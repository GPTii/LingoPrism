"""Shared first cell of the algorithm notebooks: Django of BE/ (models, database, the algorithm code) + matplotlib.

The notebooks run the *same* code as the server (BE/apps/algorithms) – nothing is copied – so a result found here is
exactly what the admin page "Thuật toán AI" shows. Kernel: "LingoPrism (BE venv)" (BE/.venv with ipykernel).
"""
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BE = ROOT / "BE"
FIGURES = ROOT / "AI" / "notebooks" / "figures"


def init():
    sys.path.insert(0, str(BE))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"  # Jupyter runs an event loop; the ORM is used synchronously here
    os.chdir(BE)
    import django

    django.setup()
    import matplotlib.pyplot as plt

    plt.rcParams.update({"figure.dpi": 110, "figure.figsize": (8, 4.2), "axes.grid": True, "grid.alpha": 0.3,
                         "font.family": ["DejaVu Sans", "Microsoft YaHei"], "axes.spines.top": False,
                         "axes.spines.right": False})
    FIGURES.mkdir(parents=True, exist_ok=True)
    print("Django OK –", os.environ["DJANGO_SETTINGS_MODULE"], "| hình lưu ở", FIGURES)


def save(fig, name: str):
    """Keep every chart as a PNG (AI/notebooks/figures/) for the thesis report."""
    path = FIGURES / f"{name}.png"
    fig.savefig(path, bbox_inches="tight", dpi=160)
    return path


def table(rows: list[dict], cols: list[str] | None = None):
    """Small text table (no pandas needed)."""
    cols = cols or list(rows[0])
    fmt = lambda v: f"{v:.4f}" if isinstance(v, float) else str(v)
    width = {c: max(len(c), *(len(fmt(r.get(c, ""))) for r in rows)) for c in cols}
    print("  ".join(c.ljust(width[c]) for c in cols))
    print("  ".join("-" * width[c] for c in cols))
    for r in rows:
        print("  ".join(fmt(r.get(c, "")).ljust(width[c]) for c in cols))
