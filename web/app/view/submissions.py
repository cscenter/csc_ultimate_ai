from flask_appbuilder import BaseView, expose
from web.app import db
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface

from web.app.models import SubmissionDockerImage, CompetitionRound


def get_user():
    return g.user


class Submissions(BaseView):
    default_view = 'total_results'

    @expose('total_results')
    def total_results(self):
        r = db.session.query(CompetitionRound).order_by(CompetitionRound.created_on.desc()).first()
        # session.query(ObjectRes).order_by(ObjectRes.id.desc()).first()
        data = [
            {'date': '2012-06-28', 'user': 405},
            {'date': '2012-06-29', 'user': 368},
            {'date': '2012-06-30', 'user': 119},
        ]
        self.update_redirect()
        return self.render_template('leaderboard.html', rows=data)


class SubmissionSettings(ModelView):
    datamodel = SQLAInterface(SubmissionDockerImage)
    # base_filters = [['created_by', FilterEqualFunction, get_user]]
    base_order = ('created_on', 'asc')

    label_columns = {'docker_image': 'Dockerhub image'}

    list_columns = [
        "competition",
        "docker_image",
        "comment",
        "last_competition",
        "last_score",
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
