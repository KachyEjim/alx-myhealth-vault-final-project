from flask import Flask, request, flash, jsonify
import bcrypt, abort
from sqlachemy.exec import SQLAlchemyError


@app.route('/login', methods=['POST'], strict_slashes=True)
def login():
    '''
    collecting user information for authentication and login
    '''
    data = request.get_json()
    # retrieve email and password from the reqest data
    email = data.get('email')
    password = data.get('password')

    # retrieve user from the database
    user = Users.query.filter_by(email=data['email']).first()

    # validating user credentials
    if user and user.check_password_hash(password):
        session['user_id'] = str(user.id)
        flash('You have loggedin successfully', 'success'), 200
        return jsonify({'msg': 'login successful'})

    return jsonify({'Incorrect email or password'}), 401


@app.route('/signup', methods=['POST'])
def signup():
    '''
    route for user registration
    '''
    data = request.get_json()
    Fullname = data.get('Fullname')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')
    gender = data.get('gender')
    address = data.get('address')

    # check if user already exixts in database
    if user in user.query.filter_by(email=data['email']).first():
        flash('user already exist')
        abort(400)

    # create and add user
    hash_password = bcrypt.generate_password_hash(
            password).decode('utf-8')
    new_user = User(Fullname=Fullname,email=email, phone=phone,
                gender=gender, address=address)

    try:
        db.session.add(new_user)
        db.session.commit()
        return jsonify(msg="User registration sucvessfull"), 201

    except SQLAlchemyError as e:
        db.session.rollback()
        return jsonify(msg="User already exists!"), 400
