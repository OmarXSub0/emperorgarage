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
from waitress import serve
from functools import wraps
import uuid
from dotenv import load_dotenv
import grpc
from google.cloud import firestore
from google.oauth2 import service_account
from google.auth import default
from google.auth.transport.requests import Request
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', '844cac20884a4595ca8349dddea8a2a94156777b3e157aa6249b03a6a89f3b85')

SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "emperorgarage",
    "private_key_id": "b00c63f7e233a970efea9b9491a8a2649b2d021b",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQDaw2UAaFsKD8YH\nDKJptyZgpsnxkMJnVKNitJIPtgAidCk8cpb0BTxNnrJieX7pvjHo1zpIvb+yn318\nTd2Zll3Zluixr5dgueHPescRmIqMydH0da0W5TYzxioyYAqlAf3mgywVkH+XshFD\ndcuQTltXA9/29cQ8+dBIwYikjoSWitXIlUfMd6EuC80VBJFeTkBGvosCV/yxBKXQ\ni/MDZ4ePsG1QO/OtdYc+sef6rB+LyW/HG3ZMxpV168SUT4UVBR/ib049dvjoJJgg\n3DCzaER0sS2NvOYLbAUHi7Td1oRRxBBDjDwWZ0BDaLDYg30O1JKIFe1SbAGTj1Rv\nt915hgFtAgMBAAECggEAAO8OFpEbeGDGW9/YLqLXQVjc6lDPn6DLHMAAEpyYhg0g\nYu9rSQnfrsYjZUu2+Lj03hVTHJ3gvFq1bqsna8EqT+Q2xJFnEETi25+ey2qvBrhS\n0twQu9UJJPHu2q2xxfAK/SmorcPi44shSzwsvQY0mhu8YEG+z3LSioj29BreooTd\nrEXHf3K+ffojUi2DvqGo86/tZ/ZGZy2KE7rFPcqQd61/UdaaNP8MtMx4TlGtYYVD\nB2pLF8RPl8QU1n6ZoxNBvkbfavctvYYWbfR/sG8AtB3trbM2u7EC564jUSjv5TOp\nlMFPRpg5DwEBP7fj4yAU+QbIwBvlcV7um2JbYB9AkQKBgQD55zB2LMMjTZuGgBzs\nTvNd7EifJWTEk8J+n9stA68Vs5bYQZx7x6YJZJ/8U5lVyQ1meRTlJX7rvcTnEiJk\nBBCRDihedXfQn9DH52ZOp98qXwO7Hzv/hvkXta9/r77Pdaw62koT3qUxmk48l82E\nJ4xa8d8pU5UAOdBHN5km/qMynQKBgQDgGbdjX+JNLIB5idhjRISsgIxBhsPB4V8z\n+/ucE5KwUqNOvp9tSKKx7DX4qDuOU6XMvvmE+SfDRZrCcYhKUGxfq616kTsjEG9P\nJ+kNzZcpEwpJ0h6WiFfX3koFx5jqCZEN/oUo/eEH0Yndg51ljsYuy0iV4WwenkPD\nCQZ0J36pEQKBgQDQJiN0WwZSUmL3XaA5p+0HTzaR8DiFj7lRdN6/GLFttv8usz+e\nzgVbD4g+SHeQP3083B9uWZPk0VS/Tph8i/IskAlJ3Dfm+iaRSwko/KRiC2/1HSgB\nRzAU8ozyIrUg4ZeKEaXf9PPNZAREbgCNUc+TNKE3L9oMrRrxJrsXAsN19QKBgHQ1\nwby9nzvH5QOhsN2hTW+q5ZChUug6d8UcWZjRKZNX9ynBfikMrpm3VTGSA/hFdkgb\njIchMTZ45M0KVNO8qsZd34Mcxt7jCeWxW5B12XpKTl6DoKsNHwhpVFd07t4GgfsQ\nznq4VLZaObTuKHPeuvTPI9/dWtTx20/LYVZgmLURAoGATobybu6zXD3IdXyQ9eD0\ncpi5kyEzXMqeo8aAvPMs2UzHyR9QRYvp9VNNjhD+7GBjqPffeWyhG6FothZoKar/\nb0k/mXS5zBA5+VSTWXM19zM9t9a2leath+ZNICGTuIOJcFj0W6oQNGrcg3Yg+VJm\nQbQ+oWRcpWriCyguOAYfCcU=\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@emperorgarage.iam.gserviceaccount.com",
    "client_id": "118440247245060735413",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40emperorgarage.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
}

