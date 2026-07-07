from rigor.checks.statcheck import StatResult, check_pvalue
from rigor.checks.grim import GrimResult, grim
from rigor.checks.grimmer import GrimmerResult, grimmer
from rigor.checks.consistency import DfNResult, check_df_vs_n
from rigor.checks.effectsize import EffectSizeResult, check_cohens_d

__all__ = [
    "StatResult", "check_pvalue",
    "GrimResult", "grim",
    "GrimmerResult", "grimmer",
    "DfNResult", "check_df_vs_n",
    "EffectSizeResult", "check_cohens_d",
]
