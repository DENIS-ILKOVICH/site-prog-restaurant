import re
from flask import *
import io
from datetime import datetime
from datetime import *
import os


# r = redis.StrictRedis(
#     host='redis-12658.c238.us-central1-2.gce.redns.redis-cloud.com',
#     port=12658,
#     password='a1Av0jAdSsqWSKUsfUFffqce4ijdebxD',
#     decode_responses=True
# )

admin = Blueprint('admin', __name__, template_folder='templates', static_folder='static')

menu = [
    {'title': 'Home', 'url': '.main'},
    {'title': 'Dishes', 'url': '.add_dish'},
    {'title': 'Orders', 'url': '.show_orders'},
    {'title': 'Users', 'url': '.userslist'},
    {'title': 'Reviews', 'url': '.show_reviews'},
    {'title': 'Support', 'url': '.show_support'},
    {'title': 'Finance', 'url': '.statistic'}
]


sort_menu = [
    'Starters',
    'Main Courses',
    'Side Dishes',
    'Salads',
    'Desserts',
    'Hot Drinks',
    'Cold Drinks',
    'Fruit Dishes',
    'Grilled Dishes',
    'Pasta & Baked Goods',
    'Fast Food',
    'Dairy Dishes',
    'Breakfasts'
]

@admin.before_request
def before_request():
    global dbase
    dbase = g.get('db')



@admin.teardown_request
def teardown_request(request):
    global dbase
    dbase = None
    return request


def login_admin():
    session['admin_logged'] = 1


def islogged():
    return True if session.get('admin_logged') else False


def logout_admin():
    session.pop('admin_logged', None)


@admin.route('/', methods=['POST', 'GET'])
def main():
    if not islogged():
        return redirect(url_for('.login'))
    discounts = 0
    sorted_discounted_dishes = []
    sorted_new_dishes = []
    new_dish_list = []
    dis_dish_list = []
    mx_discount = 0
    if dbase:
        try:
            cur = dbase.cursor()
            dishes = [dict(item) for item in cur.execute('SELECT * FROM dishes').fetchall()]

            new_pr = [dict(item) for item in cur.execute('SELECT * FROM new_dishes').fetchall()]
            new_pr_ids = {discount['dish_id'] for discount in new_pr}
            new_dishes = [dish for dish in dishes if dish['dish_id'] in new_pr_ids]
            sorted_new_dishes = sorted(new_dishes, key=lambda x: x['dish_id'])

            discounts = [dict(item) for item in cur.execute('SELECT * FROM discounts').fetchall()]
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
                        item['dis_price'] = item['price'] - item['price'] * (dis['discount'] / 100)
                        discount_found = True
                        break
                if not discount_found:
                    item['dis_price'] = item['price']

            sorted_new_dishes.reverse()
            new_dish_list = [item for item in dishes if item['dish_id'] not in new_pr_ids]
            dis_dish_list = [item for item in dishes if item['dish_id'] not in discounted_dish_ids]

            mx_discount = max(item['discount'] for item in discounts)

        except Exception as e:
            print(e)
    return render_template(
        'admin/main.html',
        title='Home',
        menu=menu,
        new_pr=sorted_new_dishes,
        discounts_list=sorted_discounted_dishes,
        discounts=discounts,
        new_dish_list=new_dish_list,
        dis_dish_list=dis_dish_list,
        mx_discount=mx_discount
    )



@admin.route('/add_new_dish/<int:dish_id>', methods=['POST', 'GET'])
def add_new_dish(dish_id):
    if not islogged():
        return redirect(url_for('.main'))
    if dbase:
        try:
            cur = dbase.cursor()
            if request.method == 'POST':
                cur.execute('INSERT INTO new_dishes (dish_id) VALUES(?)', (dish_id,))
                dbase.commit()
        except Exception as e:
            print(e)
    return redirect(url_for('.main'))


