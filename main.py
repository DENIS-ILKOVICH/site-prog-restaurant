from time import *
from flask import Flask, render_template, request, redirect, url_for, flash, session, g, make_response, abort, \
    send_file, jsonify
from datetime import *
from flask_login import LoginManager, login_user, logout_user, current_user, login_required
from werkzeug.security import generate_password_hash, check_password_hash
import re
from UserLogin import UserLogin
from forms import LoginForm
from dbprogsite import MenuItem
from admin.admin import admin
import io
import sqlite3
import os

app = Flask(__name__)
app.secret_key = '1567e6613dc3f3c1e16c0d6b54fdb734bcc12a4a106f885f'

default_config = {
    'DEBUG': True,
    'SECRET_KEY': 'f29f21d99708278a14661bfc44f9a12421fa72047cdcec54'
}

app.register_blueprint(admin, url_prefix='/admin')

app.config.update(default_config)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Please log in to continue using the website"
login_manager.login_message_category = 'success'


sort_menu = [
    'Starters',
    'Main Courses',
    'Salads',
    'Desserts',
    'Fruit Dishes',
    'Grilled Dishes',
    'Pastry & Baked Goods',
    'Fast Food',
    'Dairy Dishes',
    'Breakfasts',
    'Cold Drinks',
    'Hot Drinks'
]


app.config.update(
    DATABASE=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'siteprogrestaurant.db')
)


def dbconnection():
    if 'db' not in g:
        try:
            g.db = sqlite3.connect(app.config['DATABASE'])
            g.db.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            g.db = None
    return g.db


@app.before_request
def before_request():
    global dbase
    db = dbconnection()
    dbase = MenuItem(db)


@app.teardown_appcontext
def close_db(error):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()



@app.route('/show_dishes', methods=['POST', 'GET'])
def show_dishes():
    get_visit_user()

    sort = 0
    category = ''.join(request.form.values())

    list_dishes = dbase.dishes_show()
    list_dishes = like_dish(list_dishes)

    discounts = dbase.select_discount_dishes()
    for item in list_dishes:
        for dis in discounts:
            if item['dish_id'] == dis['dish_id']:
                item['dis_price'] = f"{item['price'] - item['price'] * (dis['discount'] / 100)}0"

    sort_dish = ''.join(request.form.values())
    if 'Cancel' in request.form:
        list_dishes = list_dishes
    if request.method == 'POST':
        if ''.join(request.form.values()) in sort_menu:
            list_dishes = dbase.show_dishes_search(category)
            sort = category
        if 'Expensive first' in request.form:
            list_dishes = sorted(
                list_dishes,
                key=lambda x: (int(x['dis_price'][:-3]) if 'dis_price' in x else x['price']),
                reverse=True
            )
            sort = 'Expensive first'
        if 'Cheap first' in request.form:
            list_dishes = sorted(
                list_dishes,
                key=lambda x: (int(x['dis_price'][:-3]) if 'dis_price' in x else x['price'])
            )
            sort = 'From Cheap'
        if 'New dishes' in request.form:
            list_dishes = sorted(list_dishes, key=lambda x: x['dish_id'], reverse=True)
            sort = 'New dishes'
        if 'Popular' in request.form:
            list_dishes = sorted(list_dishes, key=lambda x: x['likes_count'], reverse=True)
            sort = 'Popular'
        if 'Discounted' in request.form:
            list_dishes = [item for item in list_dishes if 'dis_price' in item]
            sort = 'Discounted'
    else:
        list_dishes = list_dishes

    if request.method == 'POST':
        list_dishes.append('sorted')
    sorted_list = best_list_dishes(like_dish(dbase.dishes_show()))

    return render_template(
        'base.html',
        title='Home Page',
        order=session.get('order'),
        sort=sort_menu,
        dishes=list_dishes,
        best_list=sorted_list,
        style=style,
        sort_type=sort
    )



@app.route('/style', methods=['POST'])
def style():
    if 'dark' in request.form:
        session['style'] = 1
    elif 'white' in request.form:
        session['style'] = 0
    return jsonify(style=session['style'])


@app.route('/', methods=['POST', 'GET'])
def index():
    best_dish = best_list_dishes(like_dish(dbase.dishes_show()))
    best_reviews = best_users_reviews(dbase.show_reviews())
    get_visit_user()
    return render_template(
        'about.html',
        title='Home Page',
        best_dish=best_dish,
        best_reviews=best_reviews,
        sort_menu=sort_menu
    )



# ----------------------------------------------------------------------------------------------------------------
@app.errorhandler(404)
def error404(error):
    return render_template(
        'error.html',
        title='Page Not Found',
        href1=url_for('index')
    ), 404


@app.errorhandler(401)
@login_required
def error401(error):
    return render_template(
        'error.html',
        title='Page Not Found',
        href1=url_for('index'),
        href2=url_for('profile')
    ), 401


