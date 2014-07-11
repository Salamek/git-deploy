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

import git_deploy
import git_deploy_remote
import git_deploy_server
import sys
import socket
import fileinput
import getpass
import os
import pwd
import ConfigParser

def load_config():
  config_file_path = '/etc/git-deploy/git-deploy.cfg'
  if os.path.isfile(config_file_path):
    config = ConfigParser.ConfigParser()
    try:
      config.read(config_file_path)
      
      ret = {'server': {}, 'hook': {}}
      if config.has_option('server', 'port'):
        ret['server']['port'] = config.getint('server', 'port')
      else:
        ret['server']['port'] = 7416
        
      if config.has_option('server', 'file_log'):
        ret['server']['file_log'] = config.get('server', 'file_log')
      else:
        ret['server']['file_log'] = '/var/log/git-deploy.log'
        
      if config.has_option('server', 'user'):
        ret['server']['user'] = config.get'server', 'user')
      else:
        ret['server']['user'] = 'root'
        
      if config.has_option('hook', 'repository_path'):
        ret['hook']['repository_path'] = config.get('hook', 'repository_path')
      else:
        ret['hook']['repository_path'] = '/home/git/repositories'
        
      if config.has_option('hook', 'tmp_path'):
        ret['hook']['tmp_path'] = config.get('hook', 'tmp_path')
      else:
        ret['hook']['tmp_path'] = '/home/git/tmp'
      
      return ret
    except IOError:
      raise Exception('Failed to parse ' + config_file_path);
  else:
    raise Exception('Config file {} not found '.format(config_file_path))


def main():
  config = load_config()
  
  #set user to run under
  uid = pwd.getpwnam(ret['server']['user'])[2]
  os.setuid(uid)
  
  if len(sys.argv) == 2 and sys.argv[1] == 'server':
    git_deploy_server.GitDeployServer(config['server']['port'], config['hook']['tmp_path'], config['server']['file_log'])
  elif len(sys.argv) == 1:
    #one arg means local run
    git_deploy.GitDeploy().get_log().output()
  elif len(sys.argv) == 2:
    #two args means local run
    git_deploy.GitDeploy(sys.argv[1]).get_log().output()
  else:
    stdin = fileinput.input()[0].strip().split(' ')
    #stdin 3 items thats post-receive
    if len(stdin) == 3:
      prev, current, branch = stdin
      git_user = getpass.getuser()
      repository_path = os.path.join(config['hook']['repository_path'])

      #Build needed info
      ssh_path = git_user + '@' + socket.gethostname() + ':' + os.getcwd().replace(repository_path,'')
      git_deploy_remote.GitDeployRemote(current, branch, ssh_path, config['hook']['tmp_path'])
  
  
