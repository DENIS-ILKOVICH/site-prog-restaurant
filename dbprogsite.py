import math
import time
import re
from datetime import datetime

from flask import url_for
import random


class MenuItem:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def dishes_show(self):
        try:
            self.__cur.execute("SELECT COUNT(*) AS count FROM dishes;")
            result = self.__cur.fetchone()

            if result[0] == 0:
                print("Таблица 'dishes' пуста.")
            else:
                res = [dict(item) for item in self.__cur.execute('SELECT * FROM dishes').fetchall()]
                if res:
                    return res
        except Exception as e:
            print(e)

        return []

    def get_dish_by_id(self, dish_id):
        try:
            self.__cur.execute("SELECT * FROM dishes WHERE dish_id = ?", (dish_id,))
            result = self.__cur.fetchone()
            if result:
                return result
        except Exception as e:
            print(e)
        return None

    def delete_dish_id(self, dish_id):
        try:
            self.__cur.execute('DELETE FROM dishes WHERE dish_id = ?', (dish_id,))
            self.__db.commit()
        except Exception as e:
            print(e)
            return False
        return True

    def cart_dishes(self, dish_id, quantity):
        try:
            self.__cur.execute('SELECT * FROM dishes WHERE dish_id = ?', (dish_id,))
            dish = self.__cur.fetchone()
            if dish:
                print(dish)
                return {'dish_id': dish['dish_id'], 'name': dish["name"], 'price': dish["price"], 'quantity': quantity}
        except Exception as e:
            print(e)
            return False
        return {}

    def cart_add_in_db(self, id_user, name, mail, cart, price, delivery):
        try:
            id_user = int(id_user)
            price = int(price)
            current_datetime = datetime.now()
            tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            self.__cur.execute(
                'INSERT INTO orders (id_user, name, email, cart, time, price, status, delivery) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?)', (id_user, name, mail, cart, tm, price, 0, delivery))
            self.__db.commit()
            return True
        except Exception as e:
            print(e)
        return False

    def adduser(self, name, mail, hpsw, app):
        try:
            self.__cur.execute("SELECT COUNT(*) FROM users WHERE email LIKE ?", (mail,))
            res = self.__cur.fetchone()
            if res[0] > 0:
                return False

            default = f'images{random.randint(1, 8)}'
            with app.open_resource(app.root_path + url_for('static', filename=f'avatar/{default}.png'), mode='rb') as f:
                img = f.read()

            current_datetime = datetime.now()
            tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

            self.__cur.execute('INSERT INTO users (name, email, password_hash, time, avatar) '
                               'VALUES (?, ?, ?, ?, ?)', (name, mail, hpsw, tm, img))
            self.__db.commit()
            self.__cur.execute('SELECT * FROM users WHERE email = ? LIMIT 1', (mail,))
            id_user = self.__cur.fetchone()
            return id_user
        except Exception as e:
            print(e)
        return False

    def getuser(self, user_id):
        try:
            self.__cur.execute('SELECT * FROM users WHERE id = ? LIMIT 1', (user_id,))
            res = self.__cur.fetchone()
            if res:
                return res
            else:

                return False
        except Exception as e:
            print(e)

        return False

    def getUserByEmail(self, mail):
        try:
            self.__cur.execute('SELECT * FROM users WHERE email = ? LIMIT 1', (mail,))
            res = self.__cur.fetchone()
            if not res:

                return False
            return res
        except Exception as e:
            print(e)
        return False

    def all_users(self):
        try:
            self.__cur.execute('SELECT * FROM users')
            res = self.__cur.fetchall()
            if res: return res
            return res
        except Exception as e:
            print(e)
        return False

    def sent_message(self, id_user, name, email, message, status):
        try:
            id_user = int(id_user)
            current_datetime = datetime.now()
            tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            self.__cur.execute('INSERT INTO support (id_user, name, email, message, time, status) '
                               'VALUES (?, ?, ?, ?, ?, ?)', (id_user, name, email, message, tm, status))
            self.__db.commit()

            id_support = self.__cur.execute('SELECT id FROM support WHERE time = ?', (tm,)).fetchone()
            if id_support is not None:
                id_support = int(id_support[0])
                self.__cur.execute(
                    'INSERT INTO support_chat (id_support, id_message, id_user, name, email, message, time) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)', (id_support, 1, id_user, name, email, message, tm))
                self.__db.commit()
            return True
        except Exception as e:
            print(e)
        return False

    def select_support(self, id_support):
        try:
            self.__cur.execute('SELECT * FROM support_chat where id_support = ?', (id_support,))
            res = self.__cur.fetchall()
            if res:
                return [dict(item) for item in res]
        except Exception as e:
            print(e)
        return []


    def insert_reply_support(self, id_support, id_user, name, email, message):
        try:
            current_datetime = datetime.now()
            tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

            info = self.__cur.execute('select id_message from support_chat where id_support = ?',
                                      (id_support,)).fetchall()
            info = [dict(item) for item in info]

            mx = max(vl for item in info for vl in item.values())
            next_id_message = int(mx) + 1

            self.__cur.execute('INSERT INTO support_chat (id_support, id_message, id_user, name, email, message, time) '
                               'VALUES (?, ?, ?, ?, ?, ?, ?)',
                               (id_support, next_id_message, id_user, name, email, message, tm))
            self.__db.commit()
            return True
        except Exception as e:
            print(e)
        return False

    def supportmsg(self, id_user):
        try:
            self.__cur.execute('SELECT * FROM support WHERE id_user = ? ORDER BY id DESC', (id_user,))
            res = self.__cur.fetchall()
            if res:
                return res
        except Exception as e:
            print(e)
        return []

    def select_support_data(self, id_support):
        try:
            self.__cur.execute('SELECT * FROM support WHERE id = ?', (id_support,))
            res = self.__cur.fetchall()

            if res:
                return [dict(item) for item in res]

        except Exception as e:
            print(e)
        return []

    def show_orders(self, id_user):
        try:
            self.__cur.execute('SELECT * FROM orders WHERE id_user = ? ORDER BY id DESC', (id_user,))
            res = self.__cur.fetchall()

            if res:
                return res

        except Exception as e:
            print(e)
        return []

    def show_orders_status(self, id_user):
        try:
            self.__cur.execute('SELECT * FROM orders WHERE id_user = ? and status < 3 ORDER BY id DESC', (id_user,))
            res = self.__cur.fetchall()

            if res:
                return res

        except Exception as e:
            print(e)
        return []

    def show_dishes_search(self, dish_category):
        try:
            res = [dict(item) for item in
                   self.__cur.execute('SELECT * FROM dishes where category = ?', (dish_category,)).fetchall()]
            if res:
                return res
        except Exception as e:
            print(e)
        return []

    def show_like_dishes(self):
        try:
            res = [dict(item) for item in self.__cur.execute('SELECT * FROM likes').fetchall()]
            if res:
                return res
        except Exception as e:
            print(e)
        return []

    def show_reviews(self):
        try:
            self.__cur.execute('SELECT * FROM reviews ORDER BY id DESC')
            res = self.__cur.fetchall()
            if res: return res
        except Exception as e:
            print(e)
        return []

    def show_reply(self):
        try:
            self.__cur.execute('SELECT * FROM reply_reviews')
            res = self.__cur.fetchall()
            if res: return res
        except Exception as e:
            print(e)
        return []

    def add_reviews_in_db(self, id_user, name, email, message, avatar, rating):
        try:
            id_user = int(id_user)
            current_datetime = datetime.now()
            tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
            self.__cur.execute('INSERT INTO reviews (id_user, name, email, message, time, status, avatar, rating) '
                               'VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
                               (id_user, name, email, message, tm, 1, avatar, rating))
            self.__db.commit()
            return True
        except Exception as e:
            print(e)
        return False

    def users(self):
        self.__cur.execute('select * from users')
        res = self.__cur.fetchall()
        return res

    def statistics_add(self, date, count):
        try:
            if count == '':
                count = 0
            else:
                count = int(count)

            self.__cur.execute('SELECT COUNT(*) FROM visits WHERE date = ? AND count = ?', (date, count))
            exists = self.__cur.fetchone()[0]

            if exists == 0:
                self.__cur.execute('INSERT INTO visits (date, count) VALUES (?, ?)', (date, count))
                self.__db.commit()
                return True
            else:
                print(f"Запись с датой {date} и количеством {count} уже существует.")
                return False
        except Exception as e:
            print(e)
        return False

    def toggle_like(self, dish_id, user_id, liked):
        try:
            existing_like = self.__cur.execute('SELECT * FROM likes WHERE dish_id = ? AND user_id = ?',
                                               (dish_id, user_id)).fetchone()

            if liked and not existing_like:
                self.__cur.execute('INSERT INTO likes (dish_id, user_id) VALUES (?, ?)', (dish_id, user_id))
            elif not liked and existing_like:
                self.__cur.execute('DELETE FROM likes WHERE dish_id = ? AND user_id = ?', (dish_id, user_id))
            self.__db.commit()
            return True
        except Exception as e:
            print(e)
        return False

    def likes_count(self, dish_id):
        likes_count = {}
        try:
            likes_count = self.__cur.execute('SELECT COUNT(*) FROM likes WHERE dish_id = ?', (dish_id,)).fetchone()[0]
        except Exception as e:
            print(e)
        return likes_count

    def show_reviews_rating(self, number):
        try:
            res = self.__cur.execute('select * from reviews WHERE rating = ? ORDER BY id DESC',
                                     (int(number),)).fetchall()
            if res:
                return res
        except Exception as e:
            print(e)
        return []

    def show_my_reviews(self, user_id):
        try:
            res = self.__cur.execute('select * from reviews WHERE id_user = ? ORDER BY id DESC',
                                     (int(user_id),)).fetchall()
            if res:
                return res
        except Exception as e:
            print(e)
        return []

    def select_visit_user(self, id_user):
        try:
            res = self.__cur.execute('select visit_time from visit_statistics WHERE id_user = ? order by id desc',
                                     (int(id_user),)).fetchone()
            if res:
                return res
        except Exception as e:
            print(e)
        return []

    def insert_visit_time(self, visit_time, id_user):
        try:
            self.__cur.execute('INSERT INTO visit_statistics (visit_time, id_user) VALUES (?, ?)',
                               (visit_time, id_user))
            self.__db.commit()
            return True
        except Exception as e:
            print(e)
        return False

    def select_discount_dishes(self):
        try:
            res = self.__cur.execute('select * from discounts').fetchall()
            return [dict(item) for item in res]
        except Exception as e:
            print(e)
        return []

    def select_new_dishes(self):
        try:
            res = self.__cur.execute('select * from new_dishes').fetchall()
            return [dict(item) for item in res]
        except Exception as e:
            print(e)
        return []