@admin.route('/remove_new_dish/<int:dish_id>', methods=['POST', 'GET'])
def remove_new_dish(dish_id):
    if not islogged():
        return redirect(url_for('.main'))
    if dbase:
        try:
            cur = dbase.cursor()
            if request.method == 'POST':
                cur.execute('DELETE FROM new_dishes WHERE dish_id = ?', (dish_id,))
                dbase.commit()
                print(dish_id)
        except Exception as e:
            print(e)
    return redirect(url_for('.main'))


@admin.route('/add_discount_dish/<int:dish_id>', methods=['POST', 'GET'])
def add_discount_dish(dish_id):
    if not islogged():
        return redirect(url_for('.main'))
    if dbase:
        try:
            cur = dbase.cursor()
            if request.method == 'POST':
                discount = request.form.get('discount', '')
                if discount.isdigit():
                    discount = int(discount)
                    if 1 <= discount <= 100:
                        cur.execute('INSERT INTO discounts (dish_id, discount) VALUES(?, ?)', (dish_id, discount))
                        dbase.commit()
        except Exception as e:
            print(e)
    return redirect(url_for('.main'))


@admin.route('/remove_discount_dish/<int:dish_id>', methods=['POST', 'GET'])
def remove_discount_dish(dish_id):
    if not islogged():
        return redirect(url_for('.main'))
    if dbase:
        try:
            cur = dbase.cursor()
            if request.method == 'POST':
                cur.execute('DELETE FROM discounts WHERE dish_id = ?', (dish_id,))
                dbase.commit()
        except Exception as e:
            print(e)
    return redirect(url_for('.main'))


@admin.route('/login', methods=['POST', 'GET'])
def login():
    if islogged():
        return redirect(url_for('.main'))
    if request.method == 'POST':
        if request.form['login'] == 'admin' and request.form['psw'] == '4159':
            login_admin()
            return redirect(url_for('.main'))
    return render_template('admin/login_admin.html', title='Авторизация')


@admin.route('/logout', methods=['POST', 'GET'])
def logout():
    if not islogged():
        return redirect(url_for('.login', title='Login'))

    logout_admin()

    return redirect(url_for('index'))

@admin.route('/userslist', methods=['POST', 'GET'])
def userslist():
    if not islogged():
        return redirect(url_for('.login', title='Login'))

    list_user = []
    if dbase:
        try:
            cur = dbase.cursor()
            if request.method == 'POST':
                search_user = request.form.get('user', '').strip()
                pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
                if re.search(pattern, search_user):
                    cur.execute('SELECT * FROM users WHERE email = ?', (search_user,))
                else:
                    user_list_name = sorted(
                        item['name'] for item in [dict(item) for item in cur.execute('SELECT name FROM users')]
                    )
                    user_list_name = list(set(user_list_name))

                    for item in user_list_name:
                        if item.lower().startswith(search_user.lower()):
                            cur.execute('SELECT * FROM users WHERE name = ?', (item,))
                            list_user.append(cur.fetchall())
                    list_user = [dict(i) for item in list_user for i in item]
            else:
                cur.execute('SELECT * FROM users ORDER BY time DESC')
                list_user = cur.fetchall()
        except Exception as e:
            print(e)

    return render_template(
        'admin/userslist.html',
        title='All Users',
        list=list_user,
        menu=menu
    )


def dishes_show():
    if dbase:
        try:
            cur = dbase.cursor()
            cur.execute("SELECT COUNT(*) AS count FROM dishes;")
            result = cur.fetchone()
            if result['count'] == 0:
                cur.execute("DELETE FROM dishes;")
                cur.execute("ALTER TABLE dishes AUTOINCREMENT = 1;")
                dbase.commit()
            else:
                cur.execute('select * from dishes order by dish_id desc')
                res = cur.fetchall()
                if res:
                    res = [dict(item) for item in res]
                    return res

        except Exception as e:
            print(e)
    return []
@admin.route('/add_dish', methods=['POST', 'GET'])
def add_dish():
    if not islogged():
        return redirect(url_for('.login', title='Login'))

    dishes = []
    if dbase:
        cur = dbase.cursor()
        if request.method == 'POST':
            category = request.form.get('category', '').strip()
            name = request.form.get('name', '').strip()
            price = request.form.get('price', '').strip()
            file = request.files.get('file')
            description = request.form.get('description', '').strip()

            if file and file.filename:
                try:
                    img = file.read()
                    if len(name) > 0 and len(price) > 0 and len(description) > 0:
                        res = cur.execute(
                            "INSERT INTO dishes (name, image, price, description, category) "
                            "VALUES (?, ?, ?, ?, ?)", (name, img, price, description, category)
                        )
                        dbase.commit()
                        if res:
                            flash('Dish added successfully', category='success')
                        else:
                            flash('Error adding dish', category='error')
                    else:
                        flash('Name, price, and description must be filled', category='error')
                except Exception as e:
                    print(e)
                    flash('An error occurred while adding the dish', category='error')
            else:
                flash('Input error: file not selected', category='error')

            if 's_dish' in request.form:
                list_dish = dishes_show()
                list_dish = sorted(item['name'] for item in list_dish)
                search_dish = request.form.get('s_dish').capitalize()
                for item in list_dish:
                    if search_dish.lower() in item.lower():
                        cur.execute('SELECT * FROM dishes WHERE name = ?', (item,))
                        dishes.append(cur.fetchall())
                dishes = [dict(i) for item in dishes for i in item]
            else:
                cur.execute('SELECT * FROM dishes ORDER BY dish_id DESC')
        else:
            cur.execute('SELECT * FROM dishes ORDER BY dish_id DESC')
            dishes = cur.fetchall()
            dishes = [dict(item) for item in dishes]

    return render_template(
        'admin/dishes.html',
        title="Dishes Page",
        dishes=dishes,
        menu=menu,
        select=sort_menu
    )

@admin.route('/image_dish/<int:dish_id>')
def image_dish(dish_id):
    if not islogged():
        return redirect(url_for('.login', title='Авторизация'))

    if dbase:
        try:
            cur = dbase.cursor()
            cur.execute("SELECT image FROM dishes WHERE dish_id = ?", (dish_id,))
            result = dict(cur.fetchone())

            if result and result['image']:
                img_data = result['image']
                img_io = io.BytesIO(img_data)
                img_io.seek(0)
                return send_file(img_io, mimetype='image/jpeg')
            else:
                abort(404)
        except Exception as e:
            print(e)
            abort(500)


@admin.route('/image_dish/<int:dish_id>/delete', methods=['POST'])
def delete_dish(dish_id):
    if not islogged():
        return redirect(url_for('.login', title='Login'))
    if dbase:
        try:
            cur = dbase.cursor()
            cur.execute('DELETE FROM dishes WHERE dish_id = ?;', (dish_id,))
            dbase.commit()
        except Exception as e:
            print(e)
    return redirect(url_for('.add_dish'))

@admin.route('/show_orders', methods=['POST', 'GET'])
def show_orders():
    if not islogged():
        return redirect(url_for('.login', title='Login'))

    search_query = request.args.get('search_order')
    sort_query = request.args.get('sort_order')

    orders = []

    if request.method == 'POST':
        search_query = request.form.get('order', '').strip()
        sort_query = ''.join(request.form.keys())
        return redirect(url_for('.show_orders', search_order=search_query, sort_order=sort_query))

    if dbase:
        try:
            cur = dbase.cursor()

            if search_query:
                if search_query.isdigit():
                    cur.execute('SELECT * FROM orders WHERE id = ?', (int(search_query),))
                elif search_query.lower() in ['ordered', 'o', 'ord']:
                    cur.execute('SELECT * FROM orders WHERE status = 0 ORDER BY id DESC')
                elif search_query.lower() in ['in progress', 'i', 'inpr']:
                    cur.execute('SELECT * FROM orders WHERE status = 1 ORDER BY id DESC')
                elif search_query.lower() in ['delivery', 'd', 'del']:
                    cur.execute('SELECT * FROM orders WHERE status = 2 ORDER BY id DESC')
                elif search_query.lower() in ['completed', 'c', 'comp']:
                    cur.execute('SELECT * FROM orders WHERE status = 3 ORDER BY id DESC')
                else:
                    cur.execute('SELECT * FROM orders WHERE name = ? ORDER BY id DESC', (search_query,))
            elif sort_query:
                if 'orderX' in sort_query or 'order1' in sort_query:
                    cur.execute('SELECT * FROM orders ORDER BY id DESC')
                elif 'order2' in sort_query:
                    cur.execute('SELECT * FROM orders ORDER BY id ASC')
                elif 'order_price1' in sort_query:
                    cur.execute('SELECT * FROM orders ORDER BY price DESC')
                elif 'order_price2' in sort_query:
                    cur.execute('SELECT * FROM orders ORDER BY price ASC')
                elif 'order_status1' in sort_query:
                    cur.execute('SELECT * FROM orders WHERE status = 0 ORDER BY id DESC')
                elif 'order_status2' in sort_query:
                    cur.execute('SELECT * FROM orders WHERE status = 1 ORDER BY id DESC')
                elif 'order_status3' in sort_query:
                    cur.execute('SELECT * FROM orders WHERE status = 2 ORDER BY id DESC')
                elif 'order_status4' in sort_query:
                    cur.execute('SELECT * FROM orders WHERE status = 3 ORDER BY id DESC')
            else:
                cur.execute('SELECT * FROM orders ORDER BY id DESC')

            orders = cur.fetchall()

        except Exception as e:
            print(f"Query execution error: {e}")

    return render_template('admin/orders.html', title='Orders', menu=menu, orders=orders)


@admin.route('/show_orders/<int:id>/confirmation', methods=['POST', 'GET'])
def order_confirmation(id):
    if not islogged():
        return redirect(url_for('.login'))

    if dbase:
        if request.method == 'POST':
            try:
                status = request.args.get('flag')
                cur = dbase.cursor()
                cur.execute('UPDATE orders SET status = ? WHERE id = ?', (status, id,))
                dbase.commit()
            except Exception as e:
                print(e)

    search_query = request.args.get('search_order')
    sort_query = request.args.get('sort_order')
    return redirect(url_for('.show_orders', search_order=search_query, sort_order=sort_query))


@admin.route('/show_orders/<int:id>/delete', methods=['POST', 'GET'])
def delete_order(id):
    if not islogged():
        return redirect(url_for('.login'))
    if dbase:
        if request.method == 'POST':
            try:
                cur = dbase.cursor()
                cur.execute('DELETE FROM orders WHERE id = ?;', (id,))
                dbase.commit()
            except Exception as e:
                print(e)
    search_query = request.args.get('search_order')
    sort_query = request.args.get('sort_order')
    return redirect(url_for('.show_orders', search_order=search_query, sort_order=sort_query))

@admin.route('/support', methods=['POST', 'GET'])
def show_support():
    if not islogged():
        return redirect(url_for('.login'))

    mes_list = []
    search_query = request.args.get('search', '')
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

    if request.method == 'POST':
        search_query = request.form.get('search', '').strip()
        return redirect(url_for('.show_support', search=search_query))

    if search_query:
        try:
            cur = dbase.cursor()

            if search_query.isdigit():
                cur.execute('SELECT * FROM support WHERE id = ? ORDER BY id DESC', (int(search_query),))
            elif search_query.lower() in ['pending', 'p']:
                cur.execute('SELECT * FROM support WHERE status = 0')
            elif search_query.lower() in ['reviewed', 'r']:
                cur.execute('SELECT * FROM support WHERE status = 1')
            elif re.search(pattern, search_query):
                cur.execute('SELECT * FROM support WHERE email = ? ORDER BY id DESC', (search_query,))
            else:
                cur.execute('SELECT * FROM support WHERE name = ? ORDER BY id DESC', (search_query,))

            mes_list = cur.fetchall()

            if not mes_list:
                flash('No results found for your query.', 'warning')

        except Exception as e:
            flash('Error executing the request.', 'error')
            print(e)

    else:
        try:
            cur = dbase.cursor()
            cur.execute('SELECT * FROM support ORDER BY id DESC')
            mes_list = cur.fetchall()

        except Exception as e:
            flash('Error loading data.', 'error')
            print(e)

    return render_template('admin/support.html', title='Support Messages', menu=menu, message=mes_list)


@admin.route('/support/<int:id>/delete', methods=['POST'])
def del_message(id):
    if not islogged():
        return redirect(url_for('.login'))

    if dbase and request.method == 'POST':
        try:
            cur = dbase.cursor()
            cur.execute('DELETE FROM support WHERE id = ?;', (id,))
            cur.execute('DELETE FROM support_chat WHERE id_support = ?;', (id,))
            dbase.commit()
        except Exception as e:
            flash('Error deleting the message.', 'error')
            print(e)

    search_query = request.form.get('search', '').strip()
    return redirect(url_for('.show_support', search=search_query))


@admin.route('/support/<alias>/reply_message_support', methods=['POST'])
def reply_message_support(alias):
    if not islogged():
        return redirect(url_for('.login', title='Login'))

    if dbase:
        try:
            if request.method == 'POST':
                cur = dbase.cursor()

                id_support = request.form.get('id_support', '').strip()

                info = cur.execute(
                    'SELECT id_message FROM support_chat WHERE id_support = ?', (id_support,)
                ).fetchall()
                info = [dict(item) for item in info]

                mx = max(vl for item in info for vl in item.values())
                next_id_message = int(mx) + 1

                message = request.form.get('message', '').strip()

                current_datetime = datetime.now()
                tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")

                cur.execute(
                    'INSERT INTO support_chat (id_support, id_message, id_user, name, email, message, time) '
                    'VALUES (?, ?, ?, ?, ?, ?, ?)',
                    (id_support, next_id_message, 0, 'admin', 'admin_email', message, tm)
                )
                dbase.commit()
        except Exception as e:
            flash('Error updating the message status.', 'error')
            print(e)

    return redirect(url_for('.support_chat', alias=alias))



@admin.route('/support/<alias>')
def support_chat(alias):
    alias = str(alias)
    id_support = int(alias.replace('support_chat_', ''))
    support_chat_list = []
    status = []

    if dbase:
        try:
            cur = dbase.cursor()

            res1 = cur.execute(
                'SELECT * FROM support_chat WHERE id_support = ?', (id_support,)
            ).fetchall()
            if res1:
                support_chat_list = [dict(item) for item in res1]

            res2 = cur.execute(
                'SELECT status FROM support WHERE id = ?', (id_support,)
            ).fetchall()
            if res2:
                status = int([dict(item) for item in res2][0]['status'])
        except Exception as e:
            print(e)

    return render_template(
        'admin/support_chat.html',
        title='Support Chat',
        support_chat_list=support_chat_list,
        alias=alias,
        menu=menu,
        status=status
    )


@admin.route('/support/<int:user_id>')
def get_user_avatar(user_id):
    if dbase:
        try:
            cur = dbase.cursor()
            avatar_data = \
                [dict(item) for item in cur.execute('select avatar from users where id = ?', (user_id,)).fetchall()][0][
                    'avatar']
            if avatar_data:
                img_io = io.BytesIO(avatar_data)
                img_io.seek(0)
                return send_file(img_io, mimetype='image/png')

        except Exception as e:
            print(e)
    abort(404)


@admin.route('/support/<int:id>/reviewed', methods=['POST'])
def reviewed_message(id):
    if not islogged():
        return redirect(url_for('.login', title='Login'))

    if dbase:
        try:
            cur = dbase.cursor()
            cur.execute('UPDATE support SET status = 1 WHERE id = ?', (id,))
            dbase.commit()
        except Exception as e:
            flash('Error updating the message status.', 'error')
            print(e)
            return False

    search_query = request.form.get('search', '').strip()
    return redirect(url_for('.show_support', search=search_query))


