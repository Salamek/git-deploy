#!/usr/bin/php
<?php

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
      }
      catch(Exception $e)
      {
        echo Color::string($e->getMessage(), 'white', 'red');
      }
    }
    catch(Exception $e)
    {
      echo Color::string($e->getMessage(), 'white', 'red');
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
    
    $revision = NULL;
    $gitRevision = NULL;
    try
    {
      $revision =  trim($connection->readFile($this->config['uri']['path'].'/'.$this->revisonFile));
      $gitRevision = trim($this->git->getRevision());
    }
    catch(Exception $e)
    {
      //here i assume no version file on remote, so invalide version check
      $gitRevision = FALSE;
    }
    
    //Revision not match, we must get changes and upload it on server
    if($gitRevision !== $revision)
    {
      if($revision && $gitRevision)
      {
        $text = sprintf('Remote revision is %s, current revison is %s', $revision, $gitRevision);
        echo Color::string($text, 'green', 'black');
      }
      else
      {
        $text = sprintf('No remote revision, deploying revision %s', $gitRevision);
        echo Color::string($text, 'green', 'black');
      }
      
      $files = $this->git->diffCommited($revision);
      print_r($files);
    }
    else
    {
      echo Color::string('Revisions match, no deploy needed.', 'white', 'green');
    }
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
    $data = array();
    exec('git diff --name-status', $data);
    exec('git diff --cached --name-status', $data);
    return $this->gitParseFiles($data);
  }
  
  public function diffCommited($revision = NULL)
  {
    $files = array();
    if ($revision)
    {
      exec('git diff --name-status '.$revision, $files);
    }
    else
    {
      $data = array();
      exec('git ls-files '.$this->getGitRoot().'  --full-name', $data);
      foreach ($data AS $line)
      {
        $files[] = 'M	'.$line;
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
    $return = array('upload' => array(), 'delete' => array());
    if(count($data) > 0)
    {
      foreach ($data AS $line)
      {
        if($line)
        {
          $line_r = explode('	',trim($line));
          list($action, $filename) = $line_r;

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
    }
    return $return;
  }
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

    /*!FIXME idk how to calculate FP from this or it is possible
     * if(!$this->fingerprints)
    {
      $this->fingerprints = $keyInfo['fingerprints'];
    }*/
    
    if(!$this->publicKey)
    {
      $this->publicKey = $keyInfo['publicKey'];
    }
    
    if(!$this->privateKey)
    {
      $this->privateKey = $keyInfo['privateKey'];
    }
    
    /*!FIXME idk how to calculate FP from this or it is possible
    $fingerprint = ssh2_fingerprint($this->connection, SSH2_FINGERPRINT_SHA1 | SSH2_FINGERPRINT_HEX); 
    if(!in_array($fingerprint, $this->fingerprints))
    { 
      throw new Exception('Server has unknow fingerprint :'. $fingerprint); 
    }*/
    
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
    $userHome = $_SERVER['HOME'];
    
    $return = array();
    $return['publicKey']    = '';
    $return['privateKey']    = '';
    $return['fingerprints'] = array();
    
    if(isset($userHome))
    {
      $sshDir = $userHome.'/.ssh';
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
  
  
  public function readFile($filePath)
  {
    $tmp = sys_get_temp_dir().'/ssh_file_temp_'.getmypid().'.tmp';
    $this->getFile($filePath, $tmp);
    $data = file_get_contents($tmp);
    unlink($tmp);
    return $data;
  }
  
  public function getFile($filePath, $fileTarget)
  {
    if(!@ssh2_scp_recv($this->connection, $filePath, $fileTarget))
    {
      throw new Exception('Failed to copy file from remote server');
    }
  }
}

class Color
{
  public static $foreground_colors = array();
  public static $background_colors = array();


  public static function init() 
  {
    self::$foreground_colors['black']         = '0;30';
    self::$foreground_colors['dark_gray']     = '1;30';
    self::$foreground_colors['blue']          = '0;34';
    self::$foreground_colors['light_blue']    = '1;34';
    self::$foreground_colors['green']         = '0;32';
    self::$foreground_colors['light_green']   = '1;32';
    self::$foreground_colors['cyan']          = '0;36';
    self::$foreground_colors['light_cyan']    = '1;36';
    self::$foreground_colors['red']           = '0;31';
    self::$foreground_colors['light_red']     = '1;31';
    self::$foreground_colors['purple']        = '0;35';
    self::$foreground_colors['light_purple']  = '1;35';
    self::$foreground_colors['brown']         = '0;33';
    self::$foreground_colors['yellow']        = '1;33';
    self::$foreground_colors['light_gray']    = '0;37';
    self::$foreground_colors['white']         = '1;37';

    self::$background_colors['black']         = '40';
    self::$background_colors['red']           = '41';
    self::$background_colors['green']         = '42';
    self::$background_colors['yellow']        = '43';
    self::$background_colors['blue']          = '44';
    self::$background_colors['magenta']       = '45';
    self::$background_colors['cyan']          = '46';
    self::$background_colors['light_gray']    = '47';
  }

  public static function string($string, $foreground_color = NULL, $background_color = NULL) 
  {
    self::init();
    $colored_string = '';

    if (in_array($foreground_color, self::$foreground_colors)) 
    {
      $colored_string .= "\033[" . self::$foreground_colors[$foreground_color] . "m";
    }

    if (in_array($background_color, self::$background_colors)) 
    {
      $colored_string .= "\033[" . self::$background_colors[$background_color] . "m";
    }

    $colored_string .=  $string . "\033[0m";

    return $colored_string.PHP_EOL;
	}
}


$git = new GitDeploy('/home/sadam/git/git-deploy');
//print_r($git->diffUncommitted());


?>