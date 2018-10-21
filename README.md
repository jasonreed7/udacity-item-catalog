# Udacity Item Catalog
This is a project for the Udacity Full Stack Nanodegree.

It is an item catalog that allows all users to view categories 
and items, and allows authorized users to create, edit and delete
items. It uses Python 3, Flask and SQLAlchemy.

## Setup
The project runs using [VirtualBox](https://www.virtualbox.org/) 
and [Vagrant](https://www.vagrantup.com/). It builds 
off of the [FSND-Virtual-Machine](https://github.com/udacity/fullstack-nanodegree-vm).

First clone the FSND-Virtual-Machine repo.

Then clone the project code inside of the `vagrant/catalog` 
directory of the `fullstack-nanodegree-vm` directory, then you
can start up the virtual machine from the `vagrant` directory.
```
git clone https://github.com/jasonreed7/udacity-item-catalog.git
vagrant up
vagrant ssh
cd /vagrant/catalog
``` 
If it is your first time running the project, create the database
with:
```
python3 database_setup.py
```
You can add some mock data with:
```
python3 mock_data.py
```
To run the app, 
```
python3 application.py
```

## Pages/ API endpoints for GET requests
Path | Result
---|---
/login | Google login button
/gdisconnect | Logout
/ | Shows categories and 10 most recent items
/catalog | Same as above
/JSON | Shows catalog as JSON
/catalog/JSON | Same as above
/catalog/<category_name>/items | Shows items for a given category
/catalog/<category_name>/items/JSON | Same as above but JSON
/catalog/<category_name>/<item_name> | Shows an item
/catalog/<category_name>/<item_name>/JSON | Same as above but JSON
/catalog/item/new/ | Form to create new item- requires authentication
/catalog/<category_name>/<item_name>/edit | Form to edit an item- requires authorization
/catalog/<category_name>/<item_name>/delete | Page to delete an item- requires authorization

