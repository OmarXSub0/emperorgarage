from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file, abort
import firebase_admin 
from firebase_admin import credentials, firestore, storage , auth
from datetime import datetime
import requests
import hashlib 
import json
import io
import secrets
import os
import pyrebase
from functools import wraps
import uuid
from dotenv import load_dotenv

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY','844cac20884a4595ca8349dddea8a2a94156777b3e157aa6249b03a6a89f3b85')
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {'storageBucket': 'emperorgarage.firebasestorage.app'})

db = firestore.client()
bucket = storage.bucket()

print("connected successfully")
firebaseConfig = {
    "apiKey": "AIzaSyCbi72B8iT5P0VAvE_eix6nsuDDzlqTVWk",     
    "authDomain": "emperorgarage.firebaseapp.com",  
    "databaseURL": "https://emperorgarage-default-rtdb.firebaseio.com/", 
    "projectId": "emperorgarage",       
    "storageBucket": "emperorgarage.firebasestorage.app", 
    "messagingSenderId": "405891329254", 
    "appId": "1:405891329254:web:8c511fbcccf25fd9d01f27",
} 
firebase_py = pyrebase.initialize_app(firebaseConfig)
pyre_auth = firebase_py.auth()

@app.route('/static/placeholder.png')
def placeholder_image():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" width="185" height="200" viewBox="0 0 300 200">
        <rect width="300" height="200" fill="#f0f0f0"/>
        <text x="50%" y="50%" text-anchor="middle" dy=".3em" fill="#999" font-size="14">No Image</text>
    </svg>'''
    
    return send_file(
        io.BytesIO(svg.encode('utf-8')),
        mimetype='image/svg+xml',
        as_attachment=False
    )

@app.route('/')
def index():
    try:
        products_ref = db.collection('products').stream()
        cars = []
        parts = []
        
        for doc in products_ref:
            product = doc.to_dict()
            product['seller_id'] = doc.id
            
            images = []
            if 'image_urls' in product and product['image_urls']:
                for i in range(6): 
                    if i < len(product['image_urls']) and product['image_urls'][i]:
                        image_path = product['image_urls'][i]
                        if not image_path.startswith('http'):
                            try:
                                if 'storage.googleapis.com' in image_path:
                                    images.append(image_path)
                                else:
                                    blob = bucket.blob(image_path)
                                    image_url = blob.generate_signed_url(expiration=86400)
                                    images.append(image_url)
                            except Exception as img_error:
                                print(f"Error loading image {i} for {product.get('name')}: {img_error}")
                                images.append(None)
                        else:
                            images.append(image_path)
                    else:
                        images.append(None)
            else:
                # No images at all
                images = [None] * 6
            
            product['images'] = images
            
            if product.get('category') == 'cars':
                cars.append(product)
            else:
                parts.append(product)
        
        cars.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        parts.sort(key=lambda x: x.get('created_at', ''), reverse=True)
        
        return render_template('index.html', cars=cars, parts=parts)
        
    except Exception as e:
        print(f"Error loading products: {e}")
        import traceback
        traceback.print_exc()
        return render_template('index.html', cars=[], parts=[])

@app.route('/signup') 
def signup_page():
 return render_template('signup.html')  

@app.route('/signin') 
def signin_page():
 return render_template('signin.html')  

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        email = data.get('email')
        password = data.get('password')
        business_name = data.get('business_name')
        business_type = data.get('business_type', '')
        
        user = auth.create_user(
            email=email,
            password=password
        )
        
        seller_data = {
            'business_name': business_name,
            'email': email,
            'business_type': business_type,
            'password': password,
            'uid': user.uid,
            'created_at': datetime.now().isoformat(),
            'approved': True
        }
        
        db.collection('sellers').document(user.uid).set(seller_data)
        
        session['seller_id'] = user.uid
        session['business_name'] = business_name
        session['email'] = email
        
        return jsonify({
            'success': True, 
            'message': 'Signup successful! Redirecting to dashboard...'
        })
        
    except auth.EmailAlreadyExistsError:
        return jsonify({'success': False, 'message': 'Email already registered.'}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': 'An error occurred during signup.'}), 400
    
@app.route('/api/login', methods=['POST'])
def login():
    try:
        print("=" * 50)
        print("LOGIN REQUEST RECEIVED")
        
        # Get JSON data
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False, 
                'message': 'No data received'
            }), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        print(f"Email: {email}")
        print(f"Password received: {'Yes' if password else 'No'}")
        
        if not email or not password:
            return jsonify({
                'success': False, 
                'message': 'Email and password are required'
            }), 400
        
        fb_api_key = "AIzaSyCbi72B8iT5P0VAvE_eix6nsuDDzlqTVWk"
        rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={fb_api_key}"
        
        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }
        
        # Make request to Firebase
        response = requests.post(rest_api_url, json=payload)
        auth_result = response.json()
        
        print(f"Firebase response status: {response.status_code}")
        
        if response.status_code != 200:
            error_message = auth_result.get('error', {}).get('message', 'Invalid credentials')
            print(f"Firebase auth error: {error_message}")
            
            # Return user-friendly error
            if error_message == 'EMAIL_NOT_FOUND':
                return jsonify({
                    'success': False, 
                    'message': 'No account found with this email. Please sign up first.'
                }), 401
            elif error_message == 'INVALID_PASSWORD':
                return jsonify({
                    'success': False, 
                    'message': 'Incorrect password. Please try again.'
                }), 401
            else:
                return jsonify({
                    'success': False, 
                    'message': 'Invalid email or password'
                }), 401
        
        # Get user info from Firebase
        user_uid = auth_result.get('localId')
        id_token = auth_result.get('idToken')
        
        print(f"Firebase auth successful for UID: {user_uid}")
        
        seller_doc = db.collection('sellers').document(user_uid).get()
        
        if not seller_doc.exists:
            return jsonify({
                'success': False, 
                'message': 'Seller account not found. Please register as a seller.',
                'redirect': '/signup'
            }), 404
        
        seller_data = seller_doc.to_dict()
        
        # Check approval status
        if not seller_data.get('approved', False):
            return jsonify({
                'success': False, 
                'message': 'Account pending admin approval. You will be notified when approved.'
            }), 403
        
        session['seller_id'] = user_uid
        session['business_name'] = seller_data.get('business_name')
        session['email'] = email
        session['logged_in'] = True
        
       # print(f"Login successful for: {email}")
        #print("=" * 50)
        
        return jsonify({
            'success': True,
            'message': 'Login successful! Redirecting to dashboard...',
            'redirect': '/dashboard',
            'business_name': seller_data.get('business_name')
        })
        
    except Exception :
        print("Unexpected error during login")
       # import traceback
       # traceback.print_exc()
        #print("=" * 50)
        return jsonify({
            'success': False,
            'message': 'Server error'
        }), 500
            
@app.route('/dashboard')
def dashboard():
    try:
        seller_id = session.get('seller_id')
        
        if not seller_id:
            return redirect(url_for('/')) 

        products_ref = db.collection('products').where('seller_id', '==', seller_id).stream()
        
        products = []
        
        for doc in products_ref:
            product = doc.to_dict()
            product['id'] = doc.id
            
            if 'image_urls' in product and product['image_urls']:
                valid_images = [img for img in product['image_urls'] if img]
                product['images'] = valid_images[:6]
            else:
                product['images'] = []
            
            # Ensure other fields exist
            product['phone'] = product.get('phone', 'Not provided')
            product['location'] = product.get('location', 'Not specified')
            product['stock'] = product.get('stock', 0)
            product['description'] = product.get('description', '')
            
            products.append(product)
        
        return render_template('dashboard.html', products=products,seller_id=('seller_id'),business_name=session.get('business_name'))
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard.html', products=[])
def upload_image_to_firebase(file, folder, filename):
    blob = bucket.blob(f"{folder}/{filename}")
    blob.upload_from_file(file)
    blob.make_public()
    return blob.public_url

MAX_IMAGES = 6
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB per image

def validate_images(images):
    errors = []
    valid_images = []
    
    for img in images:
        if not img or not img.filename:
            continue
            
        # Check extension
        ext = img.filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"Invalid format: {img.filename}")
            continue
            
        # Check size
        img.seek(0, os.SEEK_END)
        size = img.tell()
        img.seek(0)
        if size > MAX_FILE_SIZE:
            errors.append(f"File too large: {img.filename}")
            continue
            
        valid_images.append(img)
    
    if len(valid_images) > MAX_IMAGES:
        errors.append(f"Maximum {MAX_IMAGES} images allowed")
        
    return valid_images, errors

@app.route('/add_product', methods=['POST'])
def add_product():
    if 'seller_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in!'})
    
    required_fields = ['name', 'category', 'price','location', 'phone', 'description']
    for field in required_fields:
        if not request.form.get(field): return jsonify({'success': False, 'message': f'Missing {field}'})
 
    try:
        field_names = ['image', 'image1', 'image2', 'image3', 'image4', 'image5']
        image_files = []
        
        for field_name in field_names:
            image_file = request.files.get(field_name)
            if image_file and image_file.filename:
                image_files.append(image_file)
        
        valid_images, errors = validate_images(image_files)
        
        if errors:
            return jsonify({'success': False, 'message': ' | '.join(errors)})
        
        if len(valid_images) == 0:
            return jsonify({'success': False, 'message': 'At least one image is required'})
        
        image_urls = [None] * 6
        for idx, image_file in enumerate(valid_images[:6]): 
            filename = f"{datetime.now().timestamp()}_{idx}_{image_file.filename}"
            image_url = upload_image_to_firebase(image_file, 'product_images', filename)
            image_urls[idx] = image_url
        
        product_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'location': request.form['location'],
            'category': request.form['category'],
            'price': float(request.form['price']),
            'description': request.form['description'],
            'stock': int(request.form.get('stock', 0)),
            'image_urls': image_urls,  # Store as list
            'seller_id': session['seller_id'],
            'created_at': datetime.now().isoformat()
        }
        
        db.collection('products').add(product_data)
        
        return jsonify({'success': True, 'message': 'Product Added!'})
    except Exception as e:
        return jsonify({'success': False, 'message': 'Prodeuct Not Added, Something Is Very Wrong Contact Developer'})
    
@app.route('/api/products/<product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        print(f"Attempting to delete product: {product_id}")
        
        if not db or not bucket:
            return jsonify({
                'success': False, 
                'message': 'Database not properly initialized'
            }), 500
        
        product_ref = db.collection('products').document(product_id)
        product = product_ref.get()
        
        if not product.exists:
            return jsonify({
                'success': False, 
                'message': 'Product not found, Refresh and try again'
            }), 404
        
        product_data = product.to_dict()
        print(f"Found product: {product_data.get('name')}")
        
        deleted_images = 0
        failed_images = 0
        
        image_fields = ['images', 'image_paths', 'image_urls']
        image_paths = []
        
        for field in image_fields:
            if field in product_data and product_data[field]:
                image_paths.extend(product_data[field])
        
        if 'main_image' in product_data and product_data['main_image']:
            main_image = product_data['main_image']
            if 'storage.googleapis.com' in main_image:
                # Extract the path after /o/ and before ?alt=
                import re
                match = re.search(r'/o/(.+?)\?', main_image)
                if match:
                    image_paths.append(match.group(1))
        
        print(f"Found {len(image_paths)} images to delete")
        
        for image_path in image_paths:
            try:
                if image_path: 
                    blob = bucket.blob(image_path)
                    blob.delete()
                    deleted_images += 1
                    print(f"Deleted image: {image_path}")
            except Exception as e:
                failed_images += 1
                print(f"Failed to delete image {image_path}: {str(e)}")
        
        product_ref.delete()
        print(f"Deleted product document: {product_id}")
        
        return jsonify({
            'success': True,
            'message': f'Product deleted successfully. Deleted {deleted_images} images.',
            'deleted_images': deleted_images,
            'failed_images': failed_images
        })
        
    except Exception as e:
        print(f"Error in delete_product")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'Server error'
        }), 500
        
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/api/brands', methods=['GET'])
def get_brands():
    """Get list of car brands"""
    brands = [
         {'name': 'BMW', 'code': 'bmw'},
         {'name': 'Audi', 'code': 'audi'},
         {'name': 'Mercedes-Benz', 'code': 'mercedes-benz'},
         {'name': 'Volkswagen', 'code': 'volkswagen'},
         {'name': 'Toyota', 'code': 'toyota'},
         {'name': 'Ford', 'code': 'ford'},
         {'name': 'Honda', 'code': 'honda'},
         {'name': 'Chevrolet', 'code': 'chevrolet'},
         {'name': 'Nissan', 'code': 'nissan'},
         {'name': 'Hyundai', 'code': 'hyundai'},
         {'name': 'Kia', 'code': 'kia'},
         {'name': 'Daewoo', 'code': 'daewoo'},
         {'name': 'Mazda', 'code': 'mazda'},
         {'name': 'Lexus', 'code': 'lexus'},
         {'name': 'Volvo', 'code': 'volvo'},
         {'name': 'Jaguar', 'code': 'jaguar'},
         {'name': 'Land-Rover', 'code': 'land-rover'},
         {'name': 'Mclaren', 'code': 'mclaren'},
         {'name': 'Maserati', 'code': 'maserati'},
         {'name': 'Dodge', 'code': 'dodge'},
         {'name': 'Ram', 'code': 'ram'},
         {'name': 'Jeep', 'code': 'jeep'},
         {'name': 'GMC', 'code': 'gmc'},
         {'name': 'Cadillac', 'code': 'cadillac'},
         {'name': 'Acura', 'code': 'acura'},
         {'name': 'Mitsubishi', 'code': 'mitsubishi'},
         {'name': 'Suzuki', 'code': 'suzuki'},
         {'name': 'Ferrari', 'code': 'ferrari'},
         {'name': 'Lamborghini', 'code': 'lamborghini'},
         {'name': 'Porsche', 'code': 'porsche'},
         {'name': 'Tesla', 'code': 'tesla'}
    ]
    return jsonify(brands)

if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=true)
