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

if __name__ == "__main__":
  if sys.argv[1] == 'server':
    git_deploy_server.GitDeployServer()
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
      repository_path = os.path.join('/home/', git_user, '/repositories/') #FIXME GET REPO PATH FROM CONFIG

      #Build needed info
      ssh_path = git_user + '@' + socket.gethostname() + ':' + os.getcwd().replace(repository_path,'')
      git_deploy_remote.GitDeployRemote(current, branch, ssh_path, tmp_path) #FIXME TMP PATH GET FROM CONFIG
  
  
