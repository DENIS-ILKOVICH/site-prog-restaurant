import random

from flask_login import UserMixin
from flask import *


class UserLogin(UserMixin):
    def fromDB(self, user_id, db):
        self.__user = db.getuser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['id'])

    def get_name(self):
        return str(self.__user['name']) if self.__user else 'No name'

    def get_mail(self):
        return str(self.__user['email']) if self.__user else 'No email'

    def get_avatar(self):
        return self.__user['avatar'] if self.__user else 'No avatar'

    def get_user(self):
        return self.__user