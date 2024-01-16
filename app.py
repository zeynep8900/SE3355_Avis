
from flask import Flask, redirect, render_template, request, session, url_for, flash
from datetime import datetime
from passlib.hash import sha256_crypt  
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
import re
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash








app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db = SQLAlchemy(app)

app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

migrate = Migrate(app, db)

def initialize_db():
    with app.app_context():
        db.create_all()


initialize_db()



class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    country = db.Column(db.String(50))  
    city = db.Column(db.String(50)) 
    def __repr__(self):
        return str(self.__dict__)

sql_insert = "INSERT INTO user (username, email, password, country, city) VALUES (?, ?, ?, ?, ?)"




avis_locations = [
    {'name': 'İzmir Alsancak Şehir', 'address': 'İsmet Kaptan Mh, Gaziosmanpaşa Bulvarı N:7 Hilton İzmir 2.blok Z03, 35210 Konak/İzmir'},
    {'name': 'AVIS KARAVAN İZMİR', 'address': 'Dokuz Eylül Mah. 695 Sok. No:36/C Sarnıç Gaziemir / İzmir'},

]


products = [
    {"id": 1,"type": "EKONOMİK", "name": "Renault Clio", "price": 1914.18, "transmission": "Manuel", "deposit": "2,500 TL Depozito", "mileage": "1000 km", "age": "21 Yaş Ve Üstü","image_url": "https://www.avis.com.tr/Avis/media/Avis/Cars/b-renault-clio.png"},
    {"id": 2,"type": "EKONOMİK", "name": "Fiat Egea", "price": 2071.03 , "transmission": "Manuel", "deposit": "2,500 TL Depozito", "mileage": "1000 km", "age": "21 Yaş Ve Üstü", "image_url": "https://www.avis.com.tr/Avis/media/Avis/Cars/n-fiat-egea.png"},
    {"id": 3,"type": "EKONOMİK", "name": "Renault Clio AT", "price": 2179.64 , "transmission": "Otomatik", "deposit": "2,500 TL Depozito", "mileage": "1000 km", "age": "21 Yaş Ve Üstü", "image_url": "https://www.avis.com.tr/Avis/media/Avis/Cars/f-renault-clio-at.png"},
  
]



Session(app)
app.secret_key = 'your_secure_and_unique_key'  




@app.route('/', methods=['GET', 'POST'])
def index():
    print(f"Request Method: {request.method}")

    

    if request.method == 'POST':
        print("Inside POST block")
        
        if 'pickupLocation' in request.form and 'pickupDate' in request.form and 'returnLocation' in request.form and 'returnDate' in request.form:
            print("Form fields present")
            
            return redirect(url_for('search'))

    return render_template('index.html', locations=avis_locations)

def product_is_available(product, pickup_location, pickup_date, return_location, return_date):

    return True

@app.route('/search', methods=['GET', 'POST'])
def search():

    if request.method == 'POST':

        pickup_location = request.form.get('pickupLocation')
        return_location = request.form.get('returnLocation')
        pickup_date_str = request.form.get('pickupDate')
        return_date_str = request.form.get('returnDate')

        pickup_date = datetime.strptime(pickup_date_str, '%Y-%m-%d') if pickup_date_str else None
        return_date = datetime.strptime(return_date_str, '%Y-%m-%d') if return_date_str else None

        session['pickup_location'] = pickup_location
        session['return_location'] = return_location
        session['pickup_date'] = pickup_date_str
        session['return_date'] = return_date_str

    filtered_products = products

    if session.get('pickup_date') and session.get('return_date'):
        filtered_products = [product for product in filtered_products if
                             product_is_available(product, session['pickup_location'], session['pickup_date'], session['return_location'], session['return_date'])]

    sorted_products = sorted(filtered_products, key=lambda x: x['price'])


    days_difference = (return_date - pickup_date).days if pickup_date and return_date else None


    return render_template('search.html', products=sorted_products, search_info=session, days_difference=days_difference)





@app.route('/ara', methods=['POST'])
def ara():

    search_query = request.form.get('product_search')

    filtered_products = [product for product in products if
                         search_query.lower() in product['name'].lower() or search_query.lower() in str(product['price'])]


    return render_template('search.html', products=filtered_products, search_info=session)

@app.route('/rent/<int:product_id>')
def rent(product_id):

    selected_product = next((product for product in products if product['id'] == product_id), None)

    if selected_product:

        return render_template('search.html', product=selected_product, search_info=session)
    else:

        return render_template('not_found.html')

@app.route('/login', methods=['GET', 'POST'])
def redirect_to_login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']


        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user'] = {'id': user.id, 'username': user.username, 'email': user.email}
            flash('Başarıyla giriş yaptınız.', 'success')
            return redirect(url_for('index'))
        else:
            flash('Geçersiz e-posta veya şifre', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():

    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirmPassword']
        country = request.form['country']
        city = request.form['city']

        if (
            len(password) < 8
            or not re.search("[0-9]", password)
            or not re.search("[^a-zA-Z0-9]", password)
        ):
            return render_template(
                'signup.html',
                error='Şifre en az 8 karakter içermeli, 1 rakam ve 1 alfanümerik olmayan karakter içermelidir'
            )

 
        if password != confirm_password:
            return render_template('signup.html', error='Şifreler uyuşmuyor')


        new_user = User(
            username=username,
            email=email,
            password=generate_password_hash(password, method="pbkdf2:sha256:600000"),
            country=country,
            city=city
        )


        db.session.add(new_user)
        db.session.commit()



        return redirect(url_for('redirect_to_login'))

        

    return render_template('signup.html')



@app.route('/giris-yap', methods=['POST'])
def giris_yap():
    email = request.form.get('email')
    password = request.form.get('password')

    if not email or not password:
        flash('E-posta veya şifre eksik', 'danger')
        return render_template('login.html')

    user = User.query.filter_by(email=email).first()

    print(user.password)
    if user and check_password_hash(user.password, password):
        session['user'] = {'id': user.id, 'username': user.username, 'email': user.email}
        flash('Başarıyla giriş yaptınız.', 'success')
        return redirect(url_for('index'))

    flash('Geçersiz e-posta veya şifre', 'danger')
    return render_template('login.html')




    
    


    

if __name__ == '__main__':
    app.run(debug=True)