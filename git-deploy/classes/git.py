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
__date__ ="$5.7.2014 23:58:01$"

import subprocess
import os
import re

class Git:
  
  root = None
  
  """
   * Constructor, checks existence of git bin
   * @throws Exception
  """
  def __init__(self, root = None):
    if self.is_git() == False:
      raise Exception('Git not found! Please use package manager to install it')
    if root:
      self.root = root
    else:
      self.root = self.get_git_root()
    
  """
   * Method checks if git is installed and runnable
   * @return boolean
  """
  def is_git(self):
    try:
      null = open("/dev/null", "w")
      subprocess.Popen("git", stdout=null, stderr=null)
      null.close()
      return True
    except OSError:
      return False
    
  """
   * Method sets current repo branch
   * @param string $branch
  """
  def set_branch(self, branch):
    os.system('unset GIT_DIR && cd ' + self.root + ' && git checkout ' + branch)

  """
   * Method checks if specified directory is git client repo
   * @param string $dir
   * @return boolean
  """
  def has_git(self, dir):
    return os.path.isdir(os.path.join(dir, '.git'))

  """
   * Method returns current revision
   * @return string
  """
  def get_revision(self):
    proc = subprocess.Popen(['unset GIT_DIR && cd ' + self.root + ' && git rev-parse HEAD'], stdout=subprocess.PIPE, shell=True)
    output, err = proc.communicate()
    return output.strip()

  """
   * Method returns list of uncommited files
   * @return array
  """
  def diff_uncommitted(self):
    data = []
    os.system('unset GIT_DIR && cd ' + self.root + ' && git diff --name-status', data)
    os.system('unset GIT_DIR && cd ' + self.root + ' && git diff --cached --name-status', data)
    return self.git_parse_files(data)

  """
   * Method resturns list of Commited files, in specified revision if any
   * @param string $revision
   * @return array
  """
  def diff_commited(self, revision = None):
    files = []

    if revision:
      proc = subprocess.Popen(['unset GIT_DIR && cd ' + self.root + ' && git diff --name-status ' + revision],stdout=subprocess.PIPE, shell=True)
      while True:
        line = proc.stdout.readline()
        if line != '':
          files.append(line.strip())
        else:
          break
    
    else:
      data = []
      proc = subprocess.Popen(['unset GIT_DIR && cd ' + self.root + ' && git ls-files ' + self.root + '  --full-name'],stdout=subprocess.PIPE, shell=True)
      while True:
        line = proc.stdout.readline()
        if line != '':
          data.append(line.strip())
        else:
          break

      for line in data:
        files.append('M	' + line)
        
    return self.git_parse_files(files)

  """
   * Method sets and return git root
   * @param string $root set absolute fixed git root (usefull when we running deploy form nongit path)
   * @return string path to repo
  """
  def get_git_root(self):
    proc = subprocess.Popen(['git rev-parse --show-toplevel'], stdout=subprocess.PIPE, shell=True)
    root, err = proc.communicate()
    self.root = root.strip()
    return self.root

  """
   * Method parses git filelist output and builds array from it
   * @param string $data
   * @return array
  """
  def git_parse_files(self, data):
    ignore = ['.gitignore']
    ret = {'upload': [], 'delete': []}
    if len(data):
      for line in data:
        if line:
          action, filename = line.strip().split('	')

          if os.path.basename(filename) not in ignore:
            if action in ['A', 'M', 'C']:
              ret['upload'].append(filename)
            elif action in ['D']:
              ret['delete'].append(filename);
    return ret
  
  @staticmethod
  def git_url_parse(url):
    if re.match(r'((git|ssh|http(s)?)|(git@[\w.]+))(:(//)?)([\w.@\:/-~]+)(.git)(/)?', url):
      ret = {}
      
      netloc, path = url.split(':')
      user, hostname = netloc.split('@')
      ret['path'] = path
      ret['user'] = user
      ret['hostname'] = hostname
      return ret
    else:
      return None
    
  def update(self, branch, ssh_path):
    if os.path.isdir(self.root):
      os.system('unset GIT_DIR && cd ' + self.root + ' && git pull')
    else:
      os.system('git clone -b ' + branch + ' ' + ssh_path + ' ' + self.root)
      

