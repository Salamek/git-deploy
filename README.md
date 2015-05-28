# git-deploy

## Description

git-deploy is a deployment tool to allow for quick and easy deployments based on
the changes in a git repository, from git server on `git push` command, by adding as remote hook in github/gitlab or manualy from git repo :

git-deploy supports deployment over SSH and FTP/S

## Installation

### Debian/Ubuntu (DEB):

Add new repository by running this command: `sudo echo "deb http://apt.salamek.cz debian/" >> /etc/apt/sources.list` then just run `sudo apt-get update && sudo apt-get install git-deploy`

### Archlinux:

For archlinux you can install package from AUR https://aur.archlinux.org/packages/git-deploy/

### Fedora/Rhel (RPM):

## Usage

### Manual run

Just run `git-deploy` in your git repo root

### On push as `post-receive`

Just simlink `/usr/bin/git-deploy` AS `post-receive` in hooks dir in repo you want to deploy

### On push using GitHub or GitLab

You must run git-deploy as daemon, first please edit file in `/etc/git-deploy/git-deploy.cfg` and make it suits your needs (config values should be Self-explanatory)

Then just start `git-deploy` service and add it to your init if you want (for autostart on boot)

#### GitHub

To deploy on `git push` to GitHub repo add a new webhook (Repo detail->Settings->Webhooks & Service->Add webhook) with this format of url : `http://[servername]:[port]/deploy.json` triggered on push

#### GitLab

It's same as GitHub ;-)


## Config file in deployed repo

In the root directory of your source code, create a <code>deploy.py</code> file (deploy.ini is deprecated and its support will be removed in next release).

Here is a sample code for FTP acces (port can be omitted):

    CONFIG = {
    # Configure target or multiple targets
      'targets': [
        {
          # Target uri, supported protocols are sftp, ftp, ftps format is standard URI
          'uri': 'ftp://user:password@example.com/',

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

## How It Works

`git-deploy` stores file called `REVISION` on your server inside the root path to your application.
This file stores the current revision of your application residing on your server.

When you run a `git deploy`, `git-deploy` downloads the `REVISION` file, and checks to see what
files are different between revisions and either upload the changed files or delete them from the server.
