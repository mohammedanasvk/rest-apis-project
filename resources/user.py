from sqlite3 import IntegrityError
from flask.views import MethodView
from flask_smorest import Blueprint,abort
from flask import current_app
from db import db
from model import UserModel
from schemas import UserSchema, UserRegisterSchema
from sqlalchemy.exc import SQLAlchemyError
from flask_jwt_extended import create_access_token, jwt_required, get_jwt, create_refresh_token,get_jwt_identity
from blocklist import BLOCKLIST
import requests
import os
from sqlalchemy import or_
from tasks import send_user_registration_email

from passlib.hash import pbkdf2_sha256

blp=Blueprint("users",__name__,description="operation on users")

@blp.route("/register")
class UserRegister(MethodView):
    @blp.arguments(UserRegisterSchema)
    def post(self,user_data):

        user=UserModel(username=user_data["username"],email=user_data["email"],password=pbkdf2_sha256.hash(user_data["password"]))

        try:
            db.session.add(user)
            db.session.commit()

            current_app.queue.enqueue(send_user_registration_email,user.email,user.username)
        except IntegrityError:
            abort(409,"A user with given username or email already exists")
        
        return {"message":"User created successfully"},201
    
@blp.route("/user/<int:user_id>")
class User(MethodView):
    @blp.response(200,UserSchema)
    def get(self,user_id):
        user=UserModel.query.get_or_404(user_id)
        return user
        
    def delete(self,user_id):
        user=UserModel.query.get_or_404(user_id)
        db.session.delete(user)
        db.session.commit()
        return {"message":"User deleted"},200

@blp.route("/login")
class UserLogin(MethodView):
    @blp.arguments(UserSchema)
    def post(self,user_data):
        user=UserModel.query.filter(UserModel.username==user_data["username"]).first()

        if user and pbkdf2_sha256.verify(user_data["password"],user.password):
            access_token=create_access_token(identity=user.id,fresh=True) 
            refresh_token=create_refresh_token(identity=user.id)
            return {"access_token":access_token, "refresh_token":refresh_token}
        
        abort(401,"Invalid creditials")

@blp.route("/refresh")
class TokenRefresh(MethodView):
    @jwt_required(refresh=True)
    def post(self):
        current_user=get_jwt_identity()
        new_token=create_access_token(id=current_user,fresh=False)
        return {"access_token":new_token}

@blp.route("/logout")
class UserLogout(MethodView):
    @jwt_required()
    def post(self):
        jti=get_jwt()["jti"]
        BLOCKLIST.add(jti)
        return {"message":"Successfully logget out"}