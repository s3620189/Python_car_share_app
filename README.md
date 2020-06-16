# PIoT Assignment 2
Car Share System


## Python Package Dependencies
```
(shell)$ pip install python-dotenv flask flask-mysql requests sphinx google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2 opencv-python face-recognition imutils Flask-SQLAlchemy
```
Note: The package opencv-python has several dependencies from binary libs which vary from system to system, and following lab tutorial instructions should be the way to go.


## Database Initialisation
```
(shell)$ cd <PROJECT_ROOT>/mp
(shell)$ flask init-db
```


## Master Pi Web Service

The programs are located in this directory.
```
(shell)$ cd <PROJECT_ROOT>/mp
```

Several environment variables are defined in .flaskenv, which allow you to turn on/off several functionalities in Master Pi Web Service.
* FLASK_APP is the name/path of the flask factory module which is the startint point of Master Pi Web Service.
* FLASK_ENV switches between different modes; the value "development" is for dev/debug mode. The default is "production" mode.
* UNIT_TEST_DB is to sepcify another database for unit tests.

The file content should be like this, and each variable can be truned off by adding a hash ('#') at the beginning of the line.
```
FLASK_APP=masterpi
#FLASK_ENV=development
#UNIT_TEST_DB=testdb
```

After properly setting the environment variables, start the Master Pi Web Service by this command.
```
(shell)$ flask run --host 0.0.0.0
```


## Master Pi Daemon Service

The Master Pi Daemon Service is situated in the same directory as Master Pi Web Service and can be easily launched by this command.
```
(shell)$ python daemon.py
```


## Agent Pi Application

The Agent Pi Application is put in anther sub-directory; you have to change to that directory start start running it.
```
(shell)$ cd <PROJECT_ROOT>/ap
(shell)$ python agent.py
```
