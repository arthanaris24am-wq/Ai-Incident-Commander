import os
from dotenv import load_dotenv

load_dotenv()


class Config:

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "super-secret-key"
    )

    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY",
        "jwt-secret"
    )

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URI",
        "sqlite:///incident_commander.db"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False