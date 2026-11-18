"""Entirely synthetic Phase 2D fixtures; no market or HFT files."""
from decimal import Decimal
from pathlib import Path
from data_pipeline.labels.matcher import MarketRow

FIXTURE_DIR = Path(__file__).parent

def rows(times=(0,100,200,500,1000), mids=None, source="synthetic",
         session="artificial_session", view="aggregate_core_v1", valid=None):
    if mids is None:
        mids = ["100"] * len(times)
    if valid is None:
        valid = [True] * len(times)
    return [MarketRow(source,session,i+1,view,t,
                      None if mids[i] is None else Decimal(str(mids[i])),valid[i])
            for i,t in enumerate(times)]
