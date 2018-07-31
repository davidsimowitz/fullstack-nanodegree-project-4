Item Catalog
============================================

Udacity - Full Stack Web Developer Nanodegree
---------------------------------------------
P4: Item Catalog Application 

To develop an application that provides a list of items within a variety of categories as well as provide a user registration and authentication system. Registered users will have the ability to post, edit and delete their own items.


Requirements
------------

+ A Web Browser such as [Chrome](https://www.google.com/chrome/browser/) is installed.
+ [Git](https://git-scm.com/downloads) is installed.
  (Optional, if you wish to clone the project repository.)
+ [VirtualBox](https://www.virtualbox.org/wiki/Downloads) is installed.
+ [Vagrant](https://www.vagrantup.com/downloads.html) is installed.


Usage
-----

* Run the following commands to clone the complete web site.

```bash
$ git clone https://github.com/davidsimowitz/fullstack-nanodegree-project-4.git
```
  + Above command is optional.
  + Alternatively you may download the files into the directory.

```bash
$ cd fullstack-nanodegree-project-4
```
  + Verify the following files/folders are present before continuing:
  (client secret json files will be sent separately for security purposes)
    * app.py
    * client_secret.json
    * fb_client_secret.json
    * models.py
    * populate_events_db.py
    * README.md
    * static
    * templates

* Setup the environment:

  + Run the following command inside the directory containing the Vagrantfile to bring up the Vagrant environment.
```bash
$ vagrant up
```

  + SSH into the machine.
```bash
$ vagrant ssh
```

* Startup the backend for the site:

  + Run the app:
  (after ssh'ing into your vagrant machine)
```bash
$ cd /vagrant
$ python3 app.py
```

* Connect to the frontend:

  + Connect to the [frontend of the site](http://localhost:5000) using your web browser.

