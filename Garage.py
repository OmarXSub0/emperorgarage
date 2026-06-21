import io
import json
import os
import re
from datetime import datetime
from functools import wraps

import requests
from dotenv import load_dotenv
from flask import (
    Flask, abort, jsonify, redirect, render_template,
    request, send_file, session, url_for
)
from waitress import serve

import firebase_admin
from firebase_admin import auth
from firebase_admin import credentials as fb_credentials
from google.cloud import firestore, storage

load_dotenv()

app = Flask(__name__)

app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    raise SystemExit(
        "FLASK_SECRET_KEY is not set. Add it to your .env file.\n"
        "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
    )

KEY_PATH = os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', './serviceAccountKey.json')

db = None
bucket = None
storage_client = None


def validate_key_file(path):
    """Sanity-check the service account key file before trying to use it."""
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
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False

    required_fields = ['private_key', 'private_key_id', 'client_email', 'project_id']
    missing = [field for field in required_fields if field not in data]
    if missing:
        print(f"❌ Missing required fields: {missing}")
        return False

    if 'BEGIN PRIVATE KEY' not in data['private_key']:
        print("❌ Invalid private key format")
        return False

    print("✅ Key file appears valid")
    print(f"   Service Account: {data['client_email']}")
    print(f"   Project: {data['project_id']}")
    return True


def init_google_cloud_clients(key_path):
    """
    Initialize Firestore, Cloud Storage, and the Firebase Admin SDK from a single
    service account key file. Raises on any failure instead of swallowing the
    error, so a misconfigured deployment fails loudly at startup rather than
    silently running with db/bucket left as None.
    """
    global db, bucket, storage_client

    if not validate_key_file(key_path):
        raise RuntimeError(f"Service account key file at '{key_path}' is missing or invalid")

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = key_path

    with open(key_path) as f:
        key_data = json.load(f)
    project_id = key_data['project_id']

    bucket_name = os.environ.get('STORAGE_BUCKET', f"{project_id}.firebasestorage.app")

    print("🔄 Initializing Firestore...")
    db = firestore.Client(project=project_id)
    print("✅ Firestore client ready")

    print("🔄 Initializing Cloud Storage...")
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)

    if not bucket.exists():
        raise RuntimeError(f"Storage bucket '{bucket_name}' not found or not accessible")
    print(f"✅ Storage bucket '{bucket_name}' exists")

    fb_cred = fb_credentials.Certificate(key_path)
    firebase_admin.initialize_app(fb_cred, {
        "databaseURL": os.environ.get(
            'FIREBASE_DATABASE_URL', f"https://{project_id}-default-rtdb.firebaseio.com/"
        ),
        "storageBucket": bucket_name
    })
    print("✅ Firebase Admin SDK initialized")
    print("✅ Google Cloud clients initialized")


try:
    init_google_cloud_clients(KEY_PATH)
except Exception:
    import traceback
    traceback.print_exc()
    raise SystemExit(
        "Failed to initialize Google Cloud / Firebase clients -- "
        "fix the error above before starting the server."
    )

firebaseConfig = {
    "apiKey": os.environ.get('FIREBASE_WEB_API_KEY'),
    "authDomain": "emperorgarage.firebaseapp.com",
    "databaseURL": "https://emperorgarage-default-rtdb.firebaseio.com/",
    "projectId": "emperorgarage",
    "storageBucket": "emperorgarage.firebasestorage.app",
    "messagingSenderId": "405891329254",
    "appId": "1:405891329254:web:8c511fbcccf25fd9d01f27",
}


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'seller_id' not in session:
            return jsonify({'error': 'Login required'}), 401
        return f(*args, **kwargs)
    return decorated_function


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
            if product.get('image_urls'):
                for i in range(6):
                    image_path = product['image_urls'][i] if i < len(product['image_urls']) else None
                    if not image_path:
                        images.append(None)
                        continue

                    if image_path.startswith('http') or 'storage.googleapis.com' in image_path:
                        images.append(image_path)
                    else:
                        try:
                            blob = bucket.blob(image_path)
                            images.append(blob.generate_signed_url(expiration=86400))
                        except Exception as img_error:
                            print(f"Error loading image {i} for {product.get('name')}: {img_error}")
                            images.append(None)
            else:
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


