#!/usr/bin/php
<?php

/**
 * GitDeploy is client side git project deployer (or server side if used with GitDeployServer)
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class GitDeploy
{

  private $root = NULL;
  private $currentRevision = NULL;
  private $git = NULL;
  private $configFile = 'deploy.ini';
  private $config = NULL;
  private $revisonFile = 'REVISION';

  /**
   * Constructor
   * @param string $config
   */
  public function __construct($config = NULL)
  {
    $this->currentRevision = NULL;
    $root = NULL;

    if (is_string($config))
    {
      if (is_dir($config))
      {
        $root = $config;
      }
      else
      {
        throw new Exception($config . ' is not a directory or dont exists!');
      }
    }

    try
    {
      $this->git = new Git();
      $this->root = $this->git->getGitRoot($root);
      try
      {
        $this->parseConfig();
        if ($this->config['deploy']['deploy'])
        {
          $this->deploy();
        }
      }
      catch (Exception $e)
      {
        echo Color::string($e->getMessage(), 'white', 'red');
      }
    }
    catch (Exception $e)
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
    if (is_file($this->root . '/' . $this->configFile))
    {
      $config = parse_ini_file($this->root . '/' . $this->configFile, true);
      if ($config)
      {
        $this->config = $config;

        $this->config['uri'] = parse_url($this->config['deploy']['target']);
        if (!$this->config['uri'])
        {
          throw new Exception('Failed to prase URI in config file');
        }
      }
      else
      {
        throw new Exception('Failed to parse ' . $this->root . '/' . $this->configFile);
      }
    }
    else
    {
      echo Color::string($this->root . '/' . $this->configFile . ' not found!, skiping deploy...', 'green', 'black');
    }
  }

  /**
   * Method performs deployement
   */
  private function deploy()
  {
    $connection = NULL;
    switch ($this->config['uri']['scheme'])
    {
      case 'sftp':
        $connection = new SSH($this->config['uri']['host'], $this->config['uri']['user'], $this->config['uri']['path'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : 22), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;

      case 'ftp':
        $connection = new FTP($this->config['uri']['host'], $this->config['uri']['user'], $this->config['uri']['path'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : 21), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;

      case 'ftps':
        $connection = new FTPS($this->config['uri']['host'], $this->config['uri']['user'], $this->config['uri']['path'], (isset($this->config['uri']['port']) ? $this->config['uri']['port'] : 21), (isset($this->config['uri']['pass']) ? $this->config['uri']['pass'] : NULL));
        break;
    }


    $gitRevision = NULL;
    $gitRevisionLog = NULL;
    try
    {
      if ($this->currentRevision)
      {
        $gitRevisionLog = $gitRevision = $this->currentRevision;
      }
      else
      {
        $gitRevisionLog = $gitRevision = trim($this->git->getRevision());
      }
      $revision = trim($connection->readFile($this->config['uri']['path'] . '/' . $this->revisonFile));
    }
    catch (Exception $e)
    {
      //here i assume no version file on remote, so invalide version check
      $gitRevision = FALSE;
      $revision = NULL;
    }

    //Revision not match, we must get changes and upload it on server
    if ($gitRevision !== $revision)
    {
      if ($revision && $gitRevision)
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

      $errors = array();
      foreach ($files['upload'] AS $upload)
      {
        if (!Tools::endsWith($upload, $this->configFile))
        {
          try
          {
            $premisson = $this->checkPremisson($upload);
            $connection->uploadFile($this->root . '/' . $upload, $this->config['uri']['path'] . '/' . $upload, $premisson);
            echo Color::string('++ Deploying file ' . $this->config['uri']['path'] . '/' . $upload, 'green', 'black');
          }
          catch(Exception $e)
          {
            $errors[] = $e->getMessage();
          }
        }
      }

      foreach ($files['delete'] AS $delete)
      {
        try
        {
          $connection->deleteFile($this->config['uri']['path'] . '/' . $delete);
          echo Color::string('-- Deleting file ' . $delete, 'green', 'black');
        }
        catch(Exception $e)
        {
          $errors[] = $e->getMessage();
        }
      }

      $connection->uploadString($this->config['uri']['path'] . '/' . $this->revisonFile, $gitRevisionLog);

      if(!empty($errors))
      {
        foreach($errors AS $error)
        {
          echo Color::string($error, 'white', 'red');
        }

        if(isset($this->config['deploy']['maintainer']) && $this->config['deploy']['maintainer'])
        {
          if(filter_var($this->config['deploy']['maintainer'], FILTER_VALIDATE_EMAIL))
          {
            @mail($this->config['deploy']['maintainer'], sprintf('%d errors occurred while deploying project %s ', count($errors), $this->config['uri']['host']), implode("\n", $errors));
          }
          else
          {
            echo Color::string('Maintainer email is set, but has wrong format!', 'white', 'red');
          }
        }

        echo Color::string('Deploying done, but some errors occurred!', 'white', 'yellow');
      }
      else
      {
        echo Color::string('Deploying done!', 'white', 'green');

        if(isset($this->config['deploy']['remote_hook']) && $this->config['deploy']['remote_hook'])
        {
          if(filter_var($this->config['deploy']['remote_hook'], FILTER_VALIDATE_URL))
          {
            file_get_contents($this->config['deploy']['remote_hook']);
          }
          else
          {
            echo Color::string('remote_hook specified but its not valid URL', 'white', 'yellow');
          }
        }
      }
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
    foreach ($this->config['file_rights'] AS $k => $v)
    {
      if (Tools::endsWith($filename, $k) !== FALSE || $k == '*' || (strpos($k, '*') !== FALSE && Tools::startWith($filename, str_replace('*', '', $k))))
      {
        return octdec($v);
      }
    }
    return NULL;
  }

}

/**
 * This class handes work with git repository by executing git commands
 * @author Adam Schubert <adam.schubert@sg1-game.net>
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
    if (!$this->isGit())
      throw new Exception('Git not found!');
  }

  /**
   * Method checks if git is installed and runnable
   * @return boolean
   */
  public function isGit()
  {
    $status = exec('git 2> /dev/null');
    if ($status)
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
    exec('unset GIT_DIR && cd ' . $this->root . ' && git checkout ' . $branch);
  }

  /**
   * Method checks if specified directory is git client repo
   * @param string $dir
   * @return boolean
   */
  public function hasGit($dir)
  {
    return is_dir($dir . '/.git');
  }

  /**
   * Method returns current revision
   * @return string
   */
  public function getRevision()
  {
    return trim(exec('unset GIT_DIR && cd ' . $this->root . ' && git rev-parse HEAD'));
  }

  /**
   * Method returns list of uncommited files
   * @return array
   */
  public function diffUncommitted()
  {
    $data = array();
    exec('unset GIT_DIR && cd ' . $this->root . ' && git diff --name-status', $data);
    exec('unset GIT_DIR && cd ' . $this->root . ' && git diff --cached --name-status', $data);
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
      exec('unset GIT_DIR && cd ' . $this->root . ' && git diff --name-status ' . $revision, $files);
    }
    else
    {
      $data = array();
      exec('unset GIT_DIR && cd ' . $this->root . ' && git ls-files ' . $this->getGitRoot() . '  --full-name', $data);
      foreach ($data AS $line)
      {
        $files[] = 'M	' . $line;
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
    if (!$root)
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
    if (count($data) > 0)
    {
      foreach ($data AS $line)
      {
        if ($line)
        {
          $line_r = explode('	', trim($line));
          list($action, $filename) = $line_r;

          $pathinfo = pathinfo($filename);
          if (!in_array($pathinfo['basename'], $ignore))
          {
            switch ($action)
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
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class FTPS extends FTP
{

  /**
   * Constructor, creates connection to remote FTP server
   * @param string $host Hostname
   * @param string $user Username
   * @param string $root A ftp ROOT
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
   */
  public function __construct($host, $user, $root = '/', $port = 21, $password = NULL)
  {
    $this->root = $root;
    $this->connection = @ftp_ssl_connect($host, $port);
    if (!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }

    if (!@ftp_login($this->connection, $user, $password))
    {
      throw new Exception('Failed to log in, incorrect password or login!');
    }
  }

}

/**
 * Class handles work with FTP
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class FTP
{

  public $connection = NULL;
  public $root;

  /**
   * Constructor, creates connection to remote FTP server
   * @param string $host Hostname
   * @param string $user Username
   * @param string $root A ftp ROOT
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
   */
  public function __construct($host, $user, $root = '/', $port = 21, $password = NULL)
  {
    $this->root = $root;
    
    if(!function_exists('ftp_connect'))
    {
      throw new Exception('Function ftp_connect not found, FTP deploy is not available! Please enable ftp module in php.ini');
    }
    
    $this->connection = @ftp_connect($host, $port);
    if (!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }

    if (!@ftp_login($this->connection, $user, $password))
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
    $tmp = sys_get_temp_dir() . '/ftp_file_temp_' . getmypid() . '.tmp';
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

    if (!$status)
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
    if (!$status)
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
    $tmp = sys_get_temp_dir() . '/ftp_file_temp_' . getmypid() . '.tmp';
    file_put_contents($tmp, $string);
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
    if (!@ftp_delete($this->connection, $file))
    {
      throw new Exception(sprintf('Failed to delete file %s on remote server', $file));
    }
  }

  /**
   * Method creates dirpath
   * @param string $filePath path to file/dir to create
   * @param string $premisson premission for dirs
   * @throws Exception
   */
  public function createPath($filePath, $premisson = NULL)
  {
    $dirs = pathinfo($filePath, PATHINFO_DIRNAME);
    $dirArray = explode('/', str_replace($this->root, '', $dirs));

    $dirPath = $this->root . (Tools::endsWith($this->root, '/') !== FALSE ? '' : '/');
    $status = true;
    foreach ($dirArray AS $dir)
    {
      $dirPath .= $dir . '/';
      if (!@ftp_chdir($this->connection, $dirPath))
      {
        if ($status)
        {
          $status = @ftp_mkdir($this->connection, $dirPath);
          if ($status)
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

    if (!$status)
    {
      throw new Exception(sprintf('Failed to create path %s on remote server', $dirs));
    }
  }

  /**
   * Method sets premission to file/dir
   * @param string $filePath path to file/dir
   * @param string $premisson
   * @throws Exception
   */
  private function setPremission($filePath, $premisson)
  {
    if ($premisson)
    {
      if (!@ftp_chmod($this->connection, $premisson, $filePath))
      {
        throw new Exception(sprintf('Failed to set premisson on', $filePath));
      }
    }
  }

}

/**
 * Class handles SSH/SCP connection to server
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class SSH
{

  private $connection = NULL;
  private $sftpConnection = NULL;
  //Keep this empty or NULL for autodetection!
  private $fingerprints = array();
  private $publicKey = NULL;
  private $privateKey = NULL;
  private $privateKeyPassphrase = NULL;
  private $root = NULL;

  /**
   * Constructor, connect to server and log us in
   * @param string $host Hostname of server
   * @param string $user Username
   * @param string $root A SSH ROOT (Unused in SSH/SCP)
   * @param string $port Port (Optional)
   * @param string $password Password (Optional)
   * @throws Exception
   */
  public function __construct($host, $user, $root = '/', $port = 22, $password = NULL)
  {
    $this->root = $root;
    if (function_exists('ssh2_connect'))
    {
      $this->connection = ssh2_connect($host, $port);
    }
    else
    {
      throw new Exception('Function ssh2_connect not found!, please install PECL SSL or use differend protocol');
    }

    if (!$this->connection)
    {
      throw new Exception('Failed to connect to server!');
    }

    $keyInfo = $this->findKeys();

    if (!$this->fingerprints)
    {
      $this->fingerprints = $keyInfo['fingerprints'];
    }

    if (!$this->publicKey)
    {
      $this->publicKey = $keyInfo['publicKey'];
    }

    if (!$this->privateKey)
    {
      $this->privateKey = $keyInfo['privateKey'];
    }

    $fingerprint = ssh2_fingerprint($this->connection, SSH2_FINGERPRINT_SHA1 | SSH2_FINGERPRINT_HEX);
    /* !FIXME how the fuck get fingerprint from know_hosts if(!in_array($fingerprint, $this->fingerprints))
      {
      throw new Exception('Server has unknow fingerprint :'. $fingerprint);
      } */

    //No password, lets try keys
    if (!$password)
    {
      if (!@ssh2_auth_pubkey_file($this->connection, $user, $this->publicKey, $this->privateKey, $this->privateKeyPassphrase))
      {
        throw new Exception('Autentication rejected by server!');
      }
    }
    else
    {
      if (!@ssh2_auth_password($this->connection, $user, $password))
      {
        throw new Exception('Failed to log in, incorrect password or login!');
      }
    }

    //I assume we have connection and logged by key or password, so init sftp connection to mkdir and delete files
    $this->sftpConnection = ssh2_sftp($this->connection);
  }

  /**
   * Method find private/public keys for ssh auth
   * @return array
   */
  private function findKeys()
  {
    $fingerprintsNames = array('known_hosts');
    $privateKeysNames = array('id_rsa');
    $publicKeysNames = array('id_rsa.pub');
    $userHome = $_SERVER['HOME'];

    $return = array();
    $return['publicKey'] = '';
    $return['privateKey'] = '';
    $return['fingerprints'] = array();

    if (isset($userHome))
    {
      $sshDir = $userHome . '/.ssh';
      if (is_dir($sshDir))
      {
        //Fingerprints
        foreach ($fingerprintsNames AS $fingerPrintName)
        {
          if (is_file($sshDir . '/' . $fingerPrintName))
          {
            $lines = file($sshDir . '/' . $fingerPrintName);
            if (count($lines > 0))
            {
              foreach ($lines AS $line)
              {
                $return['fingerprints'][] = trim($line);
              }
            }
            break;
          }
        }

        //Private Keys
        foreach ($privateKeysNames AS $privateKeyName)
        {
          if (is_file($sshDir . '/' . $privateKeyName))
          {
            $return['privateKey'] = $sshDir . '/' . $privateKeyName;
            break;
          }
        }

        //Public Keys
        foreach ($publicKeysNames AS $publicKeyName)
        {
          if (is_file($sshDir . '/' . $publicKeyName))
          {
            $return['publicKey'] = $sshDir . '/' . $publicKeyName;
            break;
          }
        }
      }
    }
    return $return;
  }

  /**
   * Method reads file from remote server
   * @param string $filePath path to file on remote server
   * @return string file content
   */
  public function readFile($filePath)
  {
    $tmp = sys_get_temp_dir() . '/ssh_file_temp_' . getmypid() . '.tmp';
    $this->getFile($filePath, $tmp);
    $data = file_get_contents($tmp);
    unlink($tmp);
    return $data;
  }

  /**
   * Method downloads file from remote server
   * @param string $filePath
   * @param string $fileTarget
   * @throws Exception
   */
  public function getFile($filePath, $fileTarget)
  {
    if (!@ssh2_scp_recv($this->connection, $filePath, $fileTarget))
    {
      throw new Exception(sprintf('Failed to copy file %s from remote server', $filePath));
    }
  }

  /**
   * Uploads file on remote server
   * @param string $from
   * @param string $to
   * @param string $premisson
   * @throws Exception
   */
  public function uploadFile($from, $to, $premisson = 0755)
  {
    $this->createPath($to, $premisson);
    $sftpStream = @fopen('ssh2.sftp://'.$this->sftpConnection.$to, 'w');

    try 
    {
    	if (!$sftpStream) 
    	{
    	    throw new Exception("Could not open remote file: $to");
    	}
    	
    	$data_to_send = @file_get_contents($from);
    	
    	if ($data_to_send === false) 
    	{
    	    throw new Exception("Could not open local file: $from.");
    	}
    	
    	if (@fwrite($sftpStream, $data_to_send) === false) 
    	{
    	    throw new Exception("Could not send data from file: $from.");
    	}
    	
    	fclose($sftpStream);
			
    } 
    catch (Exception $e) 
    {
    	fclose($sftpStream);
    	throw $e;
    }
  }

  /**
   * Uploads string on remote server
   * @param string $filePath
   * @param string $string
   * @param string $premisson
   */
  public function uploadString($filePath, $string, $premisson = 0755)
  {
    $tmp = sys_get_temp_dir() . '/ssh_file_temp_' . getmypid() . '.tmp';
    file_put_contents($tmp, $string);
    $this->uploadFile($tmp, $filePath, $premisson);
    unlink($tmp);
  }

  /**
   * Deletes file on remote server
   * @param type $file
   * @throws Exception
   */
  public function deleteFile($file)
  {
    if (!ssh2_sftp_unlink($this->sftpConnection, $file))
    {
      throw new Exception(sprintf('Failed to delete file %s on remote server', $file));
    }
  }

  /**
   * Creates path on remote server
   * @param type $filePath
   * @param type $premisson
   */
  public function createPath($filePath, $premisson = 0755)
  {
    $dirs = pathinfo($filePath, PATHINFO_DIRNAME);
    ssh2_sftp_mkdir($this->sftpConnection, $dirs, $premisson, TRUE);
  }

}

/**
 * Class used for terminal colorized output :)
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class Color
{

  public static $foreground_colors = array();
  public static $background_colors = array();

  /**
   * Initialize our color pallete
   */
  public static function init()
  {
    self::$foreground_colors['black'] = '0;30';
    self::$foreground_colors['dark_gray'] = '1;30';
    self::$foreground_colors['blue'] = '0;34';
    self::$foreground_colors['light_blue'] = '1;34';
    self::$foreground_colors['green'] = '0;32';
    self::$foreground_colors['light_green'] = '1;32';
    self::$foreground_colors['cyan'] = '0;36';
    self::$foreground_colors['light_cyan'] = '1;36';
    self::$foreground_colors['red'] = '0;31';
    self::$foreground_colors['light_red'] = '1;31';
    self::$foreground_colors['purple'] = '0;35';
    self::$foreground_colors['light_purple'] = '1;35';
    self::$foreground_colors['brown'] = '0;33';
    self::$foreground_colors['yellow'] = '1;33';
    self::$foreground_colors['light_gray'] = '0;37';
    self::$foreground_colors['white'] = '1;37';

    self::$background_colors['black'] = '40';
    self::$background_colors['red'] = '41';
    self::$background_colors['green'] = '42';
    self::$background_colors['yellow'] = '43';
    self::$background_colors['blue'] = '44';
    self::$background_colors['magenta'] = '45';
    self::$background_colors['cyan'] = '46';
    self::$background_colors['light_gray'] = '47';
  }

  /**
   * method colorize string
   * @param string $string String to colorize
   * @param string $foreground_color color of text
   * @param string $background_color color of background
   * @return string
   */
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

    $colored_string .= $string . "\033[0m";

    return $colored_string . PHP_EOL;
  }

}

/**
 * Helper tools
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class Tools
{

  /**
   * Helper method checks if string ends with a string :)
   * @param string $haystack
   * @param string $needle
   * @return boolean
   */
  public static function endsWith($haystack, $needle)
  {
    $length = strlen($needle);
    if ($length == 0)
    {
      return true;
    }

    return (substr($haystack, -$length) === $needle);
  }

  /**
   * Helper method checks if string starts with a string :)
   * @param string $haystack
   * @param string $needle
   * @return boolean
   */
  public static function startWith($haystack, $needle)
  {
    return (strpos($haystack, $needle) == 0 ? true : false);
  }
}

/**
 * GitDeployServer is used as post-receive hook with GitDeploy class to deploy specified projects and branches to remote servers
 * Recommended git server is GitLab http://gitlab.org/
 * rename as post-receive -> /home/git/gitlab-shell/hooks/post-receive
 * @author Adam Schubert <adam.schubert@sg1-game.net>
 */
class GitDeployServer
{

  /**
   * Domain where git server is running, fill in only when running with "unknow git server"
   * @var string
   */
  private $gitHost;

  /**
   * Path to git repositories, fill in only when running with "unknow git server"
   * @var string
   */
  private $repositoryPath;

  /**
   * User under with git is running, default is git, fill in only when running with "unknow git server" or under nonstandard user
   * @var string
   */
  private $gitUser = 'git';

  /**
   * Specifies name of TMP dir, its created in server repo root
   * @var string
   */
  private $tmpDir = 'deploy_tmp';
  private $selfPath;
  private $sshPath;
  private $stdin;
  private $previousRevision;
  private $branch;
  private $lockFile = 'deploy.lck';
  public $currentRevision;
  public $tmp;

  /**
   * Constructor
   * @param string $stdin STDIN
   */
  public function __construct($stdin = null)
  {
    if (!$stdin)
    {
      $this->stdin = explode(' ', trim(fgets(STDIN)));
    }
    else
    {
      $this->stdin = $stdin;
    }

    $this->selfPath = getcwd();
    $this->gitUser = $_SERVER['USER'];
    $this->gitHost = php_uname('n');
    $this->repositoryPath = '/home/' . $this->gitUser . '/repositories/';

    //Build needed info
    $this->sshPath = $this->gitUser . '@' . $this->gitHost . ':' . str_replace($this->repositoryPath, '', $this->selfPath);
    echo Color::string('Path to repository is: ' . $this->sshPath, 'white', 'black');
    //Parse stdin
    list($prev, $current, $branch) = $this->stdin;
    $this->previousRevision = $prev;
    $this->currentRevision = $current;
    $this->branch = end(explode('/', $branch));

    //Separate tmp repos per branch
    $this->tmpDir = $this->tmpDir . '/' . $this->branch;

    $this->tmp = $this->selfPath . '/' . $this->tmpDir;

    try
    {
      $this->runningJob();
      $this->sync();
      $this->deploy();
    }
    catch (Exception $e)
    {
      echo Color::string($e->getMessage(), 'white', 'red');
    }
  }

  /**
   * Method checks if there is running job for branch, if is it will sleep till another job ends
   */
  private function runningJob()
  {
    $waitTime = 10; //s
    while ($this->checkWork())
    {
      echo Color::string(sprintf('Another deploy job is running, waiting %d s to try again...', $waitTime), 'yellow', 'black');
      sleep($waitTime);
    }
  }

  /**
   * Method checks if there is unfinished job
   * @return boolean
   */
  private function checkWork()
  {
    //Info is cached, we must clear cache before check!
    clearstatcache(true, $this->tmp . '/' . $this->lockFile);
    if (is_file($this->tmp . '/' . $this->lockFile))
    {
      //Lock file is less then one hour old... let it be and wait till expire or get removed by finished job
      if ((filectime($this->tmp . '/' . $this->lockFile) + 3600) > time())
      {
        return true;
      }
    }
    return false;
  }

  /**
   * Method sync local TMP with main repo
   */
  private function sync()
  {
    if (is_dir($this->tmp))
    {
      exec('unset GIT_DIR && cd ' . $this->tmp . ' && git pull');
    }
    else
    {
      exec('git clone -b ' . $this->branch . ' ' . $this->sshPath . ' ' . $this->tmp); //Create new TMP repo
    }
    //Create own lock file and continue
    @file_put_contents($this->tmp . '/' . $this->lockFile, $this->currentRevision);
  }

  /**
   * Method calls local deployer
   * @throws Exception
   */
  private function deploy()
  {
    new GitDeploy($this->tmp);
    $this->destroyLock();
  }

  /**
   * Method destroys lock file
   */
  private function destroyLock()
  {
    if ($this->lockFile && is_file($this->tmp . '/' . $this->lockFile))
    {
      unlink($this->tmp . '/' . $this->lockFile);
    }
  }

  /**
   * Desctructort
   */
  public function __destruct()
  {
    $this->destroyLock();
  }

}

$stdin = explode(' ', trim(fgets(STDIN)));

//We have 3 parameters i assume its post-receive hook
if (count($stdin) == 3)
{
  new GitDeployServer($stdin);
}
//One argv, thats is client side
else if (count($argv) == 1)
{
  new GitDeploy();
}
//Two params, i assume client side with specified repositorty dir
else if (count($argv) == 2)
{
  new GitDeploy($argv[1]);
}
?>