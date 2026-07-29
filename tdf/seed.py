from datetime import date

from .db import db
from .models import Stage

STAGE_DATES = [(n, date(2026, 8, n)) for n in range(1, 10)]


def seed_stages():
    if Stage.query.count() == 0:
        for number, stage_date in STAGE_DATES:
            db.session.add(Stage(number=number, date=stage_date, is_locked=False))
        db.session.commit()
