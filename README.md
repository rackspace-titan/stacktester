# Stacktester
***

### Testing an OpenStack Installation (For Developers)

#### Get the Code
    $ git clone git://github.com/rackspace-titan/stacktester.git
    $ cd stacktester

#### Edit/Review the Test Configuration
    $ vim etc/stacktester.cfg

#### Setup the Virtual Environment
    $ tools/venv_build

#### Run the Test Suite
    $ bin/venv_stacktester --verbose


<br/>
<br/>


### Testing an OpenStack Installation (For End-Users)

#### Install
    $ pip install stacktester

#### Edit/Review the Test Configuration
    $ vim /etc/stacktester.cfg

#### Run the Test Suite
    $ stacktester --verbose


