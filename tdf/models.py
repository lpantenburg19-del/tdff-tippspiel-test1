from datetime import datetime, date

from .db import db

CLASSIFICATIONS = ("gc", "points", "mountains", "youth", "team")

CLASSIFICATION_LABELS = {
    "gc": "Gesamtwertung (Gelbes Trikot)",
    "points": "Punktewertung (Grünes Trikot)",
    "mountains": "Bergwertung (Gepunktetes Trikot)",
    "youth": "Nachwuchswertung (Weißes Trikot)",
    "team": "Teamwertung",
}


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    name_normalized = db.Column(db.String(80), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    stage_predictions = db.relationship(
        "StagePrediction", backref="player", cascade="all, delete-orphan"
    )
    pretour_prediction = db.relationship(
        "PreTourPrediction", backref="player", uselist=False, cascade="all, delete-orphan"
    )


class Stage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.Integer, unique=True, nullable=False)
    date = db.Column(db.Date, nullable=False)
    is_locked = db.Column(db.Boolean, default=False, nullable=False)
    locked_at = db.Column(db.DateTime, nullable=True)

    predictions = db.relationship(
        "StagePrediction", backref="stage", cascade="all, delete-orphan"
    )
    result = db.relationship(
        "StageResult", backref="stage", uselist=False, cascade="all, delete-orphan"
    )


class StagePrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), nullable=False)
    predicted_rider = db.Column(db.String(120), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint("player_id", "stage_id"),)


class PreTourPrediction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey("player.id"), unique=True, nullable=False)
    gc_winner = db.Column(db.String(120))
    points_winner = db.Column(db.String(120))
    mountains_winner = db.Column(db.String(120))
    youth_winner = db.Column(db.String(120))
    team_winner = db.Column(db.String(120))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def field_for(self, classification):
        return getattr(self, f"{classification}_winner")


class StageResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    stage_id = db.Column(db.Integer, db.ForeignKey("stage.id"), unique=True, nullable=False)
    winning_rider = db.Column(db.String(120), nullable=False)
    source = db.Column(db.String(20), default="manual_override", nullable=False)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class FinalClassificationResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    classification = db.Column(db.String(20), unique=True, nullable=False)
    winner = db.Column(db.String(120), nullable=False)
    source = db.Column(db.String(20), default="manual_override", nullable=False)
    synced_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Rider(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    team_name = db.Column(db.String(120), nullable=True)
    is_captain = db.Column(db.Boolean, default=False, nullable=False)


class Team(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
