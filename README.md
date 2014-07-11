# git-deploy

## Description

git-deploy is a deployment tool to allow for quick and easy deployments based on
the changes in a git repository, from git server on `git push` command, by adding as remote hook in github/gitlab or manualy from git repo :

![Animation of active deploy](https://gist.github.com/Salamek/6412607/raw/a8942ce9a0b6d638a70caf9618e97cd8b31f87b1/anim.gif)

git-deploy supports deployment over SSH and FTP/S

## Installation

### Debian/Ubuntu (DEB):

### Archlinux:

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

In the root directory of your source code, create a <code>deploy.ini</code> file.

Here is a sample code for FTP acces (port can be omitted):

    ;target configuration
    [deploy]    
    ;;protocols can be sftp for SSH (SCP), ftp or ftps for FTP or secure FTP
    target = ftp://user:password@example.com:21/path/to/deploy
    ;or private key auth over SSH :
    ;target = sftp://user@example.com:22/path/to/deploy
    ;;deploy a project or not
    deploy = true
    ;Optional, Special rights for files relative to git root
    [file_rights]
    dir/file/* = 777
    dir/file = 775

## How It Works

`git-deploy` stores file called `REVISION` on your server inside the root path to your application.
This file stores the current revision of your application residing on your server.

When you run a `git deploy`, `git-deploy` downloads the `REVISION` file, and checks to see what
files are different between revisions and either upload the changed files or delete them from the server.
