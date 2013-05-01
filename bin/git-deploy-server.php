#!/usr/bin/php
<?php
class Git
{
  private $root = NULL;
  public function __construct() 
  {
    if(!$this->isGit()) throw new Exception ('Git not found!');
  }
  
  public function isGit() 
  {
    $status = exec('git 2> /dev/null');
    if($status)
    {
      return true;
    }
    return false;
  }
  
  public function hasGit($dir)
  {
    return is_dir($dir.'/.git');
  }
  
  public function getRevision()
  {
    return trim(exec('git rev-parse HEAD'));
  }
  
  public function diffUncommitted()
  {
    $data = trim(exec('git diff --name-status'));
    $data .= trim(exec('git diff --cached --name-status'));
    return $this->gitParseFiles($data);
  }
  
  public function diffCommited($revision = NULL)
  {
    $files = '';
    if ($revision)
    {
      $files .= trim(exec('git diff --name-status'));
    }
    else
    {
      $data = trim(exec('git ls-files '.$this->getGitRoot().'--full-name'));
      $arr = explode("\n", $data);
      foreach ($arr AS $line)
      {
        $files .= 'M	' + $line + "\n";
      }
    }
    return $this->gitParseFiles($files);
  }
  
  public function getGitRoot($root = NULL)
  {
    if(!$root)
    {
      $this->root = trim(exec('git rev-parse --show-toplevel'));
    }
    else 
    {
      $this->root = $root;
    }
    return $this->root;
  }

  private function gitParseFiles($data)
  {
    $ignore = array('.gitignore');
    $lines = explode("\n", $data);
    $return = array('upload' => array(), 'delete' => array());
    if(count($lines) > 0)
    {
      foreach ($lines AS $line)
      {
        list($action, $filename) = explode('	',trim($line));
        $pathinfo = pathinfo($filename);
        if(!in_array($pathinfo['basename'],$ignore))
        {
          switch($action)
          {
            case 'A':
            case 'M':
            case 'C':
              $return['upload'][] = $filename;
              break;
            
            case 'D':
              $return['delete'][] = $filename;
              break;
          }
        }
      }
    }
    return $return;
  }
}

class GitDeploy
{
  private $root        = NULL;
  private $git         = NULL;
  private $configFile  = 'deploy.ini';
  private $config      = NULL;
  private $revisonFile = 'REVISION';

  public function __construct($root = NULL) 
  {
    try
    {
      $this->git = new Git();
      $this->root = $this->git->getGitRoot($root);
      try
      {
        $this->parseConfig();
        if($this->config['deploy']['deploy'])
        {
          $this->deploy();
        }
        print_r($this->config);
      }
      catch(Exception $e)
      {
        echo $e->getMessage();
      }
    }
    catch(Exception $e)
    {
      echo $e->getMessage();
    }
  }
  
  private function parseConfig()
  {
    if(is_file($this->root.'/'.$this->configFile))
    {
      $config = parse_ini_file($this->root.'/'.$this->configFile,true);
      if($config)
      {
        $this->config = $config;
        
        $this->config['uri'] = parse_url($this->config['deploy']['target']);
        if(!$this->config['uri'])
        {
          throw new Exception('Failed to prase URI in config file');
        }
      }
      else 
      {
        throw new Exception('Failed to parse '.$this->root.'/'.$this->configFile);
      }
    }
    else 
    {
      throw new Exception($this->root.'/'.$this->configFile.' not found!');
    }
  }
  
