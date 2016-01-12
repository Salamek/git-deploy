from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func


db = SQLAlchemy()

class BaseTable(db.Model):
  __abstract__ = True
  updated = db.Column(db.DateTime, default=func.now(), onupdate=func.current_timestamp())
  created = db.Column(db.DateTime, default=func.now())


# Server -> Namespace -> Repository -> Branch -> Commit -> Deploy -> Log

class Server(BaseTable):
  __tablename__ = 'server'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  namespace = relationship("Namespace", order_by="Namespace.id", backref="server")

class Namespace(BaseTable):
  __tablename__ = 'namespace'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  server_id = db.Column(db.Integer, db.ForeignKey('server.id'))
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  repository = relationship("Repository", order_by="Repository.id", backref="namespace")

class Repository(BaseTable):
  __tablename__ = 'repository'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  namespace_id = db.Column(db.Integer, db.ForeignKey('namespace.id'))
  branch = relationship("Branch", order_by="Branch.updated.desc()", backref="repository")

class Branch(BaseTable):
  __tablename__ = 'branch'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  repository_id = db.Column(db.Integer, db.ForeignKey('repository.id'))
  commit = relationship("Commit", order_by="Commit.created.desc()", backref="branch")

class Commit(BaseTable):
  __tablename__ = 'commit'
  id = db.Column(db.Integer, primary_key=True)
  sha = db.Column(db.String(40))
  name = db.Column(db.String(255))
  description = db.Column(db.String(1024))
  status = db.Column(db.Enum('ERROR', 'WARNING', 'OK', 'UNKNOWN', 'RUNNING', name='commit_status_type'))
  runtime = db.Column(db.Integer)
  branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'))
  user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
  deploy = relationship("Deploy", order_by="Deploy.id", backref="commit")

class Deploy(BaseTable):
  __tablename__ = 'deploy'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String(255))
  uri = db.Column(db.String(1024))
  status = db.Column(db.Enum('ERROR', 'WARNING', 'OK', 'UNKNOWN', 'RUNNING', name='deploy_status_type'))
  runtime = db.Column(db.Integer)
  commit_id = db.Column(db.Integer, db.ForeignKey('commit.id'))
  log = relationship("Log", order_by="Log.id", backref="deploy")

class Log(BaseTable):
  __tablename__ = 'log'
  id = db.Column(db.Integer, primary_key=True)
  data = db.Column(db.String(1024))
  status = db.Column(db.Enum('ERROR', 'WARNING', 'OK', 'UNKNOWN', name='log_status_type'))
  deploy_id = db.Column(db.Integer, db.ForeignKey('deploy.id'))

class User(BaseTable):
  __tablename__ = 'user'
  id = db.Column(db.Integer, primary_key=True)
  first_name = db.Column(db.String(255))
  last_name = db.Column(db.String(255))
  email = db.Column(db.String(255))
  password = db.Column(db.String(255))
  commit = relationship("Commit", order_by="Commit.id", backref="user")
  namespace = relationship("Namespace", order_by="Namespace.id", backref="user")
