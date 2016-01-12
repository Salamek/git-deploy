"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

__author__ = "Adam Schubert"
__date__ = "$6.7.2014 0:22:44$"

import sys
import os
import json
import git_deploy_remote
from flask import Flask, request, jsonify, render_template, send_file, Response, flash, abort
from flask.ext.scss import Scss
from raven.contrib.flask import Sentry
from database import db, Repository, Deploy, Commit, Namespace, Server, Branch
from sqlalchemy.sql import func
import datetime
import hashlib


class GitDeployServer:

    def __init__(self, config):
        tmp = config['hook']['tmp_path'],
        file_log = config['server']['file_log']
        app = Flask(__name__)

        # git-deploy config to Flask config
        app.config['DEBUG'] = config['server']['debug']
        app.config['SERVER_NAME'] = 'localhost:{}'.format(config['server']['port'])
        app.config['SQLALCHEMY_DATABASE_URI'] = config['server']['database_uri']
        app.config['SECRET_KEY'] = 'some_super_secret_random_key_'
        # app.config['SQLALCHEMY_ECHO'] = True
        # Init flask extensions
        db.init_app(app)
        Scss(app)

        with app.app_context():
            db.create_all()
            db.session.commit()

        if not app.debug and file_log != None:
            import logging
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(file_log)
            file_handler.setLevel(logging.WARNING)
            app.logger.addHandler(file_handler)

        # Filters
        @app.template_filter('cut_sha')
        def cut_sha_filter(sha):
            return sha[:6]

        @app.template_filter('datetime_add')
        def datetime_add_filter(date, secons_add):
            return date + datetime.timedelta(0, secons_add)

        @app.template_filter('format_since')
        def format_since_filter(date):
            now = datetime.datetime.now()
            since_seconds = int((now - date).total_seconds())
            m, s = divmod(since_seconds, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)
            mo, d = divmod(d, 30)  # ~

            number = 0
            string = 'second'
            if mo:
                number = mo
                string = 'month'
            elif d:
                number = d
                string = 'day'
            elif h:
                number = h
                string = 'hour'
            elif m:
                number = m
                string = 'minute'
            elif s:
                number = s
                string = 'second'

            if number != 1:
                string += 's'

            return 'about {} {} ago'.format(number, string)

        @app.template_filter('format_seconds')
        def format_seconds_filter(seconds):
            m, s = divmod(seconds, 60)
            h, m = divmod(m, 60)
            d, h = divmod(h, 24)

            string = ['{} sec']
            string_format = [s]
            if m:
                string.insert(0, '{} min')
                string_format.insert(0, m)

            if h:
                string.insert(0, '{} hour')
                string_format.insert(0, h)

            if d:
                string.insert(0, '{} day')
                string_format.insert(0, d)
            return ' '.join(string).format(* string_format)

        @app.template_filter('gravatar')
        def gravatar_filter(email, size=40):
            return 'https://www.gravatar.com/avatar/{}?s={}&d=retro'.format(hashlib.md5(email.lower()).hexdigest(), size)

        @app.template_filter('format_status')
        def format_status_filter(status):
            statuses = {}
            statuses['ERROR'] = 'failed'
            statuses['OK'] = 'passed'
            statuses['WARNING'] = 'passed with warnings'
            statuses['UNKNOWN'] = 'status is unknown'
            statuses['RUNNING'] = 'deploy is running'
            return statuses[status]

        # Pages
        @app.errorhandler(404)
        def not_found(error):
            #return jsonify({'message': str(error)}), 404
            return render_template("404.html", message=str(error)), 404

        @app.route('/<string:server>')
        def namespace_list(server):
            server = db.session.query(Server).filter(Server.name == server).first()
            return render_template("namespace.html", server=server)

        @app.route('/<string:server>/<string:namespace>')
        def project_list(server, namespace):
            namespace = db.session.query(Namespace).join(Repository).join(
                Server).filter(Server.name == server, Namespace.name == namespace).first()
            if namespace is None or namespace.repository is None:
                flash('No repositories found for this namespace', 'warning')
            return render_template("repository.html", namespace=namespace)

        @app.route('/', defaults={'server': None, 'namespace': None, 'repository': None, 'commit': None}, methods=['GET'])
        @app.route('/<string:server>/<string:namespace>/<string:repository>', defaults={'commit': None}, methods=['GET'])
        @app.route('/<string:server>/<string:namespace>/<string:repository>/deploy/<string:commit>', methods=['GET'])
        def index(server, namespace, repository, commit):

            latest_commit_repository = db.session.query(Commit).join(
                Branch).join(Repository).join(Deploy).group_by(Repository.id).order_by(Commit.created.desc())

            query_filter = []
            if server and namespace and repository:
                query_filter.append(Server.name == server)
                query_filter.append(Namespace.name == namespace)
                query_filter.append(Repository.name == repository)
                if commit:
                    query_filter.append(Commit.sha == commit)
                else:
                    # Commit not set lets find last one and use that
                    last_commit = db.session.query(Commit).join(
                        Branch).join(Repository).join(Deploy).filter(* query_filter).order_by(Commit.created.desc()).first()
                    if last_commit:
                        query_filter.append(Commit.sha == last_commit.sha)
            else:
                # nothing set lest use latestcommit
                first_last_commit_repository = latest_commit_repository.first()
                query_filter.append(
                    Server.id == first_last_commit_repository.branch.repository.namespace.server.id)
                query_filter.append(
                    Namespace.id == first_last_commit_repository.branch.repository.namespace.id)
                query_filter.append(
                    Repository.id == first_last_commit_repository.branch.repository.id)
                query_filter.append(Commit.id == first_last_commit_repository.id)

            result = db.session.query(Commit, func.sum(Deploy.runtime).label("total_runtime")).join(
                Branch).join(Repository).join(Deploy).filter(* query_filter).group_by(Repository.id).order_by(Commit.created.desc()).first()

            if result is None:
                 abort(404)

            first_last_commit, total_runtime = result

            branches = db.session.query(
                Branch).join(Repository).join(Namespace).join(Server).filter(Server.id == first_last_commit.branch.repository.namespace.server.id,
                                                                             Namespace.id == first_last_commit.branch.repository.namespace.id, Repository.id == first_last_commit.branch.repository.id).order_by(Branch.updated.desc())
            commits = db.session.query(
                Commit).join(Branch).join(Repository).join(Namespace).join(Server).filter(Server.id == first_last_commit.branch.repository.namespace.server.id,
                                                                                          Namespace.id == first_last_commit.branch.repository.namespace.id, Repository.id == first_last_commit.branch.repository.id, Commit.id != first_last_commit.id).order_by(Commit.created.desc())

            return render_template("index.html", latest_commit_repository=latest_commit_repository, commit=first_last_commit, total_runtime=total_runtime, branches=branches, commits=commits)

        @app.route("/<string:server>/<string:namespace>/<string:repository>.svg")
        def deploy_status(server, namespace, repository):
            found = db.session.query(Repository).join(Namespace).join(Server).filter(
                Server.name == server, Namespace.name == namespace, Repository.name == repository).first()

            found = db.session.query(Commit).join(Branch).join(Repository).join(Namespace).join(Server).filter(
                Server.name == server, Namespace.name == namespace, Repository.name == repository).order_by(Commit.created.desc()).first()

            my_path = os.path.dirname(os.path.realpath(__file__))
            image = open(
                os.path.join(my_path, 'assets/images/{}.svg'.format(found.status.lower()))).read()
            return Response(image, mimetype='image/svg+xml')

        @app.route("/deploy.json", methods=['POST', 'GET'])
        def deploy():
            if request.json == None:
                return jsonify({'message': 'I eat only JSON... bark, bark!'}), 400

            try:
                git_deploy_remote.GitDeployRemote(
                    request.json['after'], request.json['ref'], request.json['repository']['url'], tmp)
                return jsonify({'message': 'ok'}), 200
            except Exception as e:
                return jsonify({'message': str(e)}), 500

        app.run()
