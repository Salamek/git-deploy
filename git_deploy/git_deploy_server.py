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
from flask import Flask, request, jsonify, render_template

class GitDeployServer:
  app = Flask(__name__)
  tmp = None
  def __init__(self, port, tmp, file_log = None):
    self.tmp = tmp
    
    self.app.run(debug = False, host='0.0.0.0', port=port)
    if not self.app.debug and file_log != None:
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(file_log)
        file_handler.setLevel(logging.WARNING)
        self.app.logger.addHandler(file_handler)

  @app.errorhandler(404)
  def not_found(error):
    return jsonify( { 'message': str(error) } ), 404
    
    
    
  @app.route("/", methods = ['GET'])
  def log():
    return jsonify({'message': 'Hi there! Here will be something cool in the feature!'}), 200

  @app.route("/deploy.json", methods = ['POST'])
  def deploy():
    if request.json == None:
      return jsonify({'message': 'I eat only JSON... bark, bark!'}), 400
  
    try:
      git_deploy_remote.GitDeployRemote(request.json['after'], request.json['ref'], request.json['repository']['url'], self.tmp)
      return jsonify({'message': 'ok'}), 200
    except Exception as e:
      return jsonify({'message': str(e)}), 500
  
  
