import unicodedata

from .models import (
    CLASSIFICATIONS,
    FinalClassificationResult,
    Player,
    PreTourPrediction,
    StagePrediction,
    StageResult,
)

STAGE_POINTS = 5
CLASSIFICATION_POINTS = {
    "gc": 15,
    "points": 10,
    "mountains": 10,
    "youth": 10,
    "team": 5,
}


def normalize(value):
    if not value:
        return None
    value = value.strip().lower()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    return value or None


MIN_SUBSTRING_LEN = 3


def is_match(guess, official):
    guess_n = normalize(guess)
    official_n = normalize(official)
    if not guess_n or not official_n:
        return False
    if guess_n == official_n:
        return True
    if len(guess_n) < MIN_SUBSTRING_LEN:
        return False
    return guess_n in official_n or official_n in guess_n


def compute_leaderboard():
    players = Player.query.order_by(Player.name.asc()).all()
    stage_results = {r.stage_id: r.winning_rider for r in StageResult.query.all()}
    final_results = {r.classification: r.winner for r in FinalClassificationResult.query.all()}

    board = {
        p.id: {"player": p, "points": 0, "breakdown": []}
        for p in players
    }

    for pred in StagePrediction.query.all():
        actual = stage_results.get(pred.stage_id)
        if actual and is_match(pred.predicted_rider, actual):
            entry = board.get(pred.player_id)
            if entry is not None:
                entry["points"] += STAGE_POINTS
                entry["breakdown"].append(
                    f"Etappe {pred.stage.number}: +{STAGE_POINTS} ({pred.predicted_rider})"
                )

    for pred in PreTourPrediction.query.all():
        entry = board.get(pred.player_id)
        if entry is None:
            continue
        for classification in CLASSIFICATIONS:
            actual = final_results.get(classification)
            guess = pred.field_for(classification)
            if actual and is_match(guess, actual):
                pts = CLASSIFICATION_POINTS[classification]
                entry["points"] += pts
                entry["breakdown"].append(f"{classification}: +{pts} ({guess})")

    return sorted(board.values(), key=lambda entry: -entry["points"])