# -----------------------------------------------------------------------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    user_id = session.get('user_id')
    return UserLogin().fromDB(user_id, dbase)


@app.route('/login', methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('special_pr'))

    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            user = dbase.getUserByEmail(form.mail.data)
            if user:
                passDB = user['password_hash']
                passForm = form.psw.data
                if check_password_hash(passDB, passForm):
                    userlogin = UserLogin().create(user)
                    login_user(userlogin)
                    session['user_id'] = current_user.get_id()
                    return redirect(request.args.get("next") or url_for('special_pr'))
                else:
                    flash('Invalid email or password', 'error')
            else:
                flash('This user is not registered', 'info')
        else:
            flash('Input error', 'warning')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout', methods=['POST', 'GET'])
@login_required
def logout():
    if current_user.is_authenticated:
        logout_user()
    return redirect('login')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        mail = request.form.get('mail', '').strip()
        psw = request.form.get('psw', '').strip()
        psw2 = request.form.get('psw2', '').strip()

        if len(name) > 1 and len(mail) > 1 and len(psw) > 1 and psw == psw2:
            hash_psw = generate_password_hash(psw)
            user_id = dbase.adduser(name, mail, hash_psw, app)
            if user_id:
                userlogin = UserLogin().create(user_id)
                login_user(userlogin)
                session['user_id'] = current_user.get_id()
                return redirect(url_for('special_pr'))
            else:
                flash('Registration error', category='error')
        else:
            flash('Input error, please fill in all fields correctly!', 'error')

    return render_template('register.html', title='Register')



# -------------------------------------------------------------------------------------------


@app.route('/image_dish/<int:dish_id>')
def image_dish(dish_id):
    try:
        result = dbase.get_dish_by_id(dish_id)

        if result:
            img_data = result['image']
            return send_file(io.BytesIO(img_data), mimetype='image/png')
        else:
            abort(404)
    except Exception as e:
        print(e)


@app.route('/contact', methods=['POST', 'GET'])
@login_required
def contact():
    supportmsg = []
    if dbase.supportmsg(current_user.get_id()):
        supportmsg = [dict(item) for item in dbase.supportmsg(current_user.get_id())]
    print(supportmsg)

    if request.method == "POST":
        id_user = current_user.get_id()
        name = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        status = False
        if len(name) > 3 and not re.search(pattern, name) and 5 < len(message) < 1500 and re.search(pattern, email):
            mesg = dbase.sent_message(id_user, name, email, message, status)
            if not mesg:
                flash('Database error', category='error')
        else:
            flash('Input error', category='error')

    return render_template(
        'contact.html',
        title='Contact Support',
        supportmsg=supportmsg
    )



@app.route('/contact_add', methods=['POST', 'GET'])
@login_required
def contact_add():
    if request.method == "POST":
        id_user = current_user.get_id()
        name = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        status = False
        if len(name) > 3 and not re.search(pattern, name) and 5 < len(message) < 1500 and re.search(pattern, email):
            mesg = dbase.sent_message(id_user, name, email, message, status)
            if not mesg:
                flash('Database error', category='error')
        else:
            flash('Input error', category='error')

        alias = request.form.get('alias')
    return redirect(url_for('contact_chat', alias=alias))


@app.route('/<alias>')
@login_required
def contact_chat(alias):
    try:
        alias = str(alias)
        id_support = int(alias.replace('support_chat_', ''))

        id_user = dbase.select_support_data(id_support)[0]['id_user']
        support_chat_list = dbase.select_support(id_support)
        support_status = int(dbase.select_support_data(id_support)[0]['status'])

        if int(current_user.get_id()) != id_user:
            return abort(401)
    except Exception as e:
        return abort(401)

    return render_template(
        'contact_chat.html',
        title='Support Chat',
        support_chat_list=support_chat_list,
        alias=alias,
        user_id=int(current_user.get_id()),
        support_status=support_status
    )



@app.route('/contact/<alias>', methods=['POST'])
@login_required
def reply_message_support(alias):
    id_support = request.form.get('id_support')
    id_user = request.form.get('id_user')
    name = request.form.get('name')
    email = request.form.get('email')
    message = request.form.get('message')

    if request.method == 'POST':
        res = dbase.insert_reply_support(id_support, id_user, name, email, message)

    return redirect(url_for('contact_chat', alias=alias))


@app.route('/add_to_cart/<int:dish_id>', methods=['POST'])
@login_required
def add_to_cart(dish_id):
    quantity = int(request.form.get('quantity', 0))
    if 'cart' not in session:
        session['cart'] = {}
    cart = session['cart']

    dish_id = int(dish_id)
    cart = {int(k): v for k, v in cart.items()}

    if dish_id in cart:
        cart[dish_id] += quantity
    else:
        cart[dish_id] = quantity

    session['cart'] = cart

    return redirect(url_for('show_dishes'))


