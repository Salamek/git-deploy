import os
import imp
import ConfigParser
import urlparse

class configReader(object):
  config = None
  config_file = None
  config_filename = None
  def __init__(self, config_file):
    if os.path.isfile(config_file) is False:
      raise Exception('Config file {} not found'.format(config_file))
    
    self.config_file = config_file
    self.config_filename = os.path.basename(self.config_file)
    class_name, ext = self.config_filename.split('.')
    
    if ext == 'py':
      self.config = self.parse_py_config()
    elif ext == 'cfg' or ext == 'ini':
      self.config = self.parse_ini_config();
    

  def parse_py_config(self):
    class_name, ext = self.config_filename.split('.')
    config_class = imp.load_source(class_name, self.config_file)
    try:
      return config_class.CONFIG
    except AttributeError:
      raise Exception('CONFIG variable not found in {}'.format(self.config_file))
    
    
  def parse_ini_config(self):
    config = ConfigParser.ConfigParser()
    
    config_parsed = {}
    try:
      config.read(self.config_file)

      # Parser for deploy.ini
      if self.config_filename.find('deploy.ini') > -1:
        #parse config and set it into variable
        config_parsed['deploy'] = {}
        if config.has_option('deploy', 'target'):
          config_parsed['deploy']['target'] = config.get('deploy', 'target')
        else:
          raise Exception('No taget option found in config {}'.format(config_file_path))

        if config.has_option('deploy', 'deploy'):
          config_parsed['deploy']['deploy'] = config.getboolean('deploy', 'deploy')
        else:
          raise Exception('No deploy option found in config {}'.format(config_file_path))

        if config.has_option('deploy', 'maintainer'):
          config_parsed['deploy']['maintainer'] = config.get('deploy', 'maintainer')
        else:
          config_parsed['deploy']['maintainer'] = ''

        if config.has_section('file_rights'):
          config_parsed['deploy']['file_rights'] = config.items('file_rights')
        else:
          config_parsed['deploy']['file_rights'] = {}

        config_parsed['uri'] = urlparse.urlparse(config_parsed['deploy']['target'].strip("'"))

        if config_parsed['uri'] == None or config_parsed['uri'].hostname == None:
          raise Exception('Failed to prase URI in config file')
      elif self.config_filename.find('git-deploy.cfg') > -1:
        config_parsed = {'server': {}, 'hook': {}}
        if config.has_option('server', 'port'):
          config_parsed['server']['port'] = config.getint('server', 'port')
        else:
          config_parsed['server']['port'] = 7416

        if config.has_option('server', 'file_log'):
          config_parsed['server']['file_log'] = config.get('server', 'file_log')
        else:
          config_parsed['server']['file_log'] = None

        if config.has_option('server', 'user'):
          config_parsed['server']['user'] = config.get('server', 'user')
        else:
          config_parsed['server']['user'] = 'root'

        if config.has_option('hook', 'repository_path'):
          config_parsed['hook']['repository_path'] = config.get('hook', 'repository_path')
        else:
          config_parsed['hook']['repository_path'] = '/home/git/repositories'

        if config.has_option('hook', 'tmp_path'):
          config_parsed['hook']['tmp_path'] = config.get('hook', 'tmp_path')
        else:
          config_parsed['hook']['tmp_path'] = '/home/git/tmp'

    except IOError:
      raise Exception('Failed to parse ' + self.config_file)
    return config_parsed
    
  def get(self):
    return self.config

  def migrate_ini2py(self):
    class_name, ext = self.config_filename.split('.')
    if ext == 'py':
      raise Exception('Only ini or cfg files can be converted to py config')
    elif ext == 'cfg' or ext == 'ini':
      if self.config_filename.find('deploy.ini') == -1 and self.config_filename.find('git-deploy.cfg') == -1:
        raise Exception('This ini/cfg file dont looks like one used by git-deploy')
      
    # ok we got here...
    py_content = []
    if self.config_filename == 'git-deploy.cfg':
      # git-deploy.cfg match to config.py
      
      py_content.append('CONFIG = {')
      py_content.append('')
      py_content.append('  # Server configuration')
      py_content.append('  \'server\':{')
      py_content.append('')
      py_content.append('    # Port to run on')
      py_content.append('    \'port\': ' + str(self.config['server']['port']) + ',')
      py_content.append('')
      py_content.append('    # Where to store logs')
      py_content.append('    \'file_log\': \'' + self.config['server']['file_log'] + '\', ')
      py_content.append('')
      py_content.append('    # User to run under')
      py_content.append('    \'user\': \'' + self.config['server']['user'] + '\'')
      py_content.append('  },')
      py_content.append('')
      py_content.append('  # ')
      py_content.append('  \'hook\': {')
      py_content.append('')
      py_content.append('    # Path to temp dir')
      py_content.append('    \'tmp_path\': \'' + self.config['hook']['tmp_path'] + '\',')
      py_content.append('')
      py_content.append('    # Path to git repositories')
      py_content.append('    \'repository_path\': \'' + self.config['hook']['repository_path'] + '\'')
      py_content.append('  }')
      py_content.append('}')

    if self.config_filename == 'deploy.ini':
      py_content.append('CONFIG = {')
      py_content.append('  # Configure target or multiple targets')
      py_content.append('  \'targets\': [')
      py_content.append('    {')
      py_content.append('      # Target uri')
      py_content.append('      \'uri\': \'' + self.config['deploy']['target'] + '\',')
      py_content.append('')
      py_content.append('      # Web hook to run remote hook after deploy is done, optional')
      py_content.append('      \'web_hook\': None,')
      py_content.append('')
      py_content.append('      # Enables disables this target')
      py_content.append('      \'enabled\': ' + 'True' if self.config['deploy']['target'] else 'False' )
      py_content.append('    }')
      py_content.append('  ],')
      py_content.append('  # Set special file rights to deployed files, relative to GIT root')
      py_content.append('  \'file_rights\': {')
      
      rights = []
      for path, right in self.config['deploy']['file_rights']:
        rights.append('    \'' + path + '\': ' + right)
      py_content.append(", \n".join(rights)) 
      py_content.append('  }')
      py_content.append('}')

    # filename is differend git-deploy.cfg -> config.py
    if class_name == 'git-deploy':
      file_name = self.config_file.replace('git-deploy.cfg', 'config.py')
    else:
      file_name = self.config_file
      
    with open(file_name, "w") as new_config_file:
      new_config_file.write("\n".join(py_content))