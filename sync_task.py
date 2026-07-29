"""Standalone script for the daily PythonAnywhere scheduled task.

Fetches results for any stage that has already happened but has no result yet,
and once the final stage is done, fetches the final classifications too.
Safe to run repeatedly — already-synced stages are just re-synced (harmless).
"""

from datetime import date

from tdf import create_app
from tdf import pcs_sync
from tdf.models import Stage, StageResult

app = create_app()

with app.app_context():
    today = date.today()
    due_stages = Stage.query.filter(Stage.date <= today).order_by(Stage.number.asc()).all()

    last_stage_done = False
    for stage in due_stages:
        try:
            winner = pcs_sync.sync_stage_result(stage.number)
            print(f"Etappe {stage.number}: {winner}")
            if stage.number == pcs_sync.LAST_STAGE_NUMBER:
                last_stage_done = True
        except pcs_sync.SyncError as exc:
            print(f"Etappe {stage.number}: Sync fehlgeschlagen — {exc}")

    if last_stage_done:
        try:
            synced, failed = pcs_sync.sync_final_classifications()
            print("Endklassierungen übernommen:", synced)
            if failed:
                print("Endklassierungen nicht verfügbar (manuell setzen):", failed)
        except pcs_sync.SyncError as exc:
            print(f"Endklassierungen: Sync fehlgeschlagen — {exc}")
