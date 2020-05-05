from flask import render_template, redirect
from flask_appbuilder import IndexView, expose


class MyIndexView(IndexView):
    @expose("/")
    def index(self):
        return redirect("/leaderboard/total_results")
