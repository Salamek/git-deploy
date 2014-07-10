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
    
