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



## Create Activity


### Open Navigation Menu After Logging In:
![User navigation menu](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-navigation-menu-2.png)


### Select 'new activity':
![Create activity page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-activity-1.png)


### Enter A Name And Select An Icon:
![Select icon for new activity](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-activity-2.png)


### Submit Your New Activity:
![Submit new activity](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-activity-3.png)


### In The Next Section We'll Walkthrough Creating Events:
![Activity page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-activity-4.png)


### For Now, The Activity Will Be Displayed On The Main Page:
![Coordinate app main page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-activity-5.png)



## Create Event


### Select An Activity After Logging In:
![Coordinate app main page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/main-page-2.png)


### Select 'plan event' From The Navigation Menu:
![User navigation menu](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-navigation-menu-3.png)


### Enter The Event Details And Submit:
![Hosting an event](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-event-1.png)


### Your New Event Has Been Created:
![Event details](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-event-2.png)


### Your Event Is Listed Under The Activity In Which It Was Created:
![Activity page, displaying events associated with it](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/create-event-3.png)


## Update Event
#### * Events can only be updated by the user account that created them.


### You Can Update An Event You Created By Selecting It From Its Activity:
![Select event from activity page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/update-event-1.png)


### Select The Event Again From Its Event Page:
![Click on the event](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/update-event-2.png)


### Select 'update' Once You Have Completed Modifying The Event:
![Click on the event to edit it](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/update-event-3.png)



## Mark Yourself As Attending Or Considering An Event


### Browse Events After Logging In:
![Activity page, displaying events associated with it](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-event-1.png)


### Select An Event You Wish To Attend:
![Selecting an event from an activity page](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-event-2.png)


### Click Either The Check Mark (Attending) Or The Question Mark (Considering) Located Toward The Top Right Of The Event Details:
![Event details](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-event-3.png)


### Your Choice Updates To Green:
![Event has been updated to show that you are attending it](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-event-4.png)


### Events You Are Attending And Considering Will Be Marked By Either A Check Mark Or A Question Mark, Respectively:
![Events you are attending and considering will be marked by either a check mark or a question mark, respectively](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-event-5.png)



## View The Events You Are Attending


### Select 'attending' From The User Navigation Menu While Logged In:
![User navigation menu](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-navigation-menu-4.png)


### The Events You Are Attending Are Now Displayed:
![Attending Events](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-events-1.png)
![Attending Events](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/attending-events-2.png)



## View The Events You Are Considering


### Select 'considering' From The User Navigation Menu While Logged In:
![User navigation menu](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/user-navigation-menu-5.png)


### The Events You Are Considering Are Now Displayed:
![Considering Events](https://github.com/davidsimowitz/fullstack-nanodegree-project-4/blob/master/images/considering-events-1.png)



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
