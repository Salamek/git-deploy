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
        $connection = new FTP($this->config['uri']['host'], $this->config['uri']['user'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : NULL), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;
      
      case 'ftps':
        $connection = new FTPS($this->config['uri']['host'], $this->config['uri']['user'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : NULL), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;
    }
    
    $revision = NULL;
    $gitRevision = NULL;
    $gitRevisionLog = NULL;
    try
    {
      $gitRevisionLog = $gitRevision = trim($this->git->getRevision());
      $revision =  trim($connection->readFile($this->config['uri']['path'].'/'.$this->revisonFile));
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
        $text = sprintf('No remote revision found, deploying whole project %s', $gitRevisionLog);
        echo Color::string($text, 'yellow', 'black');
      }
      
      $files = $this->git->diffCommited($revision);
      
      foreach($files['upload'] AS $upload)
      {
        $connection->uploadFile($this->root.'/'.$upload, $this->config['uri']['path'].'/'.$upload);
        echo Color::string('Uploading file '.$this->root.'/'.$upload.' --> '.$this->config['uri']['path'].'/'.$upload, 'green', 'black');
      }
      
      foreach($files['delete'] AS $delete)
      {
        $connection->deleteFile($this->config['uri']['path'].'/'.$delete);
      }
      
      $connection->uploadString($this->config['uri']['path'].'/'.$this->revisonFile, $gitRevisionLog);
      
      echo Color::string('Deploying done!', 'white', 'green');
    }
    else
    {
      echo Color::string('Revisions match, no deploy needed.', 'white', 'green');
    }
  }

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

class FTPS extends FTP
{
  public function __construct($host, $user, $port = NULL, $password = NULL) 
  {
    $this->connection = ftp_ssl_connect($host, $port);
    if(!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }
    
    if(!ftp_login($this->connection, $user, $password))
    {
      throw new Exception('Failed to log in, incorrect password or login!'); 
    }
  }
}

class FTP
{
  private $connection = NULL;
  public function __construct($host, $user, $port = NULL, $password = NULL) 
  {
    $this->connection = ftp_connect($host, $port);
    if(!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }
    
    if(!ftp_login($this->connection, $user, $password))
    {
      throw new Exception('Failed to log in, incorrect password or login!'); 
    }
  }
  
  public function __destruct() 
  {
    ftp_close($this->connection);
  }
  
  
  public function readFile($filePath)
  {
    $tmp = sys_get_temp_dir().'/ftp_file_temp_'.getmypid().'.tmp';
    $this->getFile($filePath, $tmp);
    $data = file_get_contents($tmp);
    unlink($tmp);
    return $data;
  }
  
  public function getFile($filePath, $fileTarget)
  {
    $handle = fopen($fileTarget, 'w');
    $status = @ftp_fget($this->connection, $handle, $filePath, FTP_BINARY, 0);
    fclose($handle);
    
    if(!$status)
    {
      throw new Exception(sprintf('Failed to copy file %s from remote server', $filePath));
    }
  }
  
  public function uploadFile($from, $to, $premisson = 0755)
  {
    $this->createPath($to, $premisson);
    $handle = fopen($from, 'r');
    $status = @ftp_fput($this->connection, $to, $handle, FTP_BINARY);
    fclose($handle);
    if(!$status)
    {
      throw new Exception(sprintf('Failed to copy file %s to %s on remote server', $from, $to));
    }
    $this->setPremission($to, $premisson);
  }
  
  public function uploadString($filePath, $string, $premisson = 0755)
  {
    $tmp = sys_get_temp_dir().'/ftp_file_temp_'.getmypid().'.tmp';
    file_put_contents($tmp,$string);
    $this->uploadFile($tmp, $filePath, $premisson);
    unlink($tmp);
  }
  
  public function deleteFile($file)
  {
    if(!@ftp_delete($this->connection, $file))
    {
      throw new Exception(sprintf('Failed to delete file %s on remote server', $file));
    }
  }
  
  public function createPath($filePath, $premisson = 0755)
  {
    $dirs = pathinfo($filePath,PATHINFO_DIRNAME);
    $dirArray =  explode('/', $dirs);
    
    $dirPath = '';
    $status = true;
    foreach($dirArray AS $dir)
    {
      $dirPath .= $dir.'/';
      if(!@ftp_chdir($this->connection, $dirPath))
      {
        if($status)
        {
          $status = @ftp_mkdir($this->connection, $dirPath);
          if($status)
          {
            $this->setPremission($dirPath, $premisson);
          }
        }
        else 
        {
          break;
        }
      }
    }
    
    if(!$status)
    {
      throw new Exception(sprintf('Failed to create path on remote server', $dirs));
    }
  }
  
  private function setPremission($filePath, $premisson)
  {
    if(!@ftp_chmod($this->connection, $premisson, $filePath))
    {
      throw new Exception(sprintf('Failed to set premisson on', $filePath));
    }
  }
}

class SSH
{
  private $connection           = NULL;
  private $sftpConnection       = NULL;
  //Keep this empty or NULL for autodetection!
  //private $fingerprints         = array();
  private $publicKey            = NULL;
  private $privateKey           = NULL;
  private $privateKeyPassphrase = NULL;
  
  public function __construct($host, $user, $port = NULL, $password = NULL)
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
    
    //I assume we have connection and logged by key or password, so init sftp connection to mkdir and delete files
    $this->sftpConnection = ssh2_sftp($this->connection);
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
      throw new Exception(sprintf('Failed to copy file %s from remote server', $filePath));
    }
  }
  
  public function uploadFile($from, $to, $premisson = 0755)
  {
    $this->createPath($to, $premisson);
    if(!@ssh2_scp_send($this->connection, $from, $to, $premisson))
    {
      throw new Exception(sprintf('Failed to copy file %s to %s on remote server', $from, $to));
    }
  }
  
  public function uploadString($filePath, $string, $premisson = 0755)
  {
    $tmp = sys_get_temp_dir().'/ssh_file_temp_'.getmypid().'.tmp';
    file_put_contents($tmp,$string);
    $this->uploadFile($tmp, $filePath, $premisson);
    unlink($tmp);
  }
  
  public function deleteFile($file)
  {
    if(!ssh2_sftp_unlink($this->sftpConnection, $file))
    {
      throw new Exception(sprintf('Failed to delete file %s on remote server', $file));
    }
  }
  
  public function createPath($filePath, $premisson = 0755)
  {
    $dirs = pathinfo($filePath,PATHINFO_DIRNAME);
    ssh2_sftp_mkdir($this->sftpConnection, $dirs, $premisson, TRUE);
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

    if (array_key_exists($foreground_color, self::$foreground_colors)) 
    {
      $colored_string .= "\033[" . self::$foreground_colors[$foreground_color] . "m";
    }

    if (array_key_exists($background_color, self::$background_colors)) 
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