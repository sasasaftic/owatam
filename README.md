Owatam
=========

Owatam is an open source web analytic tool.


Version
----

1.0

Installation
--------------
Launch an Ubuntu 12.04 server (it's tested on ubuntu but it should work anywhere where django is supported) and login to it as a user that has full sudo privileges.

```sh
sudo apt-get update -y
sudo apt-get upgrade -y
sudo apt-get install python-pip
sudo apt-get install git
reboot
```

##### Git checkout

Go to desired folder

```sh
cd your_folder # replace with actual folder name
git clone
cd owatam
sudo pip install -r requirements.txt

```

##### Start development server

```sh
python manage.py runserver 0.0.0.0:8000

```

License
----

MIT


**Free Software!!**

