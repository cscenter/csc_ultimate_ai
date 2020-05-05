import logging

from flask import render_template
from flask_appbuilder import AppBuilder, SQLA

from web.app import app, db
from web.app.view.index import MyIndexView
from web.app.view.leaderboard import Leaderboard
from web.app.view.submissions import Submissions, SubmissionSettings


db.create_all()

appbuilder = AppBuilder(app, db.session, indexview=MyIndexView())
appbuilder.add_view(Leaderboard, "Leaderboard", category='Leaderboard')
# appbuilder.add_view(Submissions, "Submissions", category='Submissions')
appbuilder.add_view(SubmissionSettings, "Submission settings", category="Submissions")


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )
