# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

__author__="Adam Schubert"
__date__ ="$10.7.2014 0:05:45$"

from shell import Shell

class Log:
  
  messages = {'ok': [], 'warning': [], 'error': []}
  
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