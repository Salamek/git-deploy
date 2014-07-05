#!/usr/bin/env python2

import os
import ConfigParser
import re
import smtplib
import fileinput
import getpass
import socket
import time
import ftplib
import StringIO
import paramiko
import subprocess
import urlparse

class GitDeploy:
  
  root = None
  current_revision = None
  git = None
  config_file = 'deploy.ini'
  config = {}
  revison_file = 'REVISION'
  
  def __init__(self, config = None):
    self.currentRevision = None
    root = None
    
    if isinstance(config, str):
      if os.path.isdir(config):
        root = config
      else:
        raise Exception(config + ' is not a directory or dont exists!')

    #try:
    self.git = Git(root);
    self.root = self.git.root
    #  try:
    self.parse_config()
    if self.config['deploy']['deploy'] == True:
      self.deploy()
    #  except Exception as e:
    #    raise e
    #    print(Color.string(str(e), 'white', 'red'))
    #except Exception as e:
    #  raise e
    #  print(Color.string(str(e), 'white', 'red'))
  
  
  def parse_config(self):
    config_file_path = os.path.join(self.root, self.config_file)

    if os.path.isfile(config_file_path):
      config = ConfigParser.ConfigParser()
      try:
        config.read(config_file_path)

        #parse config and set it into variable
        self.config['deploy'] = {}
        self.config['deploy']['target'] = config.get('deploy', 'target')
        self.config['deploy']['deploy'] = config.getboolean('deploy', 'deploy')
        self.config['deploy']['maintainer'] = config.get('deploy', 'maintainer')
        self.config['deploy']['file_rights'] = config.items('file_rights')

        self.config['uri'] = urlparse.urlparse(self.config['deploy']['target'].strip("'"))

        if self.config['uri'] == None or self.config['uri'].hostname == None:
          raise Exception('Failed to prase URI in config file')
      except IOError:
        raise Exception('Failed to parse ' + config_file_path);
    else:
      print(Color.string(config_file_path + ' not found!, skiping deploy...', 'green', 'black'))
      
      
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
      if revision and git_revision:
        text = 'Remote revision is {}, current revison is {}'.format(revision, git_revision)
        print(Color.string(text, 'green', 'black'))
      else:
        text = 'No remote revision found, deploying whole project {}'.format(git_revision_log)
        print(Color.string(text, 'green', 'black'))

      files = self.git.diff_commited(revision);

      errors = []
      for upload in files['upload']:
        if upload.endswith(self.config_file) == False:
          try:
            premisson = self.check_premisson(upload)
            connection.upload_file(os.path.join(self.root, upload), os.path.join(self.config['uri'].path, upload), premisson)
            print(Color.string('++ Deploying file ' + self.config['uri'].path + '/' + upload, 'green', 'black'))
          except Exception as e:
            errors.append(str(e))


      for delete in files['delete']:
        try:
          connection.delete_file(os.path.join(self.config['uri'].path, delete))
          print(Color.string('++ Deleting file ' + self.config['uri'].path + '/' + delete, 'green', 'black'))
        except Exception as e:
          errors.append(str(e))

      connection.upload_string(os.path.join(self.config['uri'].path, self.revison_file), git_revision_log);

      if len(errors):
        for error in errors:
          print(Color.string(error, 'white', 'red'))

	
        if self.config['deploy']['maintainer']:
          if not re.match(r"[^@]+@[^@]+\.[^@]+", self.config['deploy']['maintainer']):
            msg = '{} errors occurred while deploying project {}'.format(len(errors), self.config['uri'].hostname)
            server = smtplib.SMTP('localhost')
            server.sendmail('noreply@localhost', self.config['deploy']['maintainer'], msg)
            server.quit()
          else:
            print(Color.string('Maintainer email is set, but has wrong format!', 'white', 'red'))
            print(Color.string('Deploying done, but some errors occurred!', 'white', 'yellow'))
      else:
        print(Color.string('Deploying done!', 'white', 'green'))

    else:
      print(Color.string('Revisions match, no deploy needed.', 'white', 'green'))
      
  def check_premisson(self, filename):
    #FIXME
    #for item in self.config['file_rights']:
    #  if filename.endswith(k) or k == '*' or '*' in k and filename.startwith(k.replace('*', '')):
    #    return v;
    return None

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

  
class Ftp:
  connection = None
  root = None
  
  """
   * Constructor, creates connection to remote FTP server
   * @param string $host Hostname
   * @param string $user Username
   * @param string $root A ftp ROOT
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
  """
  def __init__(self, host, user, root = '/', port = 21, password = None):
    self.root = root
    
    try:
      self.connection = ftplib.FTP()
      self.connection.connect(host, port)
    except ftplib.all_errors:
      raise Exception('Failed to connect to server!')
    
    try:
      self.connection.login(user, password)
    except ftplib.all_errors:
      raise Exception('Failed to log in, incorrect password or login!')


  """
   * Destructor, close connection to ftp server
  """
  def __del__(self):
    self.connection.quit()

  """
   * Method reads file on remote FTP and returns it content (ASCII)
   * @param string $filePath path on remote server
   * @return string
  """
  def read_file(self, file_path):
    buf = StringIO.StringIO()
    self.connection.retrbinary('RETR {}'.format(file_path), buf.write)
    return buf.getvalue()

  """
   * Method download a file from FTP
   * @param string $filePath path on remote server
   * @param string $fileTarget local path to store a file
   * @throws Exception
  """
  def get_file(self, file_path, file_target):
    try:
      file = open(file_target, 'wb')
      self.connection.retrbinary('RETR {}'.format(file_path), file.write)
      file.close()
    except ftplib.all_errors:
      raise Exception('Failed to copy file {} from remote server'.format(file_path))

  """
   * Method uploads file on remote server
   * @param string $from local path of file to upload
   * @param string $to remote path where file will be placed
   * @param string $premisson set uploaded file premission (Optional)
   * @throws Exception
  """
  def upload_file(self, from_file, to_file, premisson = None):
    self.create_path(to_file, premisson)
    try:
      self.connection.storlines('STOR {}'.format(to_file), open(from_file, 'r'))
    except ftplib.all_errors as e:
      raise Exception('Failed to copy file {} to {} on remote server'.format(from_file, to_file));

    self.set_premission(to_file, premisson)


  """
   * Method uploads string to remote server
   * @param string $filePath remote path where file will be placed
   * @param string $string string to store
   * @param string $premisson set uploaded file premission (Optional)
  """
  def upload_string(self, file_path, string, premisson = None):
    self.create_path(file_path, premisson)
    try:
      buf = StringIO.StringIO()
      buf.write(string)
      buf.seek(0)
      self.connection.storbinary('STOR {}'.format(file_path), buf)
    except ftplib.all_errors as e:
      raise Exception('Failed to copy string {} to {} on remote server'.format(string, file_path));

    self.set_premission(file_path, premisson)
    
  """
   * Method delete file on remote server
   * @param string $file
   * @throws Exception
  """
  def delete_file(self, file):
    try:
      self.connection.delete(file)
    except ftplib.all_errors:
      raise Exception('Failed to delete file {} on remote server'.format(file));

  """
   * Method creates dirpath
   * @param string $filePath path to file/dir to create
   * @param string $premisson premission for dirs
   * @throws Exception
  """
  def create_path(self, file_path, premisson = None):
    dirs = os.path.dirname(file_path).replace(self.root, '').split('/')
    dir_path = self.root
    status = True
    for dir in dirs:
      dir_path = os.path.join(dir_path, dir)
      
      try:
        self.connection.cwd(dir_path)
      except ftplib.all_errors:
        if status:
          try:
            self.connection.mkd(dir_path)
            self.set_premission(dir_path, premisson)
          except ftplib.all_errors:
            status = False
            pass
        else:
          break
    if status == False:
      raise Exception('Failed to create path {} on remote server'.format(dirs))

  """
   * Method sets premission to file/dir
   * @param string $filePath path to file/dir
   * @param string $premisson
   * @throws Exception
  """
  def set_premission(self, file_path, premisson):
    if premisson:
      try:
        self.connection.sendcmd('chmod {} {} '.format(premisson, file_path))
      except ftplib.all_errors:
        raise Exception ('Failed to set premisson on {}'.format(file_path))
  
  
