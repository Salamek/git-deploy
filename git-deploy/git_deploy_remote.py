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
__date__ ="$6.7.2014 0:22:44$"

import os
import git_deploy
import threading
from classes import Git
from classes import Shell

class DeployWorker(threading.Thread):
  caller = None
  def __init__(self, caller):
    super(DeployWorker, self).__init__()
    self.caller = caller
    
  work_list = []
  def run(self):
    while(len(self.work_list) > 0):
      current, branch, ssh_path, tmp = self.work_list.pop()
      try:
        self.sync(tmp, branch, ssh_path)
        self.caller.loger(self.deploy(tmp))
      except Exception as e:
        self.caller.fail(str(e))
        
  
  def add_work(self, work):
    self.work_list.append(work)
    
  """
   * Method sync local TMP with main repo
  """
  def sync(self, tmp, branch, ssh_path):
    git = Git(tmp)
    git.update(branch, ssh_path)
    
  """
   * Method calls local deployer
   * @throws Exception
  """
  def deploy(self, tmp):
    return git_deploy.GitDeploy(tmp).get_log()




class GitDeployRemote:
  
  workers = {}
  
  """
   * Constructor
   * @param string $stdin STDIN
  """
  def __init__(self, current, branch, ssh_path, tmp_path):
    branch = branch.split('/')[-1]

    #Separate tmp repos per branch
    parsed_path = Git.git_url_parse(ssh_path)
    tmp = os.path.join(tmp_path, parsed_path['hostname'], parsed_path['path'], branch)
    
    
    #tmp is uniqe identifier of repo, this creates front for each repo
    if tmp in self.workers:
      w = self.workers[tmp]
      if w.isAlive():
        w.add_work([current, branch, ssh_path, tmp])
      else:
        self.workers[tmp] = DeployWorker(self)
        self.workers[tmp].add_work([current, branch, ssh_path, tmp])
        self.workers[tmp].start()
    else:
      self.workers[tmp] = DeployWorker(self)
      self.workers[tmp].add_work([current, branch, ssh_path, tmp])
      self.workers[tmp].start()
      
    #clean not running workers
    for tmp in self.workers:
      if self.workers[tmp].isAlive() == False:
        del self.workers[tmp]

  def loger(self, l):
    l.output()

  def fail(self, fail):
    Shell.color(fail, 'white', 'red')