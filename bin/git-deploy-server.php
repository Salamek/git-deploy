#!/usr/bin/php
<?php

/**
 * GitDeployServer is used as post-receive hook with GitDeploy class to deploy specified projects and branches to remote servers
 * Recommended git server is GitLab http://gitlab.org/
 */
class GitDeployServer
{
  /**
   * Domain where git server is running, fill in only when running with "unknow git server"
   * @var string 
   */
  private $git_host = 'www.gitlab.loc';
  
  /**
   * Path to git repositories, fill in only when running with "unknow git server"
   * @var string 
   */
  private $repository_path = '/home/git/repositories/';
  
  /**
   * User under with git is running, default is git, fill in only when running with "unknow git server" or under nonstandard user
   * @var string 
   */
  private $git_user = 'git';
  
  /**
   * Specifies name of TMP dir, its created in server repo root
   * @var string 
   */
  private $tmp_dir = 'deploy_tmp';
  
  private $self_path;
  private $ssh_path;
  private $stdin;
  private $previous_revision;
  private $branch;
  protected $current_revision;
  protected $tmp;
  
  public function __construct()
  {
    //Get data
    $this->stdin = trim(fgets(STDIN));
    $this->self_path = getcwd();
    $this->git_user = get_current_user();
    
    //Build needed info
    $this->ssh_path = $this->git_user.'@'.$this->git_host.':'.str_replace($this->repository_path, '', $this->self_path);
    
    //Parse stdin
    list($prev, $current, $branch) =  explode(' ', $this->stdin);
    $this->previous_revision = $prev;
    $this->current_revision = $current;
    $this->branch = end(explode('/', $branch));
    
    //Separate tmp repos per branch
    $this->tmp_dir = $this->tmp_dir.'/'.$this->branch;
    
    $this->tmp = $this->self_path.'/'.$this->tmp_dir;
    
    $this->sync();
  }
  
  private function sync()
  {
    if(is_dir($this->tmp_dir))
    {
      exec('unset GIT_DIR && cd '.$this->tmp.' && git pull');
    }
    else
    {
      exec('git clone -b '.$this->branch.' '.$this->ssh_path.' '.$this->tmp); //Create new TMP repo
    }
  }
}

//lrwxrwxrwx 1 git git 41 17. dub 16.29 post-receive -> /home/git/gitlab-shell/hooks/post-receive

/**
 * GitDeploy is client side git project deployer (or server side if used with GitDeployServer)
 */
class GitDeploy
{
  private $root        = NULL;
  private $current_revision = NULL;
  private $git         = NULL;
  private $configFile  = 'deploy.ini';
  private $config      = NULL;
  private $revisonFile = 'REVISION';

  /**
   * Constructor
   * @param GitDeployServer $config
   */
  public function __construct($config = NULL) 
  {
    $this->current_revision = NULL;
    $root = NULL;
    
    if($config instanceof GitDeployServer)
    {
      $this->current_revision = $config->current_revision;
      $root = $config->tmp;
    }
    elseif (is_string($config))
    {
      $root = $config;
    }
    
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
  
  /**
   * Method parses deploy ini config
   * @throws Exception
   */
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
  
  /**
   * Method performs deployement
   */
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
    
    
    $gitRevision = NULL;
    $gitRevisionLog = NULL;
    try
    {
      if($this->current_revision)
      {
        $gitRevisionLog = $gitRevision = $this->current_revision;
      }
      else
      {
        $gitRevisionLog = $gitRevision = trim($this->git->getRevision());
      }
      $revision =  trim($connection->readFile($this->config['uri']['path'].'/'.$this->revisonFile));
    }
    catch(Exception $e)
    {
      //here i assume no version file on remote, so invalide version check
      $gitRevision = FALSE;
      $revision = NULL;
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
        $premisson = $this->checkPremisson($upload);
        $connection->uploadFile($this->root.'/'.$upload, $this->config['uri']['path'].'/'.$upload, $premisson);
        echo Color::string('++ Deploying file '.$this->root.'/'.$upload.' --> '.$this->config['uri']['path'].'/'.$upload, 'green', 'black');
      }
      
      foreach($files['delete'] AS $delete)
      {
        $connection->deleteFile($this->config['uri']['path'].'/'.$delete);
        echo Color::string('-- Deleting file '.$delete, 'green', 'black');
      }
      
      $connection->uploadString($this->config['uri']['path'].'/'.$this->revisonFile, $gitRevisionLog);
      
      echo Color::string('Deploying done!', 'white', 'green');
    }
    else
    {
      echo Color::string('Revisions match, no deploy needed.', 'white', 'green');
    }
  }
  
  /**
   * Method checks config data for special rights configuration
   * @param string $filename
   * @return octdec filerights
   */
  private function checkPremisson($filename)
  {
    foreach($this->config['file_rights'] AS $k => $v)
    {
      if($this->endsWith($filename,$k) !== FALSE)
      {
        return octdec($v);
      }
    }
    return NULL;
  }
  
  /**
   * Helper method checks if string ends with a string :)
   * @param string $haystack
   * @param string $needle
   * @return boolean
   */
  private function endsWith($haystack, $needle)
  {
    $length = strlen($needle);
    if ($length == 0) 
    {
      return true;
    }

    return (substr($haystack, -$length) === $needle);
  }

}