class Ftps(Ftp):
  """
   * Constructor, creates connection to remote FTP server
   * @param string $host Hostname
   * @param string $user Username
   * @param string $root A ftp ROOT
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
  """
  def __init__(self, host, user, root = '/', port = 21, password = None):
    self.root = root
    
    try:
      self.connection = ftplib.FTP_TLS
      self.connection.connect(host, port)
    except ftplib.all_errors:
      raise Exception('Failed to connect to server!')
    
    try:
      self.connection.login(user, password)
      self.connection.prot_p() 
    except ftplib.all_errors:
      raise Exception('Failed to log in, incorrect password or login!')
  
  
  
class Ssh:
  connection = None
  sftp_connection = None
  fingerprints = []
  public_key = None
  private_key = None
  private_key_passphrase = None
  root = None
  
  def __init__(self, host, user, root = '/', port = 22, password = None):
    self.root = root
    
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
      client.connect(host, port, user, password)
      self.connection = sftp.open_sftp()
    except (paramiko.SSHException, socket.error):
      raise Exception('Failed to connect to server!')
    
    
    sftp.get(remote_path, local_path)
    sftp.put(local_path, remote_path)
    

  """
   * Method reads file from remote server
   * @param string $filePath path to file on remote server
   * @return string file content
  """
  def read_file(self, file_path):
    buf = StringIO.StringIO()
    try:
      remote_file = self.connection.open(file_path)
      for line in remote_file:
        buf.write(line)
    finally:
      remote_file.close()
    return buf.getvalue()


  """
   * Method downloads file from remote server
   * @param string $filePath
   * @param string $fileTarget
   * @throws Exception
  """
  def get_file(self, file_path, file_target):
    self.connection.get(file_path, file_target)

  """
   * Uploads file on remote server
   * @param string $from
   * @param string $to
   * @param string $premisson
   * @throws Exception
  """
  def upload_file(self, from_file, to_file, premisson = 0o755):
    self.connection.put(from_file, to_file)
   
  """
   * Uploads string on remote server
   * @param string $filePath
   * @param string $string
   * @param string $premisson
  """
  def upload_string(self, file_path, string, premisson = 0o755):
    f = self.sftp.open(file_path, 'wb')
    f.write(string)
    f.close()

  """
   * Deletes file on remote server
   * @param type $file
   * @throws Exception
  """
  def delete_file(self, file):
    self.connection.remove(file)

  """
   * Creates path on remote server
   * @param type $filePath
   * @param type $premisson
  """
  def create_path(self, file_path, premisson = 0o755):
    self.connection.mkdir(os.path.dirname(file_path))
  
  
class Color:

  """
   * method colorize string
   * @param string $string String to colorize
   * @param string $foreground_color color of text
   * @param string $background_color color of background
   * @return string
  """
  @staticmethod
  def string(string, foreground_color = None, background_color = None):
    foreground_colors = {}
    background_colors = {}
    foreground_colors['black'] = '0;30'
    foreground_colors['dark_gray'] = '1;30'
    foreground_colors['blue'] = '0;34'
    foreground_colors['light_blue'] = '1;34'
    foreground_colors['green'] = '0;32'
    foreground_colors['light_green'] = '1;32'
    foreground_colors['cyan'] = '0;36'
    foreground_colors['light_cyan'] = '1;36'
    foreground_colors['red'] = '0;31'
    foreground_colors['light_red'] = '1;31'
    foreground_colors['purple'] = '0;35'
    foreground_colors['light_purple'] = '1;35'
    foreground_colors['brown'] = '0;33'
    foreground_colors['yellow'] = '1;33'
    foreground_colors['light_gray'] = '0;37'
    foreground_colors['white'] = '1;37'

    background_colors['black'] = '40'
    background_colors['red'] = '41'
    background_colors['green'] = '42'
    background_colors['yellow'] = '43'
    background_colors['blue'] = '44'
    background_colors['magenta'] = '45'
    background_colors['cyan'] = '46'
    background_colors['light_gray'] = '47'
    
    
    colored_string = '';

    if foreground_color in foreground_colors:
      colored_string += "\033[" + foreground_colors[foreground_color] + "m"

    if background_color in background_colors:
      colored_string += "\033[" + background_colors[background_color] + "m"

    colored_string += string + "\033[0m"

    return colored_string;

  
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
    print(Color.string('Path to repository is: ' . self.ssh_path, 'white', 'black'))
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
      print(Color.string(str(e), 'white', 'red'))

  """
   * Method checks if there is running job for branch, if is it will sleep till another job ends
  """
  def running_job(self):
    wait_time = 10#s
    while self.check_work() == True:
      print(Color.string('Another deploy job is running, waiting {} s to try again...'.format(wait_time), 'yellow', 'black'))
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
  
  
if __name__ == "__main__":
  GitDeploy()