from eco import app, db, Product

def clear_database():
    with app.app_context():
        try:
            # Table se saare products ek sath uda do
            deleted_count = db.session.query(Product).delete()
            db.session.commit()
            print(f"🧹 Ekdum Saaf! Tumhare {deleted_count} products database se hamesha ke liye delete ho gaye hain.")
        except Exception as e:
            db.session.rollback()
            print(f"Kuch gadbad hui: {e}")

if __name__ == '__main__':
    clear_database()