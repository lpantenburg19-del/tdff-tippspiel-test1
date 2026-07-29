from datetime import datetime

from flask import current_app
from procyclingstats import RaceStartlist, Stage

from .db import db
from .models import CLASSIFICATIONS, FinalClassificationResult, Rider, Stage as StageModel, StageResult

LAST_STAGE_NUMBER = 9


class SyncError(Exception):
    """Raised when a fetch from procyclingstats.com fails or returns unexpected data."""


def _race_slug():
    return current_app.config["PCS_RACE_SLUG"]


def _race_year():
    return current_app.config["PCS_RACE_YEAR"]


def _stage_url(number):
    return f"race/{_race_slug()}/{_race_year()}/stage-{number}"


def sync_startlist():
    """Fetch the startlist and (re)populate the Rider autocomplete table."""
    try:
        startlist = RaceStartlist(f"race/{_race_slug()}/{_race_year()}/startlist").startlist()
    except Exception as exc:
        raise SyncError(f"Startlist-Abruf fehlgeschlagen: {exc}") from exc

    if not startlist:
        raise SyncError("Startlist ist leer oder konnte nicht gelesen werden.")

    existing = {r.name for r in Rider.query.all()}
    for entry in startlist:
        name = (entry.get("rider_name") or "").strip()
        if name and name not in existing:
            db.session.add(Rider(name=name))
            existing.add(name)
    db.session.commit()
    return len(startlist)


def sync_stage_result(stage_number):
    """Fetch a single stage's winner from procyclingstats and upsert StageResult."""
    stage = StageModel.query.filter_by(number=stage_number).first()
    if stage is None:
        raise SyncError(f"Etappe {stage_number} existiert nicht.")

    try:
        results = Stage(_stage_url(stage_number)).results()
    except Exception as exc:
        raise SyncError(f"Ergebnis-Abruf für Etappe {stage_number} fehlgeschlagen: {exc}") from exc

    if not results:
        raise SyncError(f"Noch kein Ergebnis für Etappe {stage_number} verfügbar.")

    winner = (results[0].get("rider_name") or "").strip()
    if not winner:
        raise SyncError(f"Kein Fahrername im Ergebnis von Etappe {stage_number}.")

    existing = StageResult.query.filter_by(stage_id=stage.id).first()
    if existing is None:
        existing = StageResult(stage_id=stage.id)
        db.session.add(existing)
    existing.winning_rider = winner
    existing.source = "pcs_auto"
    existing.synced_at = datetime.utcnow()
    db.session.commit()
    return winner


_CLASSIFICATION_METHODS = {
    "gc": ("gc", "rider_name"),
    "points": ("points", "rider_name"),
    "mountains": ("kom", "rider_name"),
    "youth": ("youth", "rider_name"),
    "team": ("teams", "team_name"),
}


def sync_final_classifications():
    """Fetch final classifications from the last stage's result page and upsert them.

    Each classification is fetched independently — some (e.g. the mountains
    classification) are not always exposed by the source for every edition, so a
    missing one must not block saving the others. Returns (synced, failed) where
    both are dicts keyed by classification.
    """
    try:
        last_stage = Stage(_stage_url(LAST_STAGE_NUMBER))
    except Exception as exc:
        raise SyncError(f"Endklassierungen-Abruf fehlgeschlagen: {exc}") from exc

    synced = {}
    failed = {}
    for classification, (method_name, field) in _CLASSIFICATION_METHODS.items():
        try:
            rows = getattr(last_stage, method_name)()
            winner = (rows[0].get(field) or "").strip() if rows else ""
            if not winner:
                raise ValueError("keine Daten von der Quelle geliefert")
        except Exception as exc:
            failed[classification] = str(exc)
            continue

        existing = FinalClassificationResult.query.filter_by(classification=classification).first()
        if existing is None:
            existing = FinalClassificationResult(classification=classification)
            db.session.add(existing)
        existing.winner = winner
        existing.source = "pcs_auto"
        existing.synced_at = datetime.utcnow()
        synced[classification] = winner

    db.session.commit()

    if not synced and failed:
        raise SyncError(
            "Keine Endklassierung konnte übernommen werden: "
            + ", ".join(f"{k} ({v})" for k, v in failed.items())
        )

    return synced, failed
