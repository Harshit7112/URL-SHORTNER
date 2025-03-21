from flask import Flask, request, redirect, render_template, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
import random
import string
import os

app = Flask(__name__)

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Database model for URLs
class URL(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_url = db.Column(db.String(500), nullable=False)
    short_code = db.Column(db.String(6), unique=True, nullable=False)
    clicks = db.Column(db.Integer, default=0)

# Create the database tables
with app.app_context():
    db.create_all()

# Function to generate a random 6-character short code
def generate_short_code():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(6))

# Reusable function to shorten a URL
def shorten_url(original_url):
    # Check if URL already exists
    existing_url = URL.query.filter_by(original_url=original_url).first()
    if existing_url:
        return existing_url.short_code
    
    # Generate unique short code
    while True:
        short_code = generate_short_code()
        if not URL.query.filter_by(short_code=short_code).first():
            break
    
    # Save to database
    new_url = URL(original_url=original_url, short_code=short_code)
    db.session.add(new_url)
    db.session.commit()
    return short_code

# Homepage: Shorten URL
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        original_url = request.form['url']
        short_code = shorten_url(original_url)
        short_url = request.host_url + short_code
        return render_template('index.html', short_url=short_url)
    return render_template('index.html')

# Redirect short URL to original URL
@app.route('/<short_code>')
def redirect_url(short_code):
    url = URL.query.filter_by(short_code=short_code).first()
    if url:
        url.clicks += 1
        db.session.commit()
        return redirect(url.original_url)
    return "URL not found", 404

# Stats page: Show click counts
@app.route('/stats')
def stats():
    urls = URL.query.all()
    return render_template('stats.html', urls=urls)

# API endpoint to shorten URLs
@app.route('/api/shorten', methods=['POST'])
def api_shorten():
    data = request.json
    original_url = data.get('url')
    if not original_url:
        return jsonify({'error': 'URL is required'}), 400
    short_code = shorten_url(original_url)
    short_url = request.host_url + short_code
    return jsonify({'short_url': short_url})

if __name__ == '__main__':
    app.run(debug=True)