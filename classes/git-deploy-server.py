# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Adam Schubert"
__date__ ="$6.7.2014 0:22:44$"

import time
import socket
import fileinput
import getpass

class GitDeployServer:
  
  """
   * Domain where git server is running, fill in only when running with "unknow git server"
   * @var string
  """
  git_host = None

  """
   * Path to git repositories, fill in only when running with "unknow git server"
   * @var string
  """
  repository_path = None

  """
   * User under with git is running, default is git, fill in only when running with "unknow git server" or under nonstandard user
   * @var string
  """
  git_user = 'git'

  """
   * Specifies name of TMP dir, its created in server repo root
   * @var string
  """
  tmp_dir = 'deploy_tmp'
  self_path = None;
  ssh_path = None;
  stdin = None;
  previous_revision = None;
  branch = None;
  lock_file = 'deploy.lck'
  current_revision = None;
  tmp = None;

  """
   * Constructor
   * @param string $stdin STDIN
  """
  def __init__(self, stdin = None):
    if stdin:
      self.stdin = stdin
    else:
      self.stdin = fileinput.input()[0].strip().split(' ')

    self.self_path = os.getcwd()
    self.git_user = getpass.getuser()
    self.git_host = socket.gethostname()
    self.repository_path = os.path.join('/home/', self.git_user, '/repositories/')

    #Build needed info
    self.ssh_path = sef.git_user + '@' + self.git_host + ':' + self.self_path.replace(self.repository_path,'')
    print(Shell.color('Path to repository is: ' . self.ssh_path, 'white', 'black'))
    #Parse stdin
    prev, current, branch = self.stdin
    self.previous_revision = prev
    self.current_revision = current
    self.branch = branch.split('/')[-1]

    #Separate tmp repos per branch
    self.tmp_dir = os.path.join(self.tmp_dir, self.branch)

    self.tmp = os.path.join(self.self_path, self.tmp_dir)

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
    if os.path.isdir(self.tmp):
      os.system('unset GIT_DIR && cd ' + self.tmp + ' && git pull')
    else:
      os.system('git clone -b ' + self.branch + ' ' + self.ssh_path + ' ' + self.tmp)

    #Create own lock file and continue
    f = open(os.path.join(self.tmp, self.lock_file), 'w')
    f.write(self.current_revision)
    f.close()

  """
   * Method calls local deployer
   * @throws Exception
  """
  def deploy(self):
    GitDeploy(self.tmp)
    self.destroy_lock()

  """
   * Method destroys lock file
  """
  def destroy_lock(self):
    lock_file_path = os.path.join(self.tmp, self.lock_file),;
    if self.lock_file and os.path.isfile(lock_file_path):
      os.unlink(lock_file_path);

  """
   * Desctructort
  """
  def __del__(self):
    self.destroy_lock()
  
  