  private function deploy()
  {
    $connection = NULL;
    switch($this->config['uri']['scheme'])
    {
      case 'sftp':
        $connection = new SSH($this->config['uri']['host'], $this->config['uri']['user'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : NULL), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;
    
      case 'ftp':
      case 'ftps':
        $connection = new FTP($this->config['uri']['host'], $this->config['uri']['user'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : NULL), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;
    }
    
    
    print_r($connection);
  }






  /*if os.path.exists(self.root):
      for x in self.config:
        if self.config[x]['skip'] == False:
          if self.config[x]['scheme'] == 'sftp':
            connection = SFTP(self.config[x])
          elif self.config[x]['scheme'] == 'ftps' or self.config[x]['scheme'] == 'ftp':
            connection = FTP(self.config[x])
          else:
            print ('Unknow scheme, please use sftp/ftps/ftp ')

          #We dont need check revision at all
          if self.config[x]['overwrite_if_same_revision'] is False:
            remote_rev = connection.read_file(self.config[x]['revision_file']).decode('utf8').strip()
          else:
            remote_rev = ''

          local_rev = self.git.get_revision()

          if remote_rev == local_rev:
            print ('Revisions match, skiping deploy on ' + self.config[x]['host'])
          else:
            print ('Revisions not match, deploying on ' + self.config[x]['host'])
            files = self.git.diff_comitted(remote_rev)

            #upload new/edited files to FTP
            for u in files['upload']:
              connection.upload_file(self.root + u,u)

            #delete deleted files on FTP
            for d in files['delete']:
              connection.delete(d)

            #deploy new revision file
            connection.upload_string(self.config[x]['revision_file'],local_rev)
            print ("Deploying done!")*/
}

class FTP
{
  function __construct($host, $user, $port = NULL, $password = NULL) 
  {
    echo 'Not implemented yet';
  }
}

class SSH
{
  private $connection           = NULL;
  //Keep this empty or NULL for autodetection!
  private $fingerprints         = array();
  private $publicKey            = NULL;
  private $privateKey           = NULL;
  private $privateKeyPassphrase = NULL;
  
  function __construct($host, $user, $port = NULL, $password = NULL)
  {
    $this->connection = ssh2_connect($host, $port);
    if(!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }
    
    $keyInfo = $this->findKeys();
    print_r($keyInfo);
    if(!$this->fingerprints)
    {
      $this->fingerprints = $keyInfo['fingerprints'];
    }
    
    if(!$this->publicKey)
    {
      $this->publicKey = $keyInfo['publicKey'];
    }
    
    if(!$this->privateKey)
    {
      $this->privateKey = $keyInfo['privateKey'];
    }
    
    $fingerprint = ssh2_fingerprint($this->connection, SSH2_FINGERPRINT_MD5 | SSH2_FINGERPRINT_HEX); 
    if(!in_array($fingerprint, $this->fingerprints))
    { 
      throw new Exception('Server has unknow fingerprint :'. $fingerprint); 
    }
    
    //No password, lets try keys
    if(!$password)
    {
      if (!ssh2_auth_pubkey_file($this->connection, $user, $this->publicKey, $this->privateKey, $this->privateKeyPassphrase)) 
      { 
        throw new Exception('Autentication rejected by server!'); 
      } 
    }
    else 
    {
      if(!ssh2_auth_password($this->connection, $user, $password))
      {
        throw new Exception('Failed to log in, incorrect password or login!'); 
      }
    }
  }
  
  private function findKeys()
  {
    $fingerprintsNames = array('known_hosts');
    $privateKeysNames  = array('id_rsa');   
    $publicKeysNames   = array('id_rsa.pub');   
    $userInfo = posix_getpwuid(getmyuid());
    
    $return = array();
    $return['publicKey']    = '';
    $return['privateKey']    = '';
    $return['fingerprints'] = array();
    
    if(isset($userInfo['dir']))
    {
      $sshDir = $userInfo['dir'].'/.ssh';
      if(is_dir($sshDir))
      {
        //Fingerprints
        foreach($fingerprintsNames AS $fingerPrintName)
        {
          if(is_file($sshDir.'/'.$fingerPrintName))
          {
            $lines = file($sshDir.'/'.$fingerPrintName);
            if(count($lines > 0))
            {
              foreach($lines AS $line)
              {
                $return['fingerprints'][] = trim($line);
              }
            }
            break;
          }
        }
        
        //Private Keys
        foreach($privateKeysNames AS $privateKeyName)
        {
          if(is_file($sshDir.'/'.$privateKeyName))
          {
            $return['privateKey'] = $sshDir.'/'.$privateKeyName;
            break;
          }
        }
        
         //Public Keys
        foreach($publicKeysNames AS $publicKeyName)
        {
          if(is_file($sshDir.'/'.$publicKeyName))
          {
            $return['publicKey'] = $sshDir.'/'.$publicKeyName;
            break;
          }
        }
      }
    }
    
    return $return;
  }
}




$git = new GitDeploy('/home/sadam/git/git-deploy');
//print_r($git->diffUncommitted());


?>