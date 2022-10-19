from flask_login import UserMixin

from db import get_db
from data import mongo
import pymongo

class User(UserMixin):
    def __init__(self, id_, name, email, profile_pic):
        self.id = id_
        self.name = name
        self.email = email
        self.profile_pic = profile_pic

    @staticmethod
    def get(user_id):
        # db = get_db()
        # user = db.execute(
        #     "SELECT * FROM user WHERE id = ?", (user_id,)
        # ).fetchone()
        # if not user:
        #     return None

        mydb = mongo.get_mongo_connection()
        user_col = mydb["users"]
        user = user_col.find_one({"id": user_id})
        if user is None:
            return None

        user = User(id_=user["id"], name=user["name"], email=user["email"], profile_pic=user["profile_pic"])

        return user

    @staticmethod
    def create(id_, name, email, profile_pic):
        # db = get_db()
        # db.execute(
        #     "INSERT INTO user (id, name, email, profile_pic) "
        #     "VALUES (?, ?, ?, ?)",
        #     (id_, name, email, profile_pic),
        # )
        # db.commit()
        mydb = mongo.get_mongo_connection()
        user_col = mydb["users"]
        user = user_col.insert_one({"id": id_, "name": name, "email": email, "profile_pic": profile_pic})