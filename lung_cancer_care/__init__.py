import pymysql

pymysql.install_as_MySQLdb()

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except Exception:  # pragma: no cover - celery optional in some environments
    pass
