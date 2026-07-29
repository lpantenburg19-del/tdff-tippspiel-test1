from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from .. import pcs_sync
from ..auth import admin_required, check_admin_password
from ..db import db
from ..models import CLASSIFICATIONS, CLASSIFICATION_LABELS, FinalClassificationResult, Stage, StageResult

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if check_admin_password(request.form.get("password")):
            session["is_admin"] = True
            return redirect(url_for("admin.dashboard"))
        flash("Falsches Passwort.")
        return redirect(url_for("admin.login"))
    return render_template("admin/login.html")


@bp.route("/logout")
def logout():
    session.pop("is_admin", None)
    return redirect(url_for("admin.login"))


@bp.route("/")
@admin_required
def dashboard():
    stages = Stage.query.order_by(Stage.number.asc()).all()
    stage_results = {r.stage_id: r for r in StageResult.query.all()}
    final_results = {r.classification: r for r in FinalClassificationResult.query.all()}
    return render_template(
        "admin/dashboard.html",
        stages=stages,
        stage_results=stage_results,
        final_results=final_results,
        classifications=CLASSIFICATIONS,
        labels=CLASSIFICATION_LABELS,
    )


@bp.route("/stage/<int:number>/lock", methods=["POST"])
@admin_required
def lock_stage(number):
    stage = Stage.query.filter_by(number=number).first_or_404()
    stage.is_locked = True
    stage.locked_at = datetime.utcnow()
    db.session.commit()
    flash(f"Etappe {number} gesperrt.")
    return redirect(url_for("admin.dashboard"))


@bp.route("/stage/<int:number>/unlock", methods=["POST"])
@admin_required
def unlock_stage(number):
    stage = Stage.query.filter_by(number=number).first_or_404()
    stage.is_locked = False
    stage.locked_at = None
    db.session.commit()
    flash(f"Etappe {number} entsperrt.")
    return redirect(url_for("admin.dashboard"))


@bp.route("/stage/<int:number>/sync", methods=["POST"])
@admin_required
def sync_stage(number):
    try:
        winner = pcs_sync.sync_stage_result(number)
        flash(f"Etappe {number}: Ergebnis übernommen — Siegerin: {winner}")
    except pcs_sync.SyncError as exc:
        flash(f"Sync fehlgeschlagen: {exc}")
    return redirect(url_for("admin.dashboard"))


@bp.route("/stage/<int:number>/override", methods=["POST"])
@admin_required
def override_stage(number):
    stage = Stage.query.filter_by(number=number).first_or_404()
    winner = (request.form.get("winning_rider") or "").strip()
    if not winner:
        flash("Bitte einen Namen eingeben.")
        return redirect(url_for("admin.dashboard"))

    result = StageResult.query.filter_by(stage_id=stage.id).first()
    if result is None:
        result = StageResult(stage_id=stage.id)
        db.session.add(result)
    result.winning_rider = winner
    result.source = "manual_override"
    result.synced_at = datetime.utcnow()
    db.session.commit()
    flash(f"Etappe {number}: Ergebnis manuell gesetzt auf {winner}.")
    return redirect(url_for("admin.dashboard"))


@bp.route("/final/sync", methods=["POST"])
@admin_required
def sync_final():
    try:
        synced, failed = pcs_sync.sync_final_classifications()
        if synced:
            flash("Übernommen: " + ", ".join(f"{k}={v}" for k, v in synced.items()))
        if failed:
            flash(
                "Nicht verfügbar (bitte manuell setzen): "
                + ", ".join(f"{k} ({v})" for k, v in failed.items())
            )
    except pcs_sync.SyncError as exc:
        flash(f"Sync fehlgeschlagen: {exc}")
    return redirect(url_for("admin.dashboard"))


@bp.route("/final/override", methods=["POST"])
@admin_required
def override_final():
    classification = request.form.get("classification")
    winner = (request.form.get("winner") or "").strip()
    if classification not in CLASSIFICATIONS or not winner:
        flash("Ungültige Eingabe.")
        return redirect(url_for("admin.dashboard"))

    result = FinalClassificationResult.query.filter_by(classification=classification).first()
    if result is None:
        result = FinalClassificationResult(classification=classification)
        db.session.add(result)
    result.winner = winner
    result.source = "manual_override"
    result.synced_at = datetime.utcnow()
    db.session.commit()
    flash(f"{labels_lookup(classification)}: manuell gesetzt auf {winner}.")
    return redirect(url_for("admin.dashboard"))


def labels_lookup(classification):
    return CLASSIFICATION_LABELS.get(classification, classification)


@bp.route("/startlist/sync", methods=["POST"])
@admin_required
def sync_startlist():
    try:
        count = pcs_sync.sync_startlist()
        flash(f"Startliste synchronisiert: {count} Fahrerinnen.")
    except pcs_sync.SyncError as exc:
        flash(f"Sync fehlgeschlagen: {exc}")
    return redirect(url_for("admin.dashboard"))
