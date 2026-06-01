from flask import Flask, render_template, request, redirect, url_for, jsonify, Response
import sqlite3
import os
import re
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# 🚀 PRO SEO TRICK: Title को URL (Slug) में बदलने का फ़िल्टर
@app.template_filter('slugify')
def slugify(s):
    s = str(s).lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    s = re.sub(r'[\s_-]+', '-', s)
    s = re.sub(r'^-+|-+$', '', s)
    return s if s else "news"

def get_db_connection():
    conn = sqlite3.connect('news.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts WHERE status='published' ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template('index.html', posts=posts, current_category='Home')

@app.route('/category/<cat_name>')
def category_posts(cat_name):
    conn = get_db_connection()
    posts = conn.execute("SELECT * FROM posts WHERE status='published' AND category=? ORDER BY created_at DESC", (cat_name,)).fetchall()
    conn.close()
    return render_template('index.html', posts=posts, current_category=cat_name)

# 🚀 SEO URL Route (उदा: /article/1/maruti-car-launch)
@app.route('/article/<int:post_id>')
@app.route('/article/<int:post_id>/<slug>')
def article(post_id, slug=None):
    conn = get_db_connection()
    conn.execute('UPDATE posts SET views = views + 1 WHERE id = ?', (post_id,))
    conn.commit()
    post = conn.execute('SELECT * FROM posts WHERE id = ?', (post_id,)).fetchone()
    
    related_posts = []
    if post:
        category = post['category']
        related_posts = conn.execute('''
            SELECT * FROM posts 
            WHERE category = ? AND id != ? AND status = 'published' 
            ORDER BY created_at DESC LIMIT 3
        ''', (category, post_id)).fetchall()
    conn.close()
    return render_template('article.html', post=post, related_posts=related_posts)

# इमोजी रिएक्शन API
@app.route('/react/<int:post_id>/<reaction_type>', methods=['POST'])
def react(post_id, reaction_type):
    valid_reactions = ['react_fire', 'react_shock', 'react_sad', 'react_angry']
    if reaction_type in valid_reactions:
        conn = get_db_connection()
        conn.execute(f'UPDATE posts SET {reaction_type} = {reaction_type} + 1 WHERE id = ?', (post_id,))
        conn.commit()
        new_count = conn.execute(f'SELECT {reaction_type} FROM posts WHERE id = ?', (post_id,)).fetchone()[0]
        conn.close()
        return jsonify({'success': True, 'new_count': new_count})
    return jsonify({'success': False})

# इन्फिनिट स्क्रॉल API (Slug के साथ)
@app.route('/api/next_post/<int:current_id>/<category>')
def next_post(current_id, category):
    conn = get_db_connection()
    post = conn.execute('''
        SELECT * FROM posts 
        WHERE category = ? AND id < ? AND status = 'published' 
        ORDER BY id DESC LIMIT 1
    ''', (category, current_id)).fetchone()
    conn.close()
    if post:
        post_dict = dict(post)
        post_dict['slug'] = slugify(post['title']) # URL के लिए slug भेज रहे हैं
        return jsonify(post_dict)
    return jsonify({'error': 'No more posts'})

# एडमिन पैनल
@app.route('/my-secret-admin-999', methods=('GET', 'POST'))
def admin():
    conn = get_db_connection()
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        seo_tags = request.form['seo_tags']
        status = request.form['status']
        category = request.form['category']
        
        image_path = ""
        if 'image_file' in request.files:
            file = request.files['image_file']
            if file.filename != '':
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                image_path = f"/static/uploads/{filename}"

        if title and content:
            conn.execute('''
                INSERT INTO posts (title, content, image_path, seo_tags, status, category) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (title, content, image_path, seo_tags, status, category))
            conn.commit()
            return redirect(url_for('admin'))

    posts = conn.execute('SELECT * FROM posts ORDER BY created_at DESC').fetchall()
    total_views = conn.execute('SELECT SUM(views) FROM posts').fetchone()[0] or 0
    conn.close()
    return render_template('admin.html', posts=posts, total_views=total_views)

@app.route('/delete/<int:post_id>')
def delete(post_id):
    conn = get_db_connection()
    conn.execute('DELETE FROM posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

# 🚀 SITEMAP ROUTE (Google के लिए)
@app.route('/sitemap.xml')
def sitemap():
    conn = get_db_connection()
    posts = conn.execute("SELECT id, title, created_at FROM posts WHERE status='published' ORDER BY created_at DESC").fetchall()
    conn.close()
    
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += f'  <url>\n    <loc>{request.url_root}</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    
    for post in posts:
        slug = slugify(post["title"])
        xml += f'  <url>\n    <loc>{request.url_root}article/{post["id"]}/{slug}</loc>\n'
        xml += f'    <lastmod>{post["created_at"][:10]}</lastmod>\n'
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