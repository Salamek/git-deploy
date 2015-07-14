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
__date__ ="$6.7.2014 0:00:35$"

import StringIO
import ftplib
import os
 
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
   * Method reads file on remote FTP and returns it content
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
      self.connection.storbinary('STOR {}'.format(to_file), open(from_file, 'rb'))
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
    dirs = os.path.dirname(file_path)
    if self.root != '/':
      dirs = dirs.replace(self.root, '')
    
    dirs = dirs.split('/')
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
          except ftplib.all_errors as e:
            status = False
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
  
  
