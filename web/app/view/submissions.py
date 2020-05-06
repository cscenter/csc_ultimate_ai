from flask import g
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.filters import FilterEqualFunction
from flask_appbuilder.models.sqla.interface import SQLAInterface

from web.app.models import SubmissionDockerImage


def get_user():
    return g.user


class SubmissionSettings(ModelView):
    datamodel = SQLAInterface(SubmissionDockerImage)
    base_filters = [['created_by', FilterEqualFunction, get_user]]
    base_order = ('created_on', 'asc')

    label_columns = {'docker_image': 'Dockerhub image'}

    list_columns = [
        "competition",
        "docker_image",
        "comment",
        "last_competition",
        "last_score",
        "pull_status",
        "created_on"
    ]
    add_columns = [
        "docker_image",
        "comment"
    ]
    # edit_columns = [
    #     "comment",
    #     "active"
    # ]
