git-deploy
==========

Description
-----------

git-deploy is a deployment tool to allow for quick and easy deployments based on
the changes in a git repository.

git-deploy supports deployment over SSH and FTP/S

Installation
------------

git-deploy requires PHP5.3 >, PHP was chosen becouse this tool was primary created for company where PHP is main
language and use any other language would make maintance and further developement very hard for this company.

Usage
----

In the root directory of your source code, create a <code>deploy.ini</code> file.

Here is a sample code for FTP acces (skip option can be omitted):

    ;target configuration
    [deploy]
    target = 'sftp://sadam@sadam.dyndns-server.com:22/home/sadam/deploy-test'
    deploy = true

    ;Special rights for files relative to git root
    [file_rights]
    bin/git-deploy = 777

Client
------

For deploy from client side, copy `git-deploy` into `/usr/bin` just run `git deploy` from git root directory.

Server
------

For server deployment overwrite `post-receive` in hooks directory, this GIT server implementations are supported:

* [Gitlab](http://gitlab.org/) 

How It Works
------------

`git-deploy` stores file called `REVISION` on your server inside the root path to your application.
This file stores the current revision of your application residing on your server.

When you run a `git deploy`, `git-deploy` downloads the `REVISION` file, and checks to see what
files are different between revisions and either upload the changed files or delete them from the server.