@admin.route('/add_dish/<int:dish_id>/change', methods=['POST', 'GET'])
def change_dish(dish_id):
    if not islogged():
        return redirect(url_for('.login'))
    if dbase:
        if request.method == 'POST':
            try:
                cur = dbase.cursor()
                if 'name' in request.form:
                    name = request.form.get('name')
                    cur.execute('UPDATE dishes SET name = ? WHERE dish_id = ?', (name, dish_id))

                if 'file' in request.files:
                    file = request.files.get('file')
                    if file and file.filename:
                        img = file.read()
                        cur.execute('UPDATE dishes SET image = ? WHERE dish_id = ?', (img, dish_id))

                if 'price' in request.form:
                    price = float(request.form.get('price'))
                    cur.execute('UPDATE dishes SET price = ? WHERE dish_id = ?', (price, dish_id))

                if 'description' in request.form:
                    description = request.form.get('description')
                    cur.execute('UPDATE dishes SET description = ? WHERE dish_id = ?', (description, dish_id))

                if 'status_on' in request.form:
                    cur.execute('UPDATE dishes SET status = 1 WHERE dish_id = ?', (dish_id,))

                if 'status_off' in request.form:
                    cur.execute('UPDATE dishes SET status = 0 WHERE dish_id = ?', (dish_id,))

                dbase.commit()
            except Exception as e:
                print(e)
    return redirect(url_for('.add_dish'))


@admin.route('/show_reviews', methods=['post', 'get'])
def show_reviews():
    if not islogged():
        return redirect(url_for('.login'))
    list1, list2 = [], []
    if dbase:
        try:
            cur = dbase.cursor()

            if request.method == 'POST':
                if 'sort_asc' in request.form:
                    cur.execute('select * from reviews order by id asc')
                if 'sort_desc' in request.form:
                    cur.execute('select * from reviews order by id desc')
            else:
                cur.execute('select * from reviews order by id desc')

            list1 = cur.fetchall()

            cur = dbase.cursor()
            cur.execute('select * from reply_reviews order by id asc')
            list2 = cur.fetchall()

        except Exception as e:
            print(e)
    return render_template('admin/reviews.html', title='Отзывы', menu=menu, reviews=list1, reply_list=list2)


@admin.route('/reply_reviews', methods=['POST', 'GET'])
def reply_reviews():
    if not islogged():
        return redirect(url_for('.login'))

    if dbase:
        if request.method == 'POST':
            try:
                id_user = request.form.get('id_user', '').strip()
                id_review = request.form.get('id_review', '').strip()
                name = request.form['name']
                email = request.form['email']
                message = request.form.get('reply', '').strip()

                current_datetime = datetime.now()
                tm = current_datetime.strftime("%Y-%m-%d %H:%M:%S")
                cur = dbase.cursor()

                cur.execute('INSERT INTO reply_reviews (id_user, id_review, name, email, message, time, status)'
                            'VALUES (?, ?, ?, ?, ?, ?, ?)', (id_user, id_review, name, email, message, tm, 1))
                dbase.commit()
            except Exception as e:
                print(e)

    return redirect(url_for('.show_reviews'))


@admin.route('/review/<int:id_review>/delete', methods=['POST'])
def review_remove(id_review):
    if not islogged():
        return redirect(url_for('.login'))
    if dbase:
        if request.method == 'POST':
            try:
                cur = dbase.cursor()
                cur.execute('DELETE FROM reviews WHERE id = ?;', (id_review,))
                dbase.commit()
            except Exception as e:
                flash('Error deleting the message.', 'error')
                print(e)
    return redirect(url_for('.show_reviews'))


@admin.route('/reply/<int:id_reply>/delete', methods=['POST'])
def reply_remove(id_reply):
    if not islogged():
        return redirect(url_for('.login'))
    if dbase:
        if request.method == 'POST':
            try:
                cur = dbase.cursor()
                cur.execute('DELETE FROM reply_reviews WHERE id = ?;', (id_reply,))
                dbase.commit()
            except Exception as e:
                flash('Error deleting the message.', 'error')
                print(e)
    return redirect(url_for('.show_reviews'))


# @admin.route('/visits')
# def get_visits():
#     visits = r.hgetall('visits')
#     total_visits = sum(int(count) for count in visits.values())
#     online_users = len(r.keys('online_user:*'))
#     return jsonify({
#         'total_visits': total_visits,
#         'online_users': online_users
#     })


