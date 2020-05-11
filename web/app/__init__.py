import logging
#
from contextlib import contextmanager

from flask import Flask
# from flask_appbuilder import AppBuilder, SQLA
#
# """
#  Logging configuration
# """
#
from flask_appbuilder import SQLA

from base.util import log_level_from_env

logging.basicConfig(format="%(asctime)s:%(levelname)s:%(name)s:%(message)s")
level = log_level_from_env()
logging.getLogger().setLevel(level)

app = Flask(__name__)

app.config.from_object("config")
db = SQLA(app)


@contextmanager
def db_session():
    """Provide a transactional scope around a series of operations."""
    session = db.session
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()


"""
from sqlalchemy.engine import Engine
from sqlalchemy import event

#Only include this for SQLLite constraints
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    # Will force sqllite contraint foreign keys
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
"""

# from . import views
from . import app_builder
