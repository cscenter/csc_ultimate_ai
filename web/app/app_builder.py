import logging

from flask import render_template
from flask_appbuilder import AppBuilder

from web.app import app, db
from web.app.competition import run_competition
from web.app.view.index import MyIndexView
from web.app.view.leaderboard import Leaderboard
from web.app.view.registration import AppSecurityManager
from web.app.view.submissions import SubmissionSettings
from apscheduler.schedulers.blocking import BlockingScheduler
from threading import Thread

db.create_all()

appbuilder = AppBuilder(app, db.session,
                        indexview=MyIndexView(),
                        security_manager_class=AppSecurityManager)


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )


appbuilder.add_view(Leaderboard, "Leaderboard", category='Leaderboard')
appbuilder.add_view(SubmissionSettings, "Submission settings", category="Submissions")

appbuilder.security_cleanup()


def run_background_scheduler():
    scheduler = BlockingScheduler()
    logging.info("Run competition on start")
    run_competition()
    logging.info("Schedule competitions")
    scheduler.add_job(run_competition, 'interval', minutes=15)
    scheduler.start()


thread = Thread(target=run_background_scheduler)
thread.start()
