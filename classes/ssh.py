# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Adam Schubert"
__date__ ="$6.7.2014 0:01:09$"

import StringIO
import paramiko
import socket
import os
  
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
      self.connection = client.open_sftp()
    except (paramiko.SSHException, socket.error):
      raise Exception('Failed to connect to server!')
    
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
    self.create_path(to_file, premisson)
    self.connection.put(from_file, to_file)
   
  """
   * Uploads string on remote server
   * @param string $filePath
   * @param string $string
   * @param string $premisson
  """
  def upload_string(self, file_path, string, premisson = 0o755):
    self.create_path(file_path, premisson)
    f = self.connection.open(file_path, 'wb')
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
  
