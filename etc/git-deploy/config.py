CONFIG = {

  # Server configuration
  'server':{

    # Port to run on
    'port': 7416,

    # Where to store logs
    'file_log': '/home/git/git-deploy.log', 

    # User to run under
    'user': 'git'
  },

  # 
  'hook': {

    # Path to temp dir
    'tmp_path': '/home/git/tmp',

    # Path to git repositories
    'repository_path': '/home/git/repositories'
  }
}