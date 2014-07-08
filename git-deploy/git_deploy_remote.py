# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Adam Schubert"
__date__ ="$6.7.2014 0:22:44$"

import time
import os
import git_deploy
from classes import Git
from classes import Shell

class GitDeployRemote:
  ssh_path = None
  branch = None
  lock_file = 'deploy.lck'
  current_revision = None
  tmp = None
  git = None

  """
   * Constructor
   * @param string $stdin STDIN
  """
  def __init__(self, current, branch, ssh_path, tmp_path):
    
    #Build needed info
    self.ssh_path = ssh_path
    print(Shell.color('Path to repository is: ' + self.ssh_path, 'white', 'black'))
    #Parse stdin

    self.current_revision = current
    self.branch = branch.split('/')[-1]

    #Separate tmp repos per branch
    parsed_path = Git.git_url_parse(ssh_path)
    self.tmp = os.path.join(tmp_path, parsed_path['hostname'], parsed_path['path'], self.branch)
    self.git = Git(self.tmp)
    try:
      self.running_job()
      self.sync()
      self.deploy()
    except Exception as e:
      print(Shell.color(str(e), 'white', 'red'))

  """
   * Method checks if there is running job for branch, if is it will sleep till another job ends
  """
  def running_job(self):
    wait_time = 10#s
    while self.check_work() == True:
      print(Shell.color('Another deploy job is running, waiting {} s to try again...'.format(wait_time), 'yellow', 'black'))
      time.sleep(wait_time)

  """
   * Method checks if there is unfinished job
   * @return boolean
  """
  def check_work(self):
    lock_file_path = os.path.join(self.tmp, self.lock_file)
    if os.path.isfile(lock_file_path):
      #Lock file is less then one hour old... let it be and wait till expire or get removed by finished job
      if os.path.getctime(lock_file_path) + 3600 > int(time.time()):
        return True
    return False

  """
   * Method sync local TMP with main repo
  """
  def sync(self):
    self.git.update(self.branch, self.ssh_path)

    #Create own lock file and continue
    f = open(os.path.join(self.tmp, self.lock_file), 'w')
    f.write(self.current_revision)
    f.close()

  """
   * Method calls local deployer
   * @throws Exception
  """
  def deploy(self):
    git_deploy.GitDeploy(self.tmp)
    self.destroy_lock()

  """
   * Method destroys lock file
  """
  def destroy_lock(self):
    lock_file_path = os.path.join(self.tmp, self.lock_file)
    if self.lock_file and os.path.isfile(lock_file_path):
      os.unlink(lock_file_path);

  """
   * Desctructort
  """
  def __del__(self):
    self.destroy_lock()
  
  
