from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import psycopg2
import psycopg2.extras
import requests
import base64
import re
import os

app = Flask(__name__)

# ==========================================
# 🚀 1. यहाँ अपनी KEYS डालें (बस यही दो लाइन बदलनी हैं)
# ==========================================
DATABASE_URL = "postgresql://neondb_owner:npg_DQIh28ckflRN@ep-odd-sunset-apwike5e-pooler.c-7.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
IMGBB_API_KEY = "08980c6f8228259ac408fe7f0a67fa45"
# ==========================================

# 🚀 PRO SEO TRICK: Title को URL (Slug) में बदलने का फ़िल्टर
@app.template_filter('slugify')
def slugify(s):
    s = str(s).lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s if s else "news"

# 🚀 Cloud Database Connection
def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL)
    return conn

# 🚀 Auto-Create Table in Cloud (पहली बार रन होने पर टेबल बनाएगा)
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_path TEXT,
            seo_tags TEXT,
            status TEXT DEFAULT 'published',
            category TEXT DEFAULT 'General',
            views INTEGER DEFAULT 0,
            react_fire INTEGER DEFAULT 0,
            react_shock INTEGER DEFAULT 0,
            react_sad INTEGER DEFAULT 0,
            react_angry INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    cursor.close()
    conn.close()

# सर्वर स्टार्ट होते ही डेटाबेस चेक करेगा
init_db() 


@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM posts WHERE status='published' ORDER BY created_at DESC")
    posts = cursor.fetchall()
    conn.close()
    return render_template('index.html', posts=posts, current_category='Home')

@app.route('/category/<cat_name>')
def category_posts(cat_name):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM posts WHERE status='published' AND category=%s ORDER BY created_at DESC", (cat_name,))
    posts = cursor.fetchall()
    conn.close()
    return render_template('index.html', posts=posts, current_category=cat_name)

# 🚀 SEO URL Route
@app.route('/article/<int:post_id>')
@app.route('/article/<int:post_id>/<slug>')
def article(post_id, slug=None):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    cursor.execute('UPDATE posts SET views = views + 1 WHERE id = %s', (post_id,))
    conn.commit()
    
    cursor.execute('SELECT * FROM posts WHERE id = %s', (post_id,))
    post = cursor.fetchone()
    
    related_posts = []
    if post:
        cursor.execute('''
            SELECT * FROM posts 
            WHERE category = %s AND id != %s AND status = 'published' 
            ORDER BY created_at DESC LIMIT 3
        ''', (post['category'], post_id))
        related_posts = cursor.fetchall()
        
    conn.close()
    return render_template('article.html', post=post, related_posts=related_posts)

# इमोजी रिएक्शन API
@app.route('/react/<int:post_id>/<reaction_type>', methods=['POST'])
def react(post_id, reaction_type):
    valid_reactions = ['react_fire', 'react_shock', 'react_sad', 'react_angry']
    if reaction_type in valid_reactions:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute(f'UPDATE posts SET {reaction_type} = {reaction_type} + 1 WHERE id = %s', (post_id,))
        conn.commit()
        
        cursor.execute(f'SELECT {reaction_type} FROM posts WHERE id = %s', (post_id,))
        new_count = cursor.fetchone()[reaction_type]
        conn.close()
        return jsonify({'success': True, 'new_count': new_count})
    return jsonify({'success': False})

# इन्फिनिट स्क्रॉल API
@app.route('/api/next_post/<int:current_id>/<category>')
def next_post(current_id, category):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT * FROM posts 
        WHERE category = %s AND id < %s AND status = 'published' 
        ORDER BY id DESC LIMIT 1
    ''', (category, current_id))
    post = cursor.fetchone()
    conn.close()
    
    if post:
        post_dict = dict(post)
        post_dict['slug'] = slugify(post['title'])
        return jsonify(post_dict)
    return jsonify({'error': 'No more posts'})

# एडमिन पैनल
@app.route('/my-secret-admin-999', methods=('GET', 'POST'))
def admin():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        seo_tags = request.form['seo_tags']
        status = request.form['status']
        category = request.form['category']
        
        image_url = ""
        # 🚀 2. ImgBB API Upload Logic
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '':
                payload = {
                    "key": IMGBB_API_KEY,
                    "image": base64.b64encode(file.read()).decode('utf-8')
                }
                res = requests.post("https://api.imgbb.com/1/upload", data=payload)
                if res.status_code == 200:
                    image_url = res.json()['data']['url'] # फोटो का क्लाउड लिंक मिल गया

        if title and content:
            cursor.execute('''
                INSERT INTO posts (title, content, image_path, seo_tags, status, category) 
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', (title, content, image_url, seo_tags, status, category))
            conn.commit()
            return redirect(url_for('admin'))

    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()
    
    cursor.execute('SELECT SUM(views) FROM posts')
    total_views_result = cursor.fetchone()
    total_views = total_views_result['sum'] if total_views_result['sum'] else 0
    
    conn.close()
    return render_template('admin.html', posts=posts, total_views=total_views)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM posts WHERE id = %s', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# 🚀 SITEMAP ROUTE (Google के लिए)
@app.route('/sitemap.xml')
def sitemap():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, title, created_at FROM posts WHERE status='published' ORDER BY created_at DESC")
    posts = cursor.fetchall()
    conn.close()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url>\n    <loc>{request.url_root}</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    
    for post in posts:
        slug = slugify(post["title"])
        date_str = post["created_at"].strftime('%Y-%m-%d') if post["created_at"] else ""
        xml += f'  <url>\n    <loc>{request.url_root}article/{post["id"]}/{slug}</loc>\n'
        xml += f'    <lastmod>{date_str}</lastmod>\n'
        xml += f'    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
        
    xml += '</urlset>'
    return Response(xml, mimetype='application/xml')

# 🚀 ROBOTS.TXT ROUTE
@app.route('/robots.txt')
def robots():
    content = "User-agent: *\nAllow: /\n\n"
    content += f"Sitemap: {request.url_root}sitemap.xml"
    return Response(content, mimetype='text/plain')

if __name__ == '__main__':
    app.run(debug=True)
