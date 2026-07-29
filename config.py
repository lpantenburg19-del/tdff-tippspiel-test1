import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "changeme")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "instance", "tippspiel.db"
        )
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PCS_RACE_SLUG = os.environ.get("PCS_RACE_SLUG", "tour-de-france-femmes")
    PCS_RACE_YEAR = int(os.environ.get("PCS_RACE_YEAR", "2026"))
