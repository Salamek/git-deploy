# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="sadam"
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
  
  
