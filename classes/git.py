# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Adam Schubert"
__date__ ="$5.7.2014 23:58:01$"

import subprocess
import os

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

