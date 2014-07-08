# To change this license header, choose License Headers in Project Properties.
# To change this template file, choose Tools | Templates
# and open the template in the editor.

from setuptools import setup

__author__="Adam Schubert"
__date__ ="$8.7.2014 20:26:41$"

setup(
  name="git-deploy",
  version="2.0.0",
  author=__author__,
  author_email="adam.schubert@sg1-game.net",
  description="Git-deploy is tool written in python to allow fast and easy deployments on remote servers wia S/FTP, SSH/SCP",
  long_description=open('README.md').read(),
  license="GPL",
  install_requires=['paramiko'],
  url="https://github.com/Salamek/git-deploy",
  packages=['git-deploy', 'git-deploy/classes'],
  package_dir={'git-deploy': 'git-deploy'},
  #package_data={},
  entry_points={
    'console_scripts': ['git-deploy']
  },
  data_files=[
    ('/etc/init.d', ['etc/init.d/git-deploy']), ('/etc/git-deploy', ['etc/git-deploy/git-deploy.cfg'])
  ]
)
