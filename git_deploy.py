#!/usr/bin/env python2

import os
import ConfigParser
import re
import smtplib
import urlparse
import socket

from classes import Git
from classes import Ftp
from classes import Ftps
from classes import Ssh
from classes import Git
from classes import Shell

class GitDeploy:
  
  root = None
  current_revision = None
  git = None
  config_file = 'deploy.ini'
  config = {}
  revison_file = 'REVISION'
  
  def __init__(self, config = None):
    self.currentRevision = None
    root = None
    
    if isinstance(config, str):
      if os.path.isdir(config):
        root = config
      else:
        raise Exception(config + ' is not a directory or dont exists!')

    try:
      self.git = Git(root);
      self.root = self.git.root
      try:
        self.parse_config()
        if self.config['deploy']['deploy'] == True:
          self.deploy()
      except Exception as e:
        raise e
        print(Shell.color(str(e), 'white', 'red'))
    except Exception as e:
      raise e
      print(Shell.color(str(e), 'white', 'red'))
  
  
  def parse_config(self):
    config_file_path = os.path.join(self.root, self.config_file)

    if os.path.isfile(config_file_path):
      config = ConfigParser.ConfigParser()
      try:
        config.read(config_file_path)

        #parse config and set it into variable
        self.config['deploy'] = {}
        self.config['deploy']['target'] = config.get('deploy', 'target')
        self.config['deploy']['deploy'] = config.getboolean('deploy', 'deploy')
        self.config['deploy']['maintainer'] = config.get('deploy', 'maintainer')
        self.config['deploy']['file_rights'] = config.items('file_rights')

        self.config['uri'] = urlparse.urlparse(self.config['deploy']['target'].strip("'"))

        if self.config['uri'] == None or self.config['uri'].hostname == None:
          raise Exception('Failed to prase URI in config file')
      except IOError:
        raise Exception('Failed to parse ' + config_file_path);
    else:
      raise Exception(config_file_path + ' not found!, skiping deploy...')
      
      
  def deploy(self):
    connection = None
    if self.config['uri'].password:
      password = self.config['uri'].password
    else:
      password = None
      
    if self.config['uri'].scheme == 'sftp':
      if self.config['uri'].port:
        port = self.config['uri'].port
      else:
        port = 22
      connection = Ssh(self.config['uri'].hostname, self.config['uri'].username, self.config['uri'].path, port, password)

    elif self.config['uri'].scheme == 'ftp':
      if self.config['uri'].port:
        port = self.config['uri'].port
      else:
        port = 21
      connection = Ftp(self.config['uri'].hostname, self.config['uri'].username, self.config['uri'].path, port, password)

    elif self.config['uri'].scheme == 'ftps':
      if self.config['uri'].port:
        port = self.config['uri'].port
      else:
        port = 21
      connection = Ftps(self.config['uri'].hostname, self.config['uri'].username, self.config['uri'].path, port, password)


    git_revision = None;
    git_revision_log = None;
    try:
      if self.current_revision:
        git_revision = git_revision_log = self.current_revision
      else:
        git_revision = git_revision_log = self.git.get_revision()
    except Exception as e:
      git_revision = None;

    try:
      revision = connection.read_file(os.path.join(self.config['uri'].path, self.revison_file).strip())
    except Exception as e:
      revision = None;

    #Revision not match, we must get changes and upload it on server
    if git_revision != revision:
      if revision and git_revision:
        text = 'Remote revision is {}, current revison is {}'.format(revision, git_revision)
        print(Shell.color(text, 'green', 'black'))
      else:
        text = 'No remote revision found, deploying whole project {}'.format(git_revision_log)
        print(Shell.color(text, 'green', 'black'))

      files = self.git.diff_commited(revision);

      errors = []
      for upload in files['upload']:
        if upload.endswith(self.config_file) == False:
          try:
            premisson = self.check_premisson(upload)
            connection.upload_file(os.path.join(self.root, upload), os.path.join(self.config['uri'].path, upload), premisson)
            print(Shell.color('++ Deploying file ' + self.config['uri'].path + '/' + upload, 'green', 'black'))
          except Exception as e:
            errors.append(str(e))


      for delete in files['delete']:
        try:
          connection.delete_file(os.path.join(self.config['uri'].path, delete))
          print(Shell.color('++ Deleting file ' + self.config['uri'].path + '/' + delete, 'green', 'black'))
        except Exception as e:
          errors.append(str(e))

      connection.upload_string(os.path.join(self.config['uri'].path, self.revison_file), git_revision_log);

      if len(errors):
        for error in errors:
          print(Shell.color(error, 'white', 'red'))

	
        if self.config['deploy']['maintainer']:
          if re.match(r"[^@]+@[^@]+\.[^@]+", self.config['deploy']['maintainer']):
            msg = '{} errors occurred while deploying project {}'.format(len(errors), self.config['uri'].hostname)
            try:
              server = smtplib.SMTP('localhost')
              server.sendmail('noreply@localhost', self.config['deploy']['maintainer'], msg)
              server.quit()
            except socket.error as e:
              print(Shell.color('Failed to send email to {} Reason {}'.format(self.config['deploy']['maintainer'], str(e)), 'white', 'red'))
          else:
            print(Shell.color('Maintainer email is set, but has wrong format!', 'white', 'red'))
            print(Shell.color('Deploying done, but some errors occurred!', 'white', 'yellow'))
      else:
        print(Shell.color('Deploying done!', 'white', 'green'))

    else:
      print(Shell.color('Revisions match, no deploy needed.', 'white', 'green'))
      
  def check_premisson(self, filename):
    for path, premisson in self.config['deploy']['file_rights']:
      if filename.endswith(path) or path == '*' or '*' in path and filename.startswith(path.replace('*', '')):
        return premisson
    return None
