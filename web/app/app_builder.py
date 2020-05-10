import datetime
import json
import logging
import time
from typing import Optional

from flask import render_template
from flask_appbuilder import AppBuilder
from sqlalchemy import func
from flask_appbuilder.security.sqla.models import User

from web.app import app, db
from web.app.models import CompetitionRound, SubmissionDockerImage
from web.app.view.index import MyIndexView
from web.app.view.leaderboard import Leaderboard
from web.app.view.submissions import SubmissionSettings
from apscheduler.schedulers.blocking import BlockingScheduler

db.create_all()

appbuilder = AppBuilder(app, db.session, indexview=MyIndexView())


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

import docker
from threading import Thread
from time import sleep
from contextlib import contextmanager


@contextmanager
def session_scope(db):
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


# TODO refactor it
def run_competition():
    competition_time = datetime.datetime.now()
    logging.info(f"Launch competition time:%s", competition_time)
    client = docker.from_env()
    containers = client.containers.list(all=True)
    # short_id, name id, status 'running'
    # agent_containers
    for c in containers:
        if c.name.startswith("ai_agent_"):
            logging.info(f"Stop previous agent container:{c.name}")
            c.remove(force=True)
        if c.name.startswith("ai_server"):
            logging.info(f"Stop previous server container:{c.name}")
            c.remove(force=True)

    rank_subquery = db.session.query(
        SubmissionDockerImage.created_by_fk,
        SubmissionDockerImage.id,
        SubmissionDockerImage.docker_image,
        SubmissionDockerImage.created_on,
        func.rank().over(
            order_by=SubmissionDockerImage.created_on.desc(),
            partition_by=SubmissionDockerImage.created_by_fk
        ).label('rnk')
    ).subquery()

    images_subquery = db.session.query(rank_subquery).filter(
        rank_subquery.c.rnk == 1
    ).subquery()

    submissions_raw = db.session.query(
        User.id,
        User.first_name,
        User.last_name,
        images_subquery.c.id,
        images_subquery.c.docker_image,
        images_subquery.c.created_on
    ).join(
        images_subquery, User.id == images_subquery.c.created_by_fk
    ).all()

    logging.info(f"Found %s participants", len(submissions_raw))
    user_id_to_submissions = {}
    # preprocess
    headers = ['user_id', 'first_name', 'last_name', 'submit_id', 'docker_image', 'created_on']
    for submission in submissions_raw:
        row = {k: v for k, v in zip(headers, submission)}
        user_id = row['user_id']
        prev_row = user_id_to_submissions.get(user_id, None)
        if prev_row is None or prev_row['created_on'] < row['created_on']:
            user_id_to_submissions[user_id] = row
        logging.info(f"Participant: {row}")

    logging.info("Pre competition agent test")
    PRE_START_TIMEOUT = 3
    items = list(user_id_to_submissions.items())
    for i, (user_id, submission) in enumerate(items):
        agent_image = submission['docker_image']
        submit_id = submission['submit_id']
        try:
            logging.info("Try to poll agent from %s", agent_image)
            client.images.pull(agent_image)
            db.session.query(SubmissionDockerImage) \
                .filter(SubmissionDockerImage.id == submit_id) \
                .update({'pull_status': 'Downloaded', 'changed_by_fk': 1})
            db.session.commit()
        except Exception as e:
            del user_id_to_submissions[user_id]
            logging.exception(f"Pull image '{agent_image}' error.")
            db.session.query(SubmissionDockerImage) \
                .filter(SubmissionDockerImage.id == submit_id) \
                .update({'pull_status': 'Downloading error', 'changed_by_fk': 1})
            db.session.commit()
        logging.info("Try to run agent %s and wait for status %s seconds", agent_image, PRE_START_TIMEOUT)
        container = client.containers.run(agent_image,
                                          environment={
                                              "AGENT_NAME": 'test',
                                              "SERVER_URL": 'ai_server',
                                              "SERVER_PORT": 4181,
                                              "LOG_LEVEL": "debug"
                                          },
                                          name=f'ai_agent_{i + 1}',
                                          detach=True)
        sleep(PRE_START_TIMEOUT)
        log_data = container.logs(tail=10).decode("utf-8")
        if 'ready' not in log_data:
            del user_id_to_submissions[user_id]
            logging.warning("Container %s not ready. Log: %s", agent_image, log_data)
            db.session.query(SubmissionDockerImage) \
                .filter(SubmissionDockerImage.id == submit_id) \
                .update({'pull_status': 'Wrong launch', 'changed_by_fk': 1})
            db.session.commit()
        elif container.status == 'exited':
            del user_id_to_submissions[user_id]
            logging.warning("Container %s not ready. Status: %s", agent_image, container.status)
            db.session.query(SubmissionDockerImage) \
                .filter(SubmissionDockerImage.id == submit_id) \
                .update({'pull_status': 'Exited to fast', 'changed_by_fk': 1})
            db.session.commit()
        else:
            logging.info("Container %s ready!", agent_image)
            db.session.query(SubmissionDockerImage) \
                .filter(SubmissionDockerImage.id == submit_id) \
                .update({'pull_status': 'Ok', 'changed_by_fk': 1})
            db.session.commit()
        logging.info("Remove image %s after test ", agent_image)
        container.remove(force=True)

    if len(user_id_to_submissions) < 2:
        logging.info('Not enough submissions for round')
        return

    logging.info('Run server container')
    server_container = client.containers.run('ai_server',
                                             environment={
                                                 "SERVER_URL": "*",
                                                 "SERVER_PORT": 4181,
                                                 "TOTAL_OFFER": 100,
                                                 "TOTAL_ROUNDS": 100,
                                                 "CLIENTS_AMOUNT": len(user_id_to_submissions),
                                                 "RESPONSE_TIMEOUT": 5,
                                                 "LOG_LEVEL": "debug"
                                             },
                                             name='ai_server',
                                             ports={'4181/tcp': 4181},
                                             detach=True)

    logging.info("Prepare agents")
    agent_containers = []
    agent_results = {}
    for i, (_, submission) in enumerate(user_id_to_submissions.items()):
        name = f"{i}_{submission['first_name']}.{submission['last_name']}"
        agent_results[name] = {'submission': submission}
        agent_image = submission['docker_image']
        logging.info('Run agent container %s for %s', agent_image, name)
        container = client.containers.run(agent_image,
                                          environment={
                                              "AGENT_NAME": name,
                                              "SERVER_URL": 'ai_server',
                                              "SERVER_PORT": 4181,
                                              "LOG_LEVEL": "debug"
                                          },
                                          name=f'ai_agent_{i + 1}',
                                          links={'ai_server': 'ai_server'},
                                          detach=True)
        agent_containers.append(container)

    for c in agent_containers:
        if c.status == 'exited':
            logging.warning("Found exited container %s", c)

    def find_data_in_log(container) -> Optional[str]:
        PATTERN = 'ROUND_JSON_DATA:'
        log_data = container.logs(tail=10).decode("utf-8")
        logging.debug(f"Server container last log data %s", log_data)
        for line in log_data.split('\n'):
            if PATTERN in line:
                split_result = line.split(PATTERN)
                if len(split_result) > 1:
                    return split_result[1].strip()
        return None

    GET_RESULT_TIMEOUT = 60 * 15  # 15 minutes
    start = time.time()
    logging.info("Waiting result from containers. Time limit: %s seconds", GET_RESULT_TIMEOUT)
    while True:
        sleep(1)
        check_time = time.time()
        str_data = find_data_in_log(server_container)
        if str_data:

            data = json.loads(str_data)
            for row in data['data']:
                inner_agent_name = row['Agent']
                score = row['Score']
                submission = agent_results[inner_agent_name]['submission']
                submit_id = submission['submit_id']
                name = f"{submission['first_name']}.{submission['last_name']}"
                row['Agent'] = name
                # save submission result
                db.session.query(SubmissionDockerImage) \
                    .filter(SubmissionDockerImage.id == submit_id) \
                    .update({'last_score': f'score:{score}',
                             'last_competition': competition_time,
                             'changed_by_fk': 1})
                logging.info(f"Individual competition data successfully added for. {name}")

            db.session.add(CompetitionRound(data=json.dumps(data), created_on=competition_time))
            db.session.commit()
            logging.info(f"Competition round data successfully added. {str_data}")
            break
        elif check_time > start + GET_RESULT_TIMEOUT:
            logging.error("Get result timed out")
            break

    # cleanup
    server_container.remove(force=True)
    logging.info(f"Cleanup containers")
    for c in agent_containers:
        c.remove(force=True)
    logging.info(f"Round successfully finished")


def run_background_scheduler():
    scheduler = BlockingScheduler()
    logging.info("Run competition on start")
    run_competition()
    logging.info("Schedule competitions")
    scheduler.add_job(run_competition, 'interval', minutes=5)
    scheduler.start()


thread = Thread(target=run_background_scheduler)
thread.start()
