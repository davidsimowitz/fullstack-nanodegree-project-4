Item Catalog
============================================


Udacity - Full Stack Web Developer Nanodegree
---------------------------------------------
P4: Item Catalog Application (Coordinate App)

This project's main objective was to develop a responsive web application—providing a user registration and authentication system—that displays a list of events that can be browsed by their respective activity. Registered users have the ability to create, modify, and cancel their own events and activities—as well as mark events they are considering or planning on attending. Logged in users also gain the ability to list all the events they are hosting, attending, or considering through navigation buttons located in the user account menu.


Walkthrough
-----------

## Login


### Application Main Page:
![Coordinate app main page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/main-page-1.png)


### Open Navigation Menu:
![User navigation menu](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-navigation-menu-1.png)


### Log In Using Google Sign In:
![User login page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-login-page.png)


### You Successfully Logged In:
![User logged in page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-logged-in-page.png)


### Redirected To Previous Page Upon Logging In:
![Coordinate app main page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/main-page-logged-in.png)


Requirements
------------

+ A Web Browser such as [Chrome](https://www.google.com/chrome/browser/) is installed.
+ [Git](https://git-scm.com/downloads) is installed.
  (Optional, if you wish to clone the project repository.)
+ [VirtualBox](https://www.virtualbox.org/wiki/Downloads) is installed.
+ [Vagrant](https://www.vagrantup.com/downloads.html) is installed.


Update
------
* This web application has been modified to run on an Apache HTTP Server as a WSGI Application.
* Therefore, the following steps in the 'Usage' section should no longer be followed. Updates to the code—such as file path changes—will cause the application to not run properly. Instead, please follow the steps listed in the [Web Application Server](https://github.com/davidsimowitz/fullstack-nanodegree-project-6) repository to run this application.


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
    * Vagrantfile

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

* Accessing API endpoints:

  + For all events and activities:
    * http://localhost:5000/activities/JSON/
  + For all events associated with an individual activity:
    * http://localhost:5000/activities/<int:activity_id>/events/JSON/
  + For one specific event:
    * http://localhost:5000/activities/<int:activity_id>/events/<int:event_id>/JSON/