@app.route('/api/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()

        email = data.get('email')
        password = data.get('password')
        business_name = data.get('business_name')
        business_type = data.get('business_type', '')

        if not email or not password or not business_name:
            return jsonify({'success': False, 'message': 'Email, password, and business name are required.'}), 400

        user = auth.create_user(email=email, password=password)

        seller_data = {
            'business_name': business_name,
            'email': email,
            'business_type': business_type,
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
        print(f"Signup error: {e}")
        return jsonify({'success': False, 'message': 'An error occurred during signup.'}), 400


@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No data received'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        if not email or not password:
            return jsonify({'success': False, 'message': 'Email and password are required'}), 400

        fb_api_key = os.environ.get('FIREBASE_WEB_API_KEY')
        rest_api_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={fb_api_key}"

        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(rest_api_url, json=payload)
        auth_result = response.json()

        if response.status_code != 200:
            error_message = auth_result.get('error', {}).get('message', 'Invalid credentials')
            print(f"Firebase auth error: {error_message}")

            if error_message == 'EMAIL_NOT_FOUND':
                return jsonify({
                    'success': False,
                    'message': 'No account found with this email. Please sign up first.'
                }), 401
            elif error_message == 'INVALID_PASSWORD':
                return jsonify({'success': False, 'message': 'Incorrect password. Please try again.'}), 401
            else:
                return jsonify({'success': False, 'message': 'Invalid email or password'}), 401

        user_uid = auth_result.get('localId')
        seller_doc = db.collection('sellers').document(user_uid).get()

        if not seller_doc.exists:
            return jsonify({
                'success': False,
                'message': 'Seller account not found. Please register as a seller.',
                'redirect': '/signup'
            }), 404

        seller_data = seller_doc.to_dict()

        if not seller_data.get('approved', False):
            return jsonify({
                'success': False,
                'message': 'Account pending admin approval. You will be notified when approved.'
            }), 403

        session['seller_id'] = user_uid
        session['business_name'] = seller_data.get('business_name')
        session['email'] = email
        session['logged_in'] = True

        return jsonify({
            'success': True,
            'message': 'Login successful! Redirecting to dashboard...',
            'redirect': '/dashboard',
            'business_name': seller_data.get('business_name')
        })

    except Exception as e:
        print(f"Unexpected error during login: {e}")
        return jsonify({'success': False, 'message': 'Server error'}), 500


@app.route('/dashboard')
def dashboard():
    seller_id = session.get('seller_id')

    if not seller_id:
        return redirect(url_for('index'))

    try:
        products_ref = db.collection('products').where('seller_id', '==', seller_id).stream()
        products = []

        for doc in products_ref:
            product = doc.to_dict()
            product['id'] = doc.id

            if product.get('image_urls'):
                product['images'] = [img for img in product['image_urls'] if img][:6]
            else:
                product['images'] = []

            product['phone'] = product.get('phone', 'Not provided')
            product['location'] = product.get('location', 'Not specified')
            product['stock'] = product.get('stock', 0)
            product['description'] = product.get('description', '')

            products.append(product)

        return render_template(
            'dashboard.html',
            products=products,
            seller_id=seller_id,
            business_name=session.get('business_name')
        )

    except Exception as e:
        print(f"Dashboard error: {e}")
        return render_template('dashboard.html', products=[], seller_id=seller_id,
                                business_name=session.get('business_name'))


def upload_image_to_firebase(file, folder, filename):
    blob = bucket.blob(f"{folder}/{filename}")
    blob.upload_from_file(file)
    blob.make_public()
    return blob.public_url


MAX_IMAGES = 6
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024 


def validate_images(images):
    errors = []
    valid_images = []

    for img in images:
        if not img or not img.filename:
            continue

        if '.' not in img.filename:
            errors.append(f"Invalid format: {img.filename}")
            continue

        ext = img.filename.rsplit('.', 1)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            errors.append(f"Invalid format: {img.filename}")
            continue

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
@login_required
def add_product():
    required_fields = ['name', 'category', 'price', 'location', 'phone', 'description']
    for field in required_fields:
        if not request.form.get(field):
            return jsonify({'success': False, 'message': f'Missing {field}'})

    try:
        price = float(request.form['price'])
    except ValueError:
        return jsonify({'success': False, 'message': 'Price must be a number'})

    try:
        stock = int(request.form.get('stock', 0))
    except ValueError:
        return jsonify({'success': False, 'message': 'Stock must be a whole number'})

    try:
        field_names = ['image', 'image1', 'image2', 'image3', 'image4', 'image5']
        image_files = [request.files.get(f) for f in field_names]
        image_files = [f for f in image_files if f and f.filename]

        valid_images, errors = validate_images(image_files)
        if errors:
            return jsonify({'success': False, 'message': ' | '.join(errors)})

        if len(valid_images) == 0:
            return jsonify({'success': False, 'message': 'At least one image is required'})

        image_urls = [None] * 6
        for idx, image_file in enumerate(valid_images[:6]):
            filename = f"{datetime.now().timestamp()}_{idx}_{image_file.filename}"
            image_urls[idx] = upload_image_to_firebase(image_file, 'product_images', filename)

        product_data = {
            'name': request.form['name'],
            'phone': request.form['phone'],
            'location': request.form['location'],
            'category': request.form['category'],
            'price': price,
            'description': request.form['description'],
            'stock': stock,
            'image_urls': image_urls,
            'seller_id': session['seller_id'],
            'created_at': datetime.now().isoformat()
        }

        db.collection('products').add(product_data)

        return jsonify({'success': True, 'message': 'Product Added!'})
    except Exception as e:
        print(f"Add product error: {e}")
        return jsonify({'success': False, 'message': 'Product not added. Something went wrong -- contact the developer.'})


@app.route('/api/products/<product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    try:
        product_ref = db.collection('products').document(product_id)
        product = product_ref.get()

        if not product.exists:
            return jsonify({'success': False, 'message': 'Product not found, refresh and try again'}), 404

        product_data = product.to_dict()

        if product_data.get('seller_id') != session.get('seller_id'):
            return jsonify({'success': False, 'message': 'Not authorized to delete this product'}), 403

        deleted_images = 0
        failed_images = 0

        image_paths = []
        for field in ('images', 'image_paths', 'image_urls'):
            if product_data.get(field):
                image_paths.extend(product_data[field])

        if product_data.get('main_image'):
            main_image = product_data['main_image']
            if 'storage.googleapis.com' in main_image:
                match = re.search(r'/o/(.+?)\?', main_image)
                if match:
                    image_paths.append(match.group(1))

        for image_path in image_paths:
            if not image_path:
                continue
            try:
                bucket.blob(image_path).delete()
                deleted_images += 1
            except Exception as e:
                failed_images += 1
                print(f"Failed to delete image {image_path}: {e}")

        product_ref.delete()

        return jsonify({
            'success': True,
            'message': f'Product deleted successfully. Deleted {deleted_images} images.',
            'deleted_images': deleted_images,
            'failed_images': failed_images
        })

    except Exception as e:
        print(f"Error in delete_product: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': 'Server error'}), 500


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
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    if debug_mode:
        app.run(host='0.0.0.0', port=8080, debug=True)
    else:
        serve(app, host='0.0.0.0', port=8080, threads=8)
