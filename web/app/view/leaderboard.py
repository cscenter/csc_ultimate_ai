import json

from flask import render_template
from flask_appbuilder import BaseView, expose
from web.app import db

from web.app.models import CompetitionRound


class Leaderboard(BaseView):
    default_view = 'total_results'

    @expose('total_results')
    def total_results(self):
        # db.session.add(CompetitionRound(data=json.dumps({
        #     'headers': ['user', 'date'],
        #     'data': [
        #         {'date': '2012-06-28', 'user': 405},
        #         {'date': '2012-06-29', 'user': 368},
        #         {'date': '2012-06-30', 'user': 119},
        #     ],
        #     'competition_time': '2012-06-30'
        # })))
        # db.session.flush()
        # db.session.commit()
        headers = []
        data = []
        competition_time = ''
        result = db.session.query(CompetitionRound).order_by(CompetitionRound.created_on.desc()).first()
        if result:
            json_data = json.loads(result.data)
            headers = json_data.get('headers', [])
            data = json_data.get('data', [])
            competition_time = json_data.get('competition_time', '')

        self.update_redirect()
        return self.render_template('leaderboard.html',
                                    rows=data, headers=headers, competition_time=competition_time)
