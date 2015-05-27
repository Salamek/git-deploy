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

__author__="Adam Schubert"
__date__ ="$6.7.2014 2:01:34$"


import os
import ConfigParser
import urlparse
import config_reader

from classes import Git
from classes import Ftp
from classes import Ftps
from classes import Ssh
from classes import Log

class GitDeploy:
  
  root = None
  log = None
  current_revision = None
  git = None
  config_file_search = ['deploy.py', 'deploy.ini']
  config_file = None
  config = {}
  revison_file = 'REVISION'
  lock_file = 'deploy.lck'
  
  def __init__(self, config = None):
    self.log = Log()
    self.currentRevision = None
    root = None
    
    if config :
      if os.path.isdir(config):
        root = config
      else:
        raise Exception(config + ' is not a directory or dont exists!')
    else:
      root = None

    try:
      self.git = Git(root);
      self.root = self.git.root
      try:
        self.parse_config()
        if self.config['deploy']['deploy'] == True:
          self.deploy()
      except Exception as e:
        raise e
    except Exception as e:
      raise e
  
  
  
  def parse_config(self):
    
    for conf_file in self.config_file_search:
      config_file_path = os.path.join(self.root, conf_file)
      if os.path.isfile(config_file_path):
        break
    
    config = config_reader.configReader(config_file_path)
    if config_file_path.find('.py') == -1:
      config.migrate_ini2py()
    
    self.config = config.get()
      
      
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
      
      #create lock file on remote server
      try:
        connection.upload_string(os.path.join(self.config['uri'].path, self.lock_file), git_revision_log)
      except Exception as err:
        self.log.add(str(err), 'error')
        
      if revision and git_revision:
        self.log.add('Remote revision is {}, current revison is {}'.format(revision, git_revision), 'ok')
      else:
        self.log.add('No remote revision found, deploying whole project {}'.format(git_revision_log), 'ok')

      files = self.git.diff_commited(revision);

      
      for upload in files['upload']:
        if upload.endswith(self.config_file) == False:
          try:
            premisson = self.check_premisson(upload)
            connection.upload_file(os.path.join(self.root, upload), os.path.join(self.config['uri'].path, upload), premisson)
            self.log.add('++ Deploying file ' + self.config['uri'].path + '/' + upload, 'ok')
          except Exception as e:
            self.log.add(str(e), 'error')


      for delete in files['delete']:
        try:
          connection.delete_file(os.path.join(self.config['uri'].path, delete))
          self.log.add('++ Deleting file ' + self.config['uri'].path + '/' + delete, 'ok')
        except Exception as e:
          self.log.add(str(e), 'error')

      try:
        #destroy lock file
        connection.delete_file(os.path.join(self.config['uri'].path, self.lock_file))
      except Exception as e:
        load.add(str(e), 'error')
        
      try:
        #create revision file
        connection.upload_string(os.path.join(self.config['uri'].path, self.revison_file), git_revision_log)
      except Exception as e:
        self.log.add(str(e), 'error')
        
      self.log.add('Deploy done!', 'ok')
    else:
      self.log.add('Revisions match, no deploy needed.', 'ok')
      
  def check_premisson(self, filename):
    for path, premisson in self.config['deploy']['file_rights']:
      if filename.endswith(path) or path == '*' or '*' in path and filename.startswith(path.replace('*', '')):
        return int(premisson)
    return None
  
  def get_log(self):
    return self.log
