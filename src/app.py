from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import random, socket, struct
from faker import Faker
from sqlalchemy import desc

VM_TYPES = {
    "small": {
        "cpu": "2 core",
        "memory": "8 GB"
    },
    "medium": {
        "cpu": "4 core",
        "memory": "16 GB"
    },
    "large": {
        "cpu": "8 core",
        "memory": "64 GB"
    },
    "xlarge": {
        "cpu": "2 x 8 core",
        "memory": "128 GB"
    }
}

faker = Faker()
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
# app.config['SQLALCHEMY_ECHO'] = True


db = SQLAlchemy(app)


# Models section

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    role = db.Column(db.String(50), default="user")
    date_joined = db.Column(db.Date, default=datetime.utcnow)


class Resouce(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    vm_name = db.Column(db.String(50), default="null")
    vm_type = db.Column(db.String(50), default="null")
    vm_ip = db.Column(db.String(50), default="null")
    vm_Status = db.Column(db.String(50), default="running")
    vm_map_to = db.Column(db.String(50), default="idle")
    date_created = db.Column(db.Date, default=datetime.utcnow)


class Pool(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pool_size = db.Column(db.String)


# Drop Tables
# db.drop_all()
# exit(0)
# Create tables if not exist
# db.create_all()


# functions section

def check_for_auth_parmeters(content):
    if content.get('auth') is not None and content.get('auth').get('userid') is not None and content.get('auth').get(
            'password') is not None:
        return True
    else:
        return False


# generate Random hostname,IP,VM_Type
def get_random_vm_details():
    key, value = random.choice(list(VM_TYPES.items()))
    ip = socket.inet_ntoa(struct.pack('>I', random.randint(1, 0xffffffff)))
    hostname = faker.hostname()
    return key, ip, hostname


# Save Records for various Models
def save_records(tblObj, content):
    str = ""
    for key in content.keys():
        if key == "auth":
            continue
        if tblObj.__dict__[key]:
            str = str + key + "=content['{}'],".format(key)
        else:
            return jsonify({"message": "Invalid key -" + key}), 400
    str = str.rstrip(str[-1])
    res = eval(tblObj.__name__ + "(" + str + ")")
    db.session.add(res)
    db.session.commit()
    return jsonify({"message": "User Created."}), 201


# VM pool resize calculation and update
def syncPoolSize(expected_count):
    if Pool.query.count() == 0:
        content = {"pool_size": expected_count}
        return create_resource_pool(content)
    current_pool_size = Pool.query.all()[0].pool_size
    unused_vm_count = Resouce.query.filter_by(vm_map_to="idle").count()
    used_vm = int(current_pool_size) - int(unused_vm_count)
    if used_vm > int(expected_count):
        return jsonify({"message": "Cannot resize as , currently in used VM > expected pool resize value"}), 400
    elif int(current_pool_size) > int(expected_count):
        x = db.session.query(Resouce).filter_by(vm_map_to='idle').order_by(desc('id')).all()
        extra_resources = int(current_pool_size) - int(expected_count)
        for i in range(0, extra_resources):
            z = Resouce.query.filter_by(id=str(x[i].id)).delete()
            db.session.commit()
        poolobj = Pool.query.filter_by(id=1).first()
        poolobj.pool_size = int(expected_count);
        db.session.commit()
        return jsonify({"message": "Pool size updated successfully"}), 200
    elif int(expected_count) > int(current_pool_size):
        resultlist = []
        start = int(current_pool_size) + 1
        stop = (int(expected_count) - int(current_pool_size))
        print(start, stop)
        for count in range(start, start + stop):
            tuple = get_random_vm_details()
            hostname = {"vm_type": tuple[0], "vm_ip": tuple[1], "vm_name": tuple[2]}
            resultlist = save_records(Resouce, hostname)
        poolobj = Pool.query.filter_by(id=1).first()
        poolobj.pool_size = int(expected_count);
        db.session.commit()
        return jsonify({"message": "Pool size updated successfully"}), 200
    else:
        return jsonify({"message": "Nothing to Update"}), 200


# api Section

# Truncate Tables for fresh load
@app.route("/truncate_tables")
def truncate_tables():
    db.drop_all()
    db.create_all()
    return jsonify({"message": "Tables Created"}), 201


# Get VM Pool current Size
@app.route("/vmpoolsize")
def poolsize():
    if Pool.query.count() > 0:
        return jsonify({"vm pool size": Pool.query.all()[0].pool_size}), 200
    else:
        return jsonify({"vm pool size": "0"}), 200


@app.route("/vmdetails")
@app.route("/vmdetails/id/<id>", methods=['GET', 'DELETE'])
@app.route("/vmdetails/type/<type>")
@app.route("/vmdetails/maped_to/<user>")
@app.route("/vmdetails/status/<status>")
@app.route("/vmdetails/types/<types>")
def vmdetails(id=None, type=None, user=None, status=None, types=None):
    if request.method == "DELETE":
        content = request.json
        if not check_for_auth_parmeters(content):
            return jsonify({"message": "auth parameters missing"}), 400
        if User.query.filter_by(id=content['auth'].get("userid")).count() > 0:
            user = User.query.filter_by(id=content['auth'].get("userid")).first()
        else:
            return jsonify({"message": "Invalid user."}), 400

        if user.password == content['auth'].get("password") and user.role.lower() == "admin":
            if Resouce.query.filter_by(id=id).count() > 0:
                resource = Resouce.query.filter_by(id=id).first()
            else:
                return jsonify({"message": "Invalid VM."}), 400
            if resource.vm_map_to == "idle" or resource.vm_map_to == "maintenance":
                resource = Resouce.query.filter_by(id=id).delete()
                db.session.commit()
                current_pool_size = Pool.query.all()[0].pool_size
                pool = Pool.query.filter_by(id=1).first()
                pool.pool_size = int(current_pool_size) - 1
                db.session.commit()
                return jsonify({"Message": "VM deleted"}), 200
            else:
                return jsonify({"Message": "Cannot delete VM which is use."}), 401
        else:
            return jsonify({"Message": "Authentication or Authorization failed"}), 401
    else:
        resources = ""
        main_dict = {}
        subdict = {}
        if types is not None:
            main_dict["VM_Types"] = VM_TYPES
            return jsonify(main_dict), 200
        if id is not None:
            if Resouce.query.filter_by(id=id).count() > 0:
                resources = Resouce.query.filter_by(id=id).all()
            else:
                return jsonify({"VM_details": "[]"}), 200
        elif type is not None:
            if Resouce.query.filter_by(vm_type=type.lower()).count() > 0:
                resources = Resouce.query.filter_by(vm_type=type.lower()).all()
            else:
                return jsonify({"VM_details": "[]"}), 200
        elif user is not None:
            if Resouce.query.filter_by(vm_map_to=user).count() > 0:
                resources = Resouce.query.filter_by(vm_map_to=user).all()
            else:
                return jsonify({"VM_details": ""}), 200
        elif status is not None:
            if Resouce.query.filter_by(vm_Status=status.lower()).count() > 0:
                resources = Resouce.query.filter_by(vm_Status=status.lower()).all()
            else:
                return jsonify({"VM_details": "[]"}), 200
        else:
            if Resouce.query.count() > 0:
                resources = Resouce.query.all()
            else:
                return jsonify({"VM_details": "[]"}), 200
        for resource in resources:
            subdict[resource.__dict__["id"]] = {"id": resource.__dict__["id"], "vm_name": resource.__dict__["vm_name"],
                                                "vm_type": resource.__dict__["vm_type"],
                                                "vm_type": resource.__dict__["vm_type"],
                                                "vm_ip": resource.__dict__["vm_ip"],
                                                "vm_Status": resource.__dict__["vm_Status"],
                                                "vm_map_to": resource.__dict__["vm_map_to"],
                                                "date_created": resource.__dict__["date_created"]}

    main_dict["VM_details"] = subdict
    print(main_dict)
    return jsonify(main_dict), 200


# resize VM pool
@app.route("/resizevmpool", methods=['POST'])
def resizevmpool():
    content = request.json
    if not check_for_auth_parmeters(content):
        return jsonify({"message": "auth parameters missing"}), 400
    if User.query.count() == 0:
        return jsonify({"message": "Please create user first."}), 400
    if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
        return jsonify({"message": "Invalid user"}), 400
    user = User.query.filter_by(id=content['auth'].get("userid")).first()
    if user.password == content['auth'].get("password") and user.role.lower() == "admin":
        pool_size = content['pool_size']
        output = syncPoolSize(pool_size)
        return output[0], output[1]
    else:
        return jsonify({"Message": "Authentication or Authorization failed"}), 401


# USER MANAGEMENT
@app.route("/user", methods=['POST', 'GET', 'PATCH'])
@app.route("/user/id/<id>", methods=['GET', 'DELETE'])
@app.route("/user/email/<email>")
def user(id=None, email=None):
    if request.method == "POST":
        content = request.json

        if User.query.count() == 0:
            content["role"] = "admin"
            output = save_records(User, content)
            return output[0], output[1]
        else:
            if not check_for_auth_parmeters(content):
                return jsonify({"message": "auth parameters missing"}), 400
            user = User.query.filter_by(id=content['auth'].get("userid")).first()
            if user.password == content['auth'].get("password") and user.role.lower() == "admin":
                if User.query.filter_by(email=content['email']).count() == 0:
                    output = save_records(User, content)
                    return output[0], output[1]
                else:
                    return jsonify({"message": "User with same email already exist,User is not created."}), 400
            else:
                return jsonify({"Message": "Authentication or Authorization failed"}), 401
    elif request.method == "GET":
        resources = ""
        main_dict = {}
        subdict = {}
        if id is not None:
            if User.query.filter_by(id=id).count() > 0:
                resources = User.query.filter_by(id=id).all()
            else:
                return jsonify({"User_Details": "[]"}), 200
        elif email is not None:
            if User.query.filter_by(email=email).count() > 0:
                resources = User.query.filter_by(email=email).all()
            else:
                return jsonify({"User_Details": "[]"}), 200
        else:
            if User.query.count() > 0:
                resources = User.query.all()
            else:
                return jsonify({"User_Details": "[]"}), 200
        for resource in resources:
            subdict[resource.__dict__["id"]] = {"id": resource.__dict__["id"], "name": resource.__dict__["name"],
                                                "email": resource.__dict__["email"]}
        main_dict["User_Details"] = subdict
        print(main_dict)
        return jsonify(main_dict), 200
    elif request.method == "PATCH":
        content = request.json
        if not check_for_auth_parmeters(content):
            return jsonify({"message": "auth parameters missing"}), 400
        if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
            return jsonify({"message": "Authentication or Authorization failed"}), 400
        user = User.query.filter_by(id=content['auth'].get("userid")).first()
        if (user.password == content['auth'].get("password") and user.role.lower() == "admin") or (
                user.password == content['auth'].get("password") and content['auth'].get("userid") == content["id"]):
            if User.query.filter_by(id=content['id']).count() == 0:
                return jsonify({"message": "The user with Id" + id + " not found"}), 400
            if content.get('email') is not None:
                user = User.query.filter_by(id=content['id']).first()
                user.email = content['email']
            if content.get('name') is not None:
                user = User.query.filter_by(id=content['id']).first()
                user.name = content['name']
            if content.get('password') is not None:
                user = User.query.filter_by(id=content['id']).first()
                user.password = content['password']
            db.session.commit()
            return jsonify({"Message": "Update done"}), 200
        else:
            return jsonify({"Message": "Authentication or Authorization failed"}), 400
    elif request.method == "DELETE":
        content = request.json
        if not check_for_auth_parmeters(content):
            return jsonify({"message": "auth parameters missing"}), 400
        if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
            return jsonify({"message": "Invalid user"}), 400
        user = User.query.filter_by(id=content['auth'].get("userid")).first()
        if user.password == content['auth'].get("password") and user.role.lower() == "admin":
            if str(id).strip() == str(content['auth'].get("userid")).strip():
                return jsonify({"message": "User self delete not allowed"}), 400
            user = User.query.filter_by(id=id).delete()
            db.session.commit()
            return jsonify({"Message": "Record Deleted"}), 200
        else:
            return jsonify({"Message": "Authentication or Authorization failed"}), 401
    else:
        return jsonify({"Message": "Invalid Method/request"}), 400


# Create VM Pool
@app.route("/create_resource_pool", methods=['POST'])
@app.route("/create_resource_pool/basicstats")
def create_resource_pool(inputcontent=None):
    # Update Pool Size
    if request.method == "POST":
        if request.json is not None:
            content = request.json
            if not check_for_auth_parmeters(content):
                return jsonify({"message": "auth parameters missing"}), 400
            if User.query.count() == 0:
                return jsonify({"message": "Please create user first."}), 400
            if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
                return jsonify({"message": "Invalid user"}), 400
            user = User.query.filter_by(id=content['auth'].get("userid")).first()
            if user.password == content['auth'].get("password") and user.role.lower() == "admin":
                if Pool.query.count() == 1:
                    x = db.session.query(Pool).delete()
                    db.session.commit()
                    x = db.session.query(Resouce).delete()
                    db.session.commit()
                    save_records(Pool, content)
                    # Create Pool Resources
                    resultlist = []
                    for count in range(1, int(content['pool_size']) + 1):
                        tuple = get_random_vm_details()
                        hostname = {"vm_type": tuple[0], "vm_ip": tuple[1], "vm_name": tuple[2]}
                        resultlist = save_records(Resouce, hostname)
                    return dict(message="Pool resources recreated."), 201
            else:
                return jsonify({"Message": "Authentication or Authorization failed"}), 401
        else:
            content = inputcontent
        save_records(Pool, content)
        # Create Pool Resources
        resultlist = []
        for count in range(1, int(content['pool_size']) + 1):
            tuple = get_random_vm_details()
            hostname = {"vm_type": tuple[0], "vm_ip": tuple[1], "vm_name": tuple[2]}
            resultlist = save_records(Resouce, hostname)
        return dict(message="Resources Created."), 201

    elif request.method == "GET":
        pool=Pool.query.first();
        poolsize=pool.pool_size
        free_VM_in_pool=Resouce.query.filter_by(vm_map_to='idle').count()
        VM_under_maintenance_in_Pool=Resouce.query.filter_by(vm_map_to='maintenance').count()
        allocated_VM_in_Pool = int(poolsize)-(int(free_VM_in_pool)+int(VM_under_maintenance_in_Pool))
        dict1={}
        final_dict={}
        dict1['total_VM_count_in_pool']=poolsize
        dict1['free_VM_in_pool']=free_VM_in_pool
        dict1['VM_under_maintenance_in_Pool']=VM_under_maintenance_in_Pool
        dict1['allocated_VM_in_Pool']=allocated_VM_in_Pool
        final_dict['Pool Stats']=dict1
        return final_dict,200
    else:
        return dict(message="Unknown Method."), 400

@app.route("/checkout_vm", methods=['POST'])
@app.route("/checkout_vm/user/<userid>", methods=['GET'])
@app.route("/checkout_vm/vm/<vmid>", methods=['GET'])
def checkout_vm(userid=None, vmid=None):
    if request.method == "POST":
        content = request.json
        if not check_for_auth_parmeters(content):
            return jsonify({"message": "auth parameters missing"}), 400
        if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
            return jsonify({"message": "Invalid User"}), 400
        if content.get('vmid') is None:
            if Resouce.query.filter_by(vm_map_to="idle").count() > 0:
                r1 = Resouce.query.filter_by(vm_map_to="idle").first()
                content['vmid'] = r1.id
            else:
                return jsonify(
                    {"message": "No VM's are available in pool for checkout.Please retry after some time."}), 400
        if Resouce.query.filter_by(id=content['vmid']).count() == 0:
            return jsonify({"message": "Invalid VM"}), 400
        user = User.query.filter_by(id=content['auth'].get("userid")).first()
        resource = Resouce.query.filter_by(id=content['vmid']).first()
        if resource.vm_map_to != "idle":
            return jsonify({"message": "VM not available for use,Please select another VM."}), 400
        if user.password == content['auth'].get("password"):
            resource.vm_map_to = user.email;
            db.session.commit()
            result = {"message": "VM checkout complete.", "VM Details":
                {"vm-Id": resource.id, "hostname": resource.vm_name, "ip-address": resource.vm_ip,
                 "vm type": resource.vm_type},
                      "User Details": {"user-Id": user.id, "User-name": user.name, "user-email": user.email}
                      }
            return jsonify(result), 201
        return jsonify({"message": "Unauthorized! Authentication failed.Or you tried to check out pre owned VM. "}), 401
    elif request.method == "GET":
        if userid is not None:
            if User.query.filter_by(id=userid).count() == 0:
                return jsonify({"VM owned by user": "[]"}), 400
            user = User.query.filter_by(id=userid).first()
            if Resouce.query.filter_by(vm_map_to=user.email).count() == 0:
                return jsonify({"VM owned by user": "[]"}), 400
            resource = Resouce.query.filter_by(vm_map_to=user.email).first()
            result = {"VM owned by user":
                          {"vm-Id": resource.id, "hostname": resource.vm_name, "ip-address": resource.vm_ip,
                           "vm type": resource.vm_type},
                      "User Details": {"user-Id": user.id, "User-name": user.name, "user-email": user.email}
                      }
            return jsonify(result), 201
        if vmid is not None:
            if Resouce.query.filter_by(id=vmid).count() == 0:
                return jsonify({"VM owner Details": "[]"}), 400
            resource = Resouce.query.filter_by(id=vmid).first()
            if User.query.filter_by(email=resource.vm_map_to).count() == 0:
                return jsonify({"VM owner Details": "[]"}), 400
            user = User.query.filter_by(email=resource.vm_map_to).first()
            result = {"VM owner Details":
                          {"vm-Id": resource.id, "hostname": resource.vm_name, "ip-address": resource.vm_ip,
                           "vm type": resource.vm_type},
                      "User Details": {"user-Id": user.id, "User-name": user.name, "user-email": user.email}
                      }
            return jsonify(result), 201


@app.route("/checkin_vm", methods=['POST'])
def checkin_vm():
    if request.method == "POST":
        content = request.json
        if not check_for_auth_parmeters(content):
            return jsonify({"message": "auth parameters missing"}), 400
        if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
            return jsonify({"message": "Invalid User"}), 400
        if Resouce.query.filter_by(id=content['vmid']).count() == 0:
            return jsonify({"message": "Invalid VM"}), 400
        user = User.query.filter_by(id=content['auth'].get("userid")).first()
        resource = Resouce.query.filter_by(id=content['vmid']).first()
        if user.password == content['auth'].get("password") and resource.vm_map_to == user.email:
            resource.vm_map_to = "maintenance";
            db.session.commit()
            result = {"message": "VM checkin complete.", "VM Details":
                {"vm-Id": resource.id, "hostname": resource.vm_name, "ip-address": resource.vm_ip,
                 "vm type": resource.vm_type, "VM tagged to": "maintenance"}
                      }
            return jsonify(result), 201
        else:
            return jsonify({
                "message": "Unauthorized! Only Owner can check in the VM back to pool.Or you tried to check in "
                           "someone else VM. "}), 401


@app.route("/maintenance", methods=['POST', 'GET'])
def maintenance():
    if request.method == "POST":
        content = request.json
        if not check_for_auth_parmeters(content):
            return jsonify({"message": "auth parameters missing"}), 400
        if User.query.filter_by(id=content['auth'].get("userid")).count() == 0:
            return jsonify({"message": "Invalid User"}), 400
        if Resouce.query.filter_by(id=content['vmid']).count() == 0:
            return jsonify({"message": "Invalid VM"}), 400
        user = User.query.filter_by(id=content['auth'].get("userid")).first()
        resource = Resouce.query.filter_by(id=content['vmid']).first()

        if str(user.password).strip() == str(content['auth'].get("password")).strip() and str(
                user.role).lower().strip() == "admin" and str(resource.vm_map_to).lower().strip() == "maintenance":
            resource.vm_map_to = "idle";
            db.session.commit()
            result = {"message": "VM ready to use and available in pool.", "VM Details":
                {"vm-Id": resource.id, "hostname": resource.vm_name, "ip-address": resource.vm_ip,
                 "vm type": resource.vm_type}
                      }
            return jsonify(result), 201
        else:
            return jsonify({"message": "Unauthorized! Only Admin can bring VM back to pool.Or you tried to checkin VM "
                                       "which is not under maintenance."}), 401
    if request.method == "GET":
        main_dict = {}
        subdict = {}
        if Resouce.query.filter_by(vm_map_to='maintenance').count() == 0:
            return jsonify({"Maintenance_VM_details": "[]"}), 400
        resources = Resouce.query.filter_by(vm_map_to='maintenance').all()
        for resource in resources:
            subdict[resource.__dict__["id"]] = {"id": resource.__dict__["id"], "vm_name": resource.__dict__["vm_name"],
                                                "vm_type": resource.__dict__["vm_type"],
                                                "vm_type": resource.__dict__["vm_type"],
                                                "vm_ip": resource.__dict__["vm_ip"],
                                                "vm_Status": resource.__dict__["vm_Status"],
                                                "vm_map_to": resource.__dict__["vm_map_to"],
                                                "date_created": resource.__dict__["date_created"]}
        main_dict["Maintenance_VM_details"] = subdict
        print(main_dict)
        return jsonify(main_dict), 200


if __name__ == '__main__':
    app.run(debug=True)
