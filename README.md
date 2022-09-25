# virtualMachineReservationSystem
Mimic virtual machine reservation system

## Description 
A cloud vm pool reservation system miminc using flask,sqlalchemy and sqllite.
Users can checkout VM as per need basis and checkin back to VM pool.
Admin users can add users ,delete users and delete VM,also they can resize the VM pool size.
To keep things simple, system uses simple authentication system using passwords for methods POST,DELETE and PATCH.
All get mehods are unauthenticated.

----------------------------------------------------------------------------------------------------------------------
## Installtion and Running application.

#### Install required packages
```bash
sudo apt-get install python-pip python-virtualenv
```
#### Create and activate a virtual environment
```bash
virtualenv .env
source .env/bin/activate
```

#### Install Flask and other dependencies.
```bash
pip install Flask
pip install -r requirements.txt
```

#### Install gunicorn
```bash
pip install gunicorn
```

#### Let’s start a Gunicorn process to serve your Flask app.
```bash
cd src
gunicorn app:app -b localhost:8443 &
```

#### import postman json

----------------------------------------------------------------------------------------------------------------------

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
Creates users for system.If its first user user is marked as Admin and authentication is not required for first user.
From 2nd user onwards all new users are marked with role=user by default.For Admin role you need to explicitly mention role=admin.
Only user with admin role can add users.

##### Body for 1st  user:
```json
{
    "name": "user1",
    "email": "user1@email.com",
    "password": "user1"
}
```

##### Form second user onwards authentication is mandatory.
```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "name": "user2",
    "email": "user2@email.com",
    "password": "user2"
}
```

##### To mark the users as admin use below *note role=admin.
```json
{
    "auth": {
        "userid": 1,
        "password": "user1"
    },
    "name": "user2",
    "email": "user2@email.com",
    "password": "user2",
	"role": "admin"
}
```

#### Create VM resource pool.

```http
  POST /create_resource_pool
```

Creates vm resource pool of size provided by admin user.

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

Resizes vm pool to size mentioned by admin user.This can be helpful to save cost.

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
Admin user can delete any other user but not self.authentication is required.

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
Admin user can delete any other VM.authentication is required.

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
Admin user can update any other user.Regurlar user can only update his details.authentication is required.

```json
{
    "auth": {
        "userid": 2,
        "password": "user2"
    },
    "id": 2,
    "name": "user3",
    "email": "user3@email.com",
    "password": "user3"
}
```

#### Get VM details by status

```http
  GET /vmdetails/status/rUnning
```


#### Get VM details allocated to user by email id.

```http
  GET /vmdetails/maped_to/user2@email.com
```

#### Get VM details VM id.

```http
  GET /vmdetails/id/2
```

#### Get ALL VM details.

```http
  GET /vmdetails
```

#### Get VM Types.

```http
  GET /vmdetails/types/all
```

#### Get VM Details by type.

```http
  GET /vmdetails/type/small
```

#### Get all User Details by type.

```http
  GET /user
```

#### Get User Details by user id.

```http
  GET /user/id/1
```

#### Get User Details by email.

```http
  GET /user/email/user2@email.com
```

#### Get List of VM owned by user.

```http
  GET /checkout_vm/user/2
```

#### Get List of VM under maintenance.

```http
  GET /maintenance
```


#### Get VM resource pool size.

```http
  GET /vmpoolsize
```

#### Get VM resource pool size.

```http
  GET /vmpoolsize
```
