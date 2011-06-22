Stacktester
===========


### Testing Stacktester
Developers wishing to run `stacktester` internal unittests should run:
> $ ./setup.py test


### Testing an OpenStack Installation (For Developers)

#### Get the Code
> $ git clone git://github.com/rackspace-titan/stacktester.git
> $ cd stacktester

#### Setup the Virtual Environment
> $ python setup.py venv

#### Edit/Review the Test Configuration
> $ vim etc/stacktester.cfg

#### Run the Test Suite
> $ bin/stacktester --venv --verbose


### Testing an OpenStack Installation (For End-Users)

#### Install
> $ pip install stacktester

#### Edit/Review the Test Configuration
> $ vim etc/stacktester.cfg

#### Run the Test Suite
> $ stacktester --verbose