try:
    cred = firebase_credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://emperorgarage-default-rtdb.firebaseio.com/",
        "storageBucket": "emperorgarage.firebasestorage.app"
    })
    pyre_auth = auth
    print("✅ Firebase Admin SDK initialized")
except Exception as e:
    print(f"⚠️ Firebase Admin SDK error: {e}")
    pyre_auth = None

def init_google_cloud_clients():
    """Initialize Firestore and Storage clients with hardcoded credentials"""
    try:
        print("🔄 Creating Google Cloud credentials...")
        
        credentials = service_account.Credentials.from_service_account_info(
            SERVICE_ACCOUNT_KEY,
            scopes=['https://www.googleapis.com/auth/cloud-platform']
        )
        
        if credentials.expired:
            credentials.refresh(Request())
        print("✅ Credentials verified")
        
        print("🔄 Initializing Firestore...")
        firestore_client = firestore.Client(
            credentials=credentials,
            project='emperorgarage'
        )
        print("✅ Firestore client ready")
        
        print("🔄 Initializing Cloud Storage...")
        storage_client = storage.Client(
            credentials=credentials,
            project='emperorgarage'
        )
        
        bucket_name = "emperorgarage.firebasestorage.app"
        bucket = storage_client.bucket(bucket_name)
        
        if bucket.exists():
            print(f"✅ Storage bucket '{bucket_name}' exists")
        else:
            print(f"⚠️ Bucket '{bucket_name}' not found or not accessible")
            # Try to list available buckets
            print("Available buckets:")
            for b in storage_client.list_buckets():
                print(f"  - {b.name}")
        
        print("✅ Google Cloud clients initialized")
        return firestore_client, storage_client, bucket, credentials
        
    except Exception as e:
        print(f"❌ Error initializing Google Cloud clients: {e}")
        return None, None, None, None

firestore_client, storage_client, storage_bucket, google_creds = init_google_cloud_clients()

KEY_PATH = './serviceAccountKey.json'

def validate_key_file(path):
    """Check if the key file is valid"""
    print(f"Checking: {path}")
    
    if not os.path.exists(path):
        print("❌ File does not exist")
        return False
    
    size = os.path.getsize(path)
    print(f"📄 File size: {size} bytes")
    if size < 100:
        print("❌ File is too small - likely corrupted")
        return False
    
    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        required_fields = ['private_key', 'private_key_id', 'client_email', 'project_id']
        missing = [f for f in required_fields if f not in data]
        if missing:
            print(f"❌ Missing required fields: {missing}")
            return False
        
        private_key = data['private_key']
        if 'BEGIN PRIVATE KEY' not in private_key:
            print("❌ Invalid private key format")
            return False
        
        print("✅ Key file appears valid")
        print(f"   Service Account: {data['client_email']}")
        print(f"   Project: {data['project_id']}")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

validate_key_file(KEY_PATH)

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = './serviceAccountKey.json'

try:
    default_creds, project = default()
    if default_creds.expired:
        default_creds.refresh(Request())
    print("✅ Application Default Credentials ready")
    print(f"   Project: {project}")
except DefaultCredentialsError as e:
    print(f"⚠️ ADC not available: {e}")

firebaseConfig = {
    "apiKey": "AIzaSyCbi72B8iT5P0VAvE_eix6nsuDDzlqTVWk",     
    "authDomain": "emperorgarage.firebaseapp.com",  
    "databaseURL": "https://emperorgarage-default-rtdb.firebaseio.com/", 
    "projectId": "emperorgarage",       
    "storageBucket": "emperorgarage.firebasestorage.app", 
    "messagingSenderId": "405891329254", 
    "appId": "1:405891329254:web:8c511fbcccf25fd9d01f27",
} 


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
    app.run(app, host='0.0.0.0', port=8080, threads=8)
