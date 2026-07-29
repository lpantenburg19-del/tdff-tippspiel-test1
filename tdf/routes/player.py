from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..auth import current_player, player_required
from ..db import db
from ..models import (
    CLASSIFICATIONS,
    CLASSIFICATION_LABELS,
    Player,
    PreTourPrediction,
    Stage,
    StagePrediction,
)
from ..rider_groups import build_rider_groups, build_team_options
from ..scoring import compute_leaderboard

bp = Blueprint("player", __name__)


@bp.route("/", methods=["GET", "POST"])
def join():
    if request.method == "POST":
        raw_name = (request.form.get("name") or "").strip()
        if not raw_name:
            flash("Bitte gib einen Namen ein.")
            return redirect(url_for("player.join"))

        normalized = raw_name.lower()
        player = Player.query.filter_by(name_normalized=normalized).first()
        if player is None:
            player = Player(name=raw_name, name_normalized=normalized)
            db.session.add(player)
            db.session.commit()

        session.permanent = True
        session["player_id"] = player.id
        return redirect(url_for("player.stages_overview"))

    if current_player() is not None:
        return redirect(url_for("player.stages_overview"))
    session.pop("player_id", None)
    return render_template("join.html")


@bp.route("/logout")
def logout():
    session.pop("player_id", None)
    return redirect(url_for("player.join"))


@bp.route("/pretour", methods=["GET", "POST"])
@player_required
def pretour():
    player = current_player()
    first_stage = Stage.query.filter_by(number=1).first()
    locked = bool(first_stage and first_stage.is_locked)

    prediction = player.pretour_prediction
    if prediction is None:
        prediction = PreTourPrediction(player_id=player.id)
        db.session.add(prediction)
        db.session.commit()

    if request.method == "POST":
        if locked:
            flash("Die Vorab-Tipps sind gesperrt, da Etappe 1 bereits gestartet ist.")
            return redirect(url_for("player.pretour"))

        prediction.gc_winner = (request.form.get("gc_winner") or "").strip()
        prediction.points_winner = (request.form.get("points_winner") or "").strip()
        prediction.mountains_winner = (request.form.get("mountains_winner") or "").strip()
        prediction.youth_winner = (request.form.get("youth_winner") or "").strip()
        prediction.team_winner = (request.form.get("team_winner") or "").strip()
        db.session.commit()
        flash("Vorab-Tipps gespeichert.")
        return redirect(url_for("player.pretour"))

    return render_template(
        "pretour_picks.html",
        prediction=prediction,
        locked=locked,
        rider_groups=build_rider_groups(),
        team_options=build_team_options(),
        classifications=CLASSIFICATIONS,
        labels=CLASSIFICATION_LABELS,
    )


@bp.route("/stages")
@player_required
def stages_overview():
    player = current_player()
    stages = Stage.query.order_by(Stage.number.asc()).all()
    my_picks = {
        p.stage_id: p.predicted_rider
        for p in StagePrediction.query.filter_by(player_id=player.id).all()
    }
    return render_template("stages_overview.html", stages=stages, my_picks=my_picks)


@bp.route("/stage/<int:number>", methods=["GET", "POST"])
@player_required
def stage_pick(number):
    player = current_player()
    stage = Stage.query.filter_by(number=number).first_or_404()

    pick = StagePrediction.query.filter_by(player_id=player.id, stage_id=stage.id).first()

    if request.method == "POST":
        if stage.is_locked:
            flash(f"Etappe {number} ist gesperrt, Tipps werden nicht mehr angenommen.")
            return redirect(url_for("player.stage_pick", number=number))

        rider_name = (request.form.get("predicted_rider") or "").strip()
        if not rider_name:
            flash("Bitte eine Fahrerin auswählen.")
            return redirect(url_for("player.stage_pick", number=number))

        if pick is None:
            pick = StagePrediction(player_id=player.id, stage_id=stage.id, predicted_rider=rider_name)
            db.session.add(pick)
        else:
            pick.predicted_rider = rider_name
        db.session.commit()
        flash(f"Tipp für Etappe {number} gespeichert.")
        return redirect(url_for("player.stages_overview"))

    return render_template(
        "stage_picks.html", stage=stage, pick=pick, rider_groups=build_rider_groups()
    )


@bp.route("/leaderboard")
def leaderboard():
    board = compute_leaderboard()
    return render_template("leaderboard.html", board=board)


@bp.route("/rules")
def rules():
    return render_template("rules.html", classifications=CLASSIFICATIONS, labels=CLASSIFICATION_LABELS)
