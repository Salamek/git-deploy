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

import sys
import os
import json
import git_deploy_remote
from twisted.web.server import Site
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.python import log

class GitDeployServerFactory(Resource):
  tmp = None
  def __init__(self, tmp):
    self.tmp = tmp
  def render_GET(self, request):
    return '500 Wrong request!'

  def render_POST(self, request):
    try:
      decoded = json.loads(request.content.read())
      git_deploy_remote.GitDeployRemote(decoded['after'], decoded['ref'], decoded['repository']['url'], self.tmp)
    except ValueError as err:
      return str(err)

class GitDeployServer:
  def __init__(self, port, tmp, file_log = None):
    if file_log:
      log.startLogging(open(file_log, 'w'))
    else:
      log.startLogging(sys.stdout)

    print ('Running on pid {}'.format(os.getpid()))
    root = Resource()
    root.putChild("deploy.json", GitDeployServerFactory(tmp))
    factory = Site(root)
    reactor.listenTCP(port, factory)
    reactor.run()
  
  
