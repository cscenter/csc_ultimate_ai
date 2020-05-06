import datetime

from flask_appbuilder import Model
from flask_appbuilder.security.sqla.models import User
from flask_appbuilder.models.mixins import AuditMixin
from sqlalchemy import Column, Integer, String, DateTime, Boolean


class MyUser(User):
    __tablename__ = "ab_user"
    approved = Column(Boolean, nullable=False, default=True)


class SubmissionDockerImage(AuditMixin, Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    competition = Column(String(250), nullable=False, default='UltimateGame')
    docker_image = Column(String(2048), nullable=False)
    comment = Column(String(2048), nullable=True)
    last_competition = Column(DateTime, nullable=True)
    last_score = Column(String(2048), nullable=True)
    pull_status = Column(String(250), nullable=False, default='Waiting')


class CompetitionRound(Model):
    id = Column(Integer, primary_key=True, autoincrement=True)
    competition = Column(String(250), nullable=False, default='UltimateGame')
    created_on = Column(DateTime, default=datetime.datetime.now, nullable=False)
    data = Column(String(65536), nullable=False)