/**
 * This class handes work with git repository by executing git commands
 */
class Git
{
  private $root = NULL;
  
  /**
   * Constructor, checks existence of git bin
   * @throws Exception
   */
  public function __construct() 
  {
    if(!$this->isGit()) throw new Exception ('Git not found!');
  }
  
  /**
   * Method checks if git is installed and runnable
   * @return boolean
   */
  public function isGit() 
  {
    $status = exec('git 2> /dev/null');
    if($status)
    {
      return true;
    }
    return false;
  }

  /**
   * Method sets current repo branch
   * @param string $branch
   */
  public function setBranch($branch)
  {
    exec('git checkout '.$branch);
  }
  
  /**
   * Method checks if specified directory is git client repo
   * @param string $dir
   * @return boolean
   */
  public function hasGit($dir)
  {
    return is_dir($dir.'/.git');
  }
  
  /**
   * Method returns current revision
   * @return string
   */
  public function getRevision()
  {
    return trim(exec('git rev-parse HEAD'));
  }
  
  /**
   * Method returns list of uncommited files
   * @return array
   */
  public function diffUncommitted()
  {
    $data = array();
    exec('git diff --name-status', $data);
    exec('git diff --cached --name-status', $data);
    return $this->gitParseFiles($data);
  }
  
  /**
   * Method resturns list of Commited files, in specified revision if any
   * @param string $revision
   * @return array
   */
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
  
  /**
   * Method sets and return git root
   * @param string $root set absolute fixed git root (usefull when we running deploy form nongit path)
   * @return string path to repo
   */
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

  /**
   * Method parses git filelist output and builds array from it
   * @param string $data
   * @return array
   */
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

/**
 * Class handles work with FTPS
 */
class FTPS extends FTP
{
  /**
   * Constructor, creates connection to remote FTP server
   * @param string $host Hostname
   * @param string $user Username
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
   */
  public function __construct($host, $user, $port = NULL, $password = NULL) 
  {
    $this->connection = @ftp_ssl_connect($host, $port);
    if(!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }

    if(!@ftp_login($this->connection, $user, $password))
    {
      throw new Exception('Failed to log in, incorrect password or login!'); 
    }
  }
}

/**
 * Class handles work with FTP
 */
class FTP
{
  public $connection = NULL;
  
  /**
   * Constructor, creates connection to remote FTP server
   * @param string $host Hostname
   * @param string $user Username
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
   */
  public function __construct($host, $user, $port = NULL, $password = NULL) 
  {
    $this->connection = @ftp_connect($host, $port);
    if(!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }
    
    if(!@ftp_login($this->connection, $user, $password))
    {
      throw new Exception('Failed to log in, incorrect password or login!'); 
    }
  }
  
  /**
   * Destructor, close connection to ftp server
   */
  public function __destruct() 
  {
    ftp_close($this->connection);
  }
  
  /**
   * Method reads file on remote FTP and returns it content (ASCII)
   * @param string $filePath path on remote server
   * @return string
   */
  public function readFile($filePath)
  {
    $tmp = sys_get_temp_dir().'/ftp_file_temp_'.getmypid().'.tmp';
    $this->getFile($filePath, $tmp);
    $data = file_get_contents($tmp);
    unlink($tmp);
    return $data;
  }
  
  /**
   * Method download a file from FTP
   * @param string $filePath path on remote server
   * @param string $fileTarget local path to store a file
   * @throws Exception
   */
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
  
  /**
   * Method uploads file on remote server
   * @param string $from local path of file to upload
   * @param string $to remote path where file will be placed
   * @param string $premisson set uploaded file premission (Optional)
   * @throws Exception
   */
  public function uploadFile($from, $to, $premisson = NULL)
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
  
  /**
   * Method uploads string to remote server
   * @param string $filePath remote path where file will be placed
   * @param string $string string to store
   * @param string $premisson set uploaded file premission (Optional)
   */
  public function uploadString($filePath, $string, $premisson = NULL)
  {
    $tmp = sys_get_temp_dir().'/ftp_file_temp_'.getmypid().'.tmp';
    file_put_contents($tmp,$string);
    $this->uploadFile($tmp, $filePath, $premisson);
    unlink($tmp);
  }
  
  /**
   * Method delete file on remote server
   * @param string $file
   * @throws Exception
   */
  public function deleteFile($file)
  {
    if(!@ftp_delete($this->connection, $file))
    {
      throw new Exception(sprintf('Failed to delete file %s on remote server', $file));
    }
  }
  
  public function createPath($filePath, $premisson = NULL)
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
    if($premisson)
    {
      if(!@ftp_chmod($this->connection, $premisson, $filePath))
      {
        throw new Exception(sprintf('Failed to set premisson on', $filePath));
      }
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

//For server side
$server = new GitDeployServer();
new GitDeploy($server);

//For client side (Run from repo root)
//new GitDeploy();

//For client side (Run from *)
//new GitDeploy('/path/to/git/repository');



?>
