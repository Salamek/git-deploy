# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Adam Schubert"
__date__ ="$6.7.2014 0:14:55$"

import ftplib
import ftp

class Ftps(ftp.Ftp):
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
      self.connection = ftplib.FTP_TLS()
      self.connection.connect(host, port)
    except ftplib.all_errors:
      raise Exception('Failed to connect to server!')
    
    try:
      self.connection.login(user, password)
      self.connection.prot_p() 
    except ftplib.all_errors:
      raise Exception('Failed to log in, incorrect password or login!')
    
