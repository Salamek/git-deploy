CONFIG = {
  # Configure target or multiple targets
  'targets': [
    {
      # Name of target
      'name': 'Testing Target',

      # Target uri
      'uri': 'sftp://user:password@example.com/path/to/deploy',

      # Web hook to run remote hook after deploy is done, optional
      'web_hook': 'http://example.com/your_hook',

      # Enables disables this target
      'enabled': True
    }
  ],
  # Set special file rights to deployed files, relative to GIT root
  'file_rights': {
    'dir/file/*': 777,
    'dir/file': 775
  }
}
