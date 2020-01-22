# git-deploy

[![Donate](https://img.shields.io/badge/Donate-PayPal-green.svg)](https://www.paypal.com/cgi-bin/webscr?cmd=_donations&business=D8LQ4XTBLV3C4&lc=CZ&item_number=Salamekgit-deploy&currency_code=EUR)

## Description

git-deploy is a deployment tool to allow for quick and easy deployments based on
the changes in a git repository, from git server on `git push` command, by adding as remote hook in github/gitlab or manualy from git repo :

git-deploy supports deployment over SSH and FTP/S

## Installation

### Debian/Ubuntu (DEB):

Add new repository and install by running this commands: 

```bash
wget -O - https://repository.salamek.cz/deb/salamek.gpg.key|sudo apt-key add -
echo "deb     https://repository.salamek.cz/deb/pub all main" | sudo tee /etc/apt/sources.list.d/salamek.cz.list
sudo apt-get update && sudo apt-get install git-deploy
```

### Archlinux:

For archlinux you can install package from AUR https://aur.archlinux.org/packages/git-deploy/

### Fedora/Rhel (RPM):

## Usage

### Manual run

Just run `git-deploy` in your git repo root

### On push as `post-receive`

Just simlink `/usr/bin/git-deploy` AS `post-receive` in hooks dir in repo you want to deploy

### On push using GitHub or GitLab

You must run git-deploy as daemon, first please edit file in `/etc/git-deploy/config.py` (git-deploy.cfg is deprecated and will be migrated to new version) and make it suits your needs (config values should be Self-explanatory)

Then just start `git-deploy` service and add it to your init if you want (for autostart on boot)

#### GitHub

To deploy on `git push` to GitHub repo add a new webhook (Repo detail->Settings->Webhooks & Service->Add webhook) with this format of url : `http://[servername]:[port]/deploy.json` triggered on push

#### GitLab

It's same as GitHub ;-)


## Config file in deployed repo

In the root directory of your source code, create a <code>deploy.py</code> file (deploy.ini is deprecated and its support will be removed in next release).

Here is a sample code for FTP acces (port can be omitted):
```python
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
```
## How It Works

`git-deploy` stores file called `REVISION` on your server inside the root path to your application.
This file stores the current revision of your application residing on your server.

When you run a `git deploy`, `git-deploy` downloads the `REVISION` file, and checks to see what
files are different between revisions and either upload the changed files or delete them from the server.