@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    dishes_in_cart = []
    total_sum = 0

    if cart:
        try:
            for dish_id, quantity in cart.items():
                res = dbase.cart_dishes(dish_id, quantity)
                if res:
                    dishes_in_cart.append(res)
            if not dishes_in_cart:
                flash('Your cart is empty.', 'info')

            discounts = dbase.select_discount_dishes()
            for item in dishes_in_cart:
                discount_found = False
                for dis in discounts:
                    if item['dish_id'] == dis['dish_id']:
                        item['dis_price'] = item['price'] - (item['price'] * (dis['discount'] / 100))
                        discount_found = True
                        break
                if not discount_found:
                    item['dis_price'] = item['price']

            total_sum = sum(item['dis_price'] * item['quantity'] for item in dishes_in_cart)
            order = dishes_in_cart.copy()
            order.append({'total_sum': total_sum})
            session['order'] = order
        except Exception as e:
            print(e)

    return render_template('cart.html', dishes=dishes_in_cart, sum=total_sum)



@app.route('/remove_dish_from_cart/<int:id_remove>', methods=['POST'])
@login_required
def remove_dish_from_cart(id_remove):
    cart = session.get('cart', {})
    if request.method == 'POST':
        id_remove = str(id_remove)
        print(id_remove)
        print(cart)
        if id_remove in cart:
            cart.pop(id_remove)
            session['cart'] = cart
    return redirect(url_for('cart'))


@app.route('/add_cart_in_db', methods=['POST'])
@login_required
def add_cart_in_db():
    user_id = current_user.get_id()
    name = current_user.get_name()
    email = current_user.get_mail()

    if request.method == 'POST':
        order = session.get('order')

        city = request.form.get('city', '')
        street = request.form.get('street', '')
        house_number = request.form.get('house_number', '')
        entrance_number = request.form.get('entrance_number', '-')
        floor = request.form.get('floor', '-')
        apartment_number = request.form.get('apartment_number', '-')
        intercom_code = request.form.get('intercom_code', '-')
        landmarks = request.form.get('landmarks', '-')

        if order:
            try:
                cart = '<br>'.join([f'{item["name"]} - {item["quantity"]} pcs.' for item in order[:-1]])
                price = order[-1]["total_sum"]
                cart += f"<br>Total price: {int(price)}.00"

                delivery = (
                    f'City: {city}<br>'
                    f'Street: {street}<br>'
                    f'House: {house_number}<br>'
                    f'Entrance: {entrance_number}<br>'
                    f'Floor: {floor}<br>'
                    f'Apartment: {apartment_number}<br>'
                    f'Intercom code: {intercom_code}<br>'
                    f'Landmarks: {landmarks}'
                )

                res = dbase.cart_add_in_db(user_id, name, email, cart, price, delivery)
                if res:
                    session.pop('cart', None)
                    session.pop('order', None)
                    return redirect(url_for('show_dishes'))
            except Exception as e:
                print(e)
                flash('Database error', 'error')
        else:
            flash('Cart is empty', 'error')
    else:
        flash('Error!', 'error')
    return redirect(url_for('list_dishes'))



@app.route('/profile')
@login_required
def profile():
    prof = 'Profile ' + str(current_user.get_name())
    user = dict(dbase.getUserByEmail(current_user.get_mail()))
    orders_status = dbase.show_orders_status(current_user.get_id())
    orders = dbase.show_orders(current_user.get_id())
    print(orders)
    list_dish = like_dish(dbase.dishes_show())
    dish_like_user = []
    for item in list_dish:
        if item['user_liked'] == 1:
            dish_like_user.append(item)
    if user:
        return render_template('profile.html', title=prof, user=user, orders_status=orders_status, orders=orders,
                               like_dish=dish_like_user)
    return abort(401)


@app.route('/userava')
@login_required
def userava():
    img = current_user.get_avatar()
    if not img:
        return ''

    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/reviews', methods=['POST', 'get'])
def reviews():
    reviews_list = []
    reply_list = []
    btn_info = [request.args.get('index', 0)]
    if request.method == 'POST':
        if 'my_reviews' in request.form:
            reviews_list = dbase.show_my_reviews(current_user.get_id())
        else:
            reviews_list = dbase.show_reviews_rating(''.join(request.form))
    else:
        reviews_list = dbase.show_reviews()
        reply_list = dbase.show_reply()

    avg_reviews = average_reviews(dbase.show_reviews())
    btn_info.append(len(reviews_list))
    return render_template('reviews.html', title='Reviews', reviews_list=reviews_list, reply_list=reply_list,
                           avg_reviews=avg_reviews, btn_info=btn_info)


