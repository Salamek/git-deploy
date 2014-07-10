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
__date__ ="$10.7.2014 0:05:45$"

from shell import Shell

class Log:
  messages = {}
  def __init__(self):
    self.messages = {'ok': [], 'warning': [], 'error': []}
  
  def add(self, message, type = 'ok'):
    if type in self.messages:
      self.messages[type].append(message)
    else:
      raise Exception('Message type {} do not exists.'.format(type))
    
  def get(self, type = 'ok'):
    if type in self.messages:
      return self.messages[type]
    else:
      raise Exception('Message type {} do not exists.'.format(type))
    
  def clear(self):
    self.messages = {'ok': [], 'warning': [], 'error': []}
    
  def output(self):
    for ok in self.messages['ok']:
      print(Shell.color(ok, 'white', 'green'))
      
    for warning in self.messages['warning']:
      print(Shell.color(warning, 'yellow', 'black'))
      
    for error in self.messages['error']:
      print(Shell.color(error, 'white', 'red'))