# virtualMachineReservationSystem
Mimic virtual machine reservation system

## Description 
A cloud vm pool reservation system miminc using flask,sqlalchemy and sqllite.
Users can checkout out VM as per need basis and checkin back to VM pool.
Admin users can add users delete users and VM,also they can resize the VM pool size.
To keep things simple system is uses simple authentication system of password authetication on  methods POST,DELETE and PATCH.
All get mehods are unautheticated.

## Installtion and Running application.

#### Install required packages
sudo apt-get install python-pip python-virtualenv

#### Create and activate a virtual environment
virtualenv .env
source .env/bin/activate

#### Install Flask and other dependencies.
pip install Flask
pip install -r requirements.txt


#### import postman json



## Main api details in Sequence to run  the app

#### RESET DB OR CREATE IF NOT EXIST 

```http
  GET /truncate_tables
```
Create the database to persist information.


#### RESET DB OR CREATE IF NOT EXIST. 

```http
  POST /user
```
Create users for system.If its first user its marked as Admin and authentication is not required for first user.
from 2nd user onwards rest users are marked with role=user.For role=admin you need to explicitly mention it.
Only user with Admin role can add users.

##### Body for 1st  user:
```json
{
    "name": "user1",
    "email": "user1@gmail.com",
    "password": "user1"
}
```

##### Form second user onwards authentication is manddatory.
```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "name": "user2",
    "email": "user2@gmail.com",
    "password": "user2"
}
```

##### To mark the users as admin use below.
```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "name": "user2",
    "email": "user2@gmail.com",
    "password": "user2",
	"role": "admin"
}
```

#### Create VM resource pool.

```http
  POST /create_resource_pool
```

This post request creates vm pool of size mentioned by admin user.

```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "pool_size": "70"
}
```

#### Resize VM pool size.

```http
  POST /create_resource_pool
```

This post request resizes vm pool to size mentioned by admin user.This can be helpfull and save cost.

```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "pool_size": "10"
}
```

#### Checkout or  borrow VM.

```http
  POST /checkout_vm
```

A normal user or Admin can checkout\borrow VM for his need.

##### Incase if user needs particular VM, then VM's Id must be supplied as below.
```json
{
    "auth": {
        "userid": 2,
        "password": "user2"
    },
    "vmid": 1
}
```
##### Incase if user\admin needs any random VM, do not supply VM's Id.
```json
{
    "auth": {
        "userid": 2,
        "password": "user2"
    }
}
```

#### Check in VM back after use.

```http
  POST /checkin_vm
```

User\Admin can check the vm back to pool by using VM"s id.

```json
{
    "auth": {
        "userid": 2,
        "password": "user2"
    },
    "vmid": 1
}


#### Cleanup\maintenance activity.

```http
  POST /maintenance
```
To bring back VM to pool after cleanup\maintenance activity admin has to use VM's Id.
```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "vmid": 1
}
```
#### Basic Stats

```http
  GET /create_resource_pool/basicstats
```

Admin\User can get access to basic stats.

#### Delete user.

```http
  DELETE /user/id/2
```
Admin user can delete any other user but not self.Authentication is required.

```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    }
}
```

#### Delete VM.

```http
  DELETE /vmdetails/id/5
```
Admin user can delete any other VM.Authentication is required.

```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    }
}
```

#### Update User.

```http
  PATCH /user
```
Admin user can update any other user.Regurlar user can only update his details.Authentication is required.

```json
{
    "auth": {
        "userid": 2,
        "password": "user2"
    },
    "id": 2,
    "name": "user3",
    "email": "user3@gmail.com",
    "password": "user3"
}
```