@app.route('/avatar/<int:review_id>')
def get_avatar(review_id):
    reviews_list = [dict(item) for item in dbase.show_reviews()]

    avatar_data = next((item['avatar'] for item in reviews_list if item['id'] == review_id), None)

    if avatar_data:
        img_io = io.BytesIO(avatar_data)
        img_io.seek(0)
        return send_file(img_io, mimetype='image/png')
    abort(404)


@app.route('/add_reviews', methods=['POST', 'get'])
@login_required
def add_reviews():
    if request.method == 'POST':

        id_user = current_user.get_id()
        name = current_user.get_name()
        email = current_user.get_mail()
        message = request.form.get('reviews', '').strip()
        avatar = current_user.get_avatar()
        rating = int(request.form.get('rating', 0))

        if message:
            try:
                rev_db = dbase.add_reviews_in_db(id_user, name, email, message, avatar, rating)
            except Exception as e:
                print(e)
    return redirect(url_for('reviews'))


@app.route('/toggle_like/<int:dish_id>', methods=['POST'])
@login_required
def toggle_like(dish_id):
    user_id = current_user.get_id()
    data = request.get_json()
    liked = data.get('liked')

    dbase.toggle_like(dish_id, user_id, liked)
    likes_count = dbase.likes_count(dish_id)

    return jsonify({'likes_count': likes_count, 'user_liked': liked})

@app.route('/special_pr', methods=['POST', 'GET'])
def special_pr():
    dishes = dbase.dishes_show()

    new_pr = dbase.select_new_dishes()
    new_pr_ids = {discount['dish_id'] for discount in new_pr}
    new_dishes = [dish for dish in dishes if dish['dish_id'] in new_pr_ids]
    sorted_new_dishes = sorted(new_dishes, key=lambda x: x['dish_id'])

    discounts = dbase.select_discount_dishes()
    discounted_dish_ids = {discount['dish_id'] for discount in discounts}
    discounted_dishes = [dish for dish in dishes if dish['dish_id'] in discounted_dish_ids]
    sorted_discounted_dishes = sorted(discounted_dishes, key=lambda x: x['dish_id'])

    for item in sorted_discounted_dishes:
        for dis in discounts:
            if item['dish_id'] == dis['dish_id']:
                item['disc_price'] = item['price'] - item['price'] * (dis['discount'] / 100)

    for item in sorted_new_dishes:
        discount_found = False
        for dis in discounts:
            if item['dish_id'] == dis['dish_id']:
                item['dis_price'] = item['price'] - (item['price'] * (dis['discount'] / 100))
                discount_found = True
                break
        if not discount_found:
            item['dis_price'] = item['price']

    sorted_new_dishes.reverse()
    mx_discount = max(item['discount'] for item in discounts)

    best_dish = best_list_dishes(like_dish(dbase.dishes_show()))
    for item in best_dish:
        print(item['likes_count'])

    return render_template(
        'special_pr.html',
        title='Home',
        new_pr=sorted_new_dishes,
        discounts_list=sorted_discounted_dishes,
        discounts=discounts,
        mx_discount=mx_discount,
        best_dish=best_dish
    )



def like_dish(list_dishes):
    user_id = current_user.get_id()
    list_likes = dbase.show_like_dishes()

    likes_count = {}
    for like in list_likes:
        dish_id = like['dish_id']
        if dish_id in likes_count:
            likes_count[dish_id] += 1
        else:
            likes_count[dish_id] = 1

    if current_user.is_authenticated:
        user_liked_dishes = {like['dish_id'] for like in list_likes if like['user_id'] == int(user_id)}
    else:
        user_liked_dishes = {}

    for dish in list_dishes:
        dish_id = dish['dish_id']
        dish['likes_count'] = likes_count.get(dish_id, 0)
        dish['user_liked'] = 1 if dish_id in user_liked_dishes else 0

    return list_dishes


def best_list_dishes(list_dishes):
    result = []
    sorted_list = sorted(list_dishes, key=lambda x: x['likes_count'], reverse=True)
    for item in sorted_list:
        if item['status'] == '1':
            result.append(item)
    return result


def best_users_reviews(list_reviews):
    result = []
    for item in list_reviews:
        if item['rating'] == 5 and 50 < len(item['message']) < 150:
            result.append(item)
    return result


def average_reviews(list_reviews):
    total = 0
    len_r = 0
    for item in list_reviews:
        if item['rating'] > 0:
            total += item['rating']
            len_r += 1
    avg = total / len_r
    return round(total / len_r, 1)


def get_visit_user():
    if current_user.is_authenticated:
        today = datetime.now().strftime("%Y-%m-%d")
        id_user = current_user.get_id()
        visit_time = ''.join(dbase.select_visit_user(id_user))
        if not visit_time or visit_time != today:
            dbase.insert_visit_time(today, id_user)
    return True


if __name__ == '__main__':
    app.run(debug=True, port=5001)
