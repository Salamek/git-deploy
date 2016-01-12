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
import config_reader

def load_config():
  config_file_path_search = ['/etc/git-deploy/config.py', '/etc/git-deploy/git-deploy.cfg']
  config_file_path = None
  for conf_file in config_file_path_search:
      if os.path.isfile(conf_file):
        config_file_path = conf_file
        break

  if config_file_path is None:
    raise Exception('Git deploy config file not found in [{}]'.format(' or '.join(config_file_path_search)))

  config = config_reader.configReader(config_file_path)
  if config_file_path.find('.py') == -1:
    config.migrate_ini2py()
    os.rename(config_file_path, config_file_path + '.old')

  return config.get()


def set_user(username):
  #set user to run under
  try:
    id = pwd.getpwnam(username)
  except KeyError:
    raise Exception('User "{}" not found'.format(username))

  os.environ['HOME']  = id.pw_dir
  os.environ['LOGNAME']  = id.pw_name
  os.environ['USER']  = id.pw_name

  os.setgid(id.pw_gid)
  os.setuid(id.pw_uid)


def main():
  config = load_config()
  if len(sys.argv) == 2 and sys.argv[1] == 'server':
    set_user(config['server']['user'])

    git_deploy_server.GitDeployServer(config)
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

      set_user(config['server']['user'])

      prev, current, branch = stdin
      git_user = getpass.getuser()
      repository_path = os.path.join(config['hook']['repository_path'])

      #Build needed info
      ssh_path = git_user + '@' + socket.gethostname() + ':' + os.getcwd().replace(repository_path,'')
      git_deploy_remote.GitDeployRemote(current, branch, ssh_path, config)