@admin.route('/finance', methods=['POST', "GET"])
def finance():
    if not islogged():
        return redirect(url_for('.login'))
    data_time = []
    total = 0
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    date_week = date_obj - timedelta(weeks=1)
    date_month = date_obj - timedelta(days=30)
    date_year = date_obj - timedelta(days=365)
    try:
        if dbase:
            cur = dbase.cursor()
            if request.method == 'POST':
                if 'week' in request.form:
                    cur.execute('select * from orders where time >= ?', (date_week,))
                    data_time = cur.fetchall()
                    cur.execute('select sum(price) from orders where time >= ?', (date_week,))
                    total = cur.fetchone()[0] or 0
                if 'month' in request.form:
                    cur.execute('select * from orders where time >= ?', (date_month,))
                    data_time = cur.fetchall()
                    cur.execute('select sum(price) from orders where time >= ?', (date_month,))
                    total = cur.fetchone()[0] or 0
                if 'year' in request.form:
                    cur.execute('select * from orders where time >= ?', (date_year,))
                    data_time = cur.fetchall()
                    cur.execute('select sum(price) from orders where time >= ?', (date_year,))
                    total = cur.fetchone()[0] or 0
                if 'alltime' in request.form:
                    cur.execute('select * from orders')
                    data_time = cur.fetchall()
                    cur.execute('select sum(price) from orders')
                    total = cur.fetchone()[0] or 0
            else:
                cur.execute('select * from orders')
                data_time = cur.fetchall()
                cur.execute('select sum(price) from orders')
                total = cur.fetchone()[0] or 0
            data_time = [dict(item) for item in data_time]

    except Exception as e:
        print(e)

    finance_data = {}
    for entry in data_time:
        date_str = entry['time']
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').date()
        price = entry['price']

        if date in finance_data:
            finance_data[date] += price
        else:
            finance_data[date] = price

    dates = list(finance_data.keys())
    prices = list(finance_data.values())

    return render_template('admin/finance.html', title='Finance', menu=menu, total=total,
                           dates=dates, prices=prices)


@admin.route('/send_statistic/<int:total>', methods=['POST', 'GET'])
def send_statistic(total):
    if not islogged():
        return redirect(url_for('.login'))
    try:
        if dbase:
            cur = dbase.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            if request.method == 'POST':
                cur.execute('insert into visits (date, count) VALUES (?, ?)', (today, total))
                dbase.commit()
    except Exception as e:
        print(e)
    return redirect(url_for('.main'))


@admin.route('/visits_statistic', methods=['POST', 'GET'])
def visits_statistic():
    if not islogged():
        return redirect(url_for('.login'))
    list_visits = []
    total = 0
    if dbase:
        try:
            cur = dbase.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            visit_list = cur.execute('SELECT * FROM visit_statistics where visit_time = ?', (today,)).fetchall()
            for _ in visit_list:
                total += 1

            if request.method == 'POST':
                if 'digit' in request.form:
                    digit = request.form.get('digit', '').strip()
                    cur.execute('SELECT * FROM visits ORDER BY id DESC LIMIT ?', (digit,))

                if 'date' in request.form:
                    date = request.form.get('date')
                    if date == 'Последний':
                        cur.execute('SELECT * FROM visits ORDER BY id DESC LIMIT 1')
                    if date == 'Все':
                        cur.execute('SELECT * FROM visits ORDER BY id DESC')
            else:
                cur.execute('SELECT * FROM visits ORDER BY id DESC LIMIT 3')
            list_visits = cur.fetchall()
            list_visits = [dict(item) for item in list_visits]
            list_visits.reverse()


        except Exception as e:
            print(e)
    return render_template('admin/visits.html', title='Visitor Statistics', menu=menu, visits=list_visits,
                           total=total)


@admin.route('/statistic', methods=['POST', "GET"])
def statistic():
    if not islogged():
        return redirect(url_for('.login'))
    return render_template('admin/statistic.html', title='Website Statistics', menu=menu)
