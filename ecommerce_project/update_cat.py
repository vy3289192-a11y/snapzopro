from eco import app, db, Product

with app.app_context():
    products = Product.query.all()
    updated_count = 0

    for p in products:
        name_lower = p.name.lower()
        
        # Agar naam mein ye words hain, toh automatically 'Men' category kar do
        if any(word in name_lower for word in ['men', 'shirt', 'sweater', 'pullover', 'overshirt', 'co-ords']):
            p.category = 'Men'
            updated_count += 1
            
        # Agar naam mein ye words hain, toh automatically 'Women' category kar do
        elif any(word in name_lower for word in ['women', 'dress', 'ruched', 'saree', 'kurti', 'lehenga']):
            p.category = 'Women'
            updated_count += 1

    # Database mein save kar do
    db.session.commit()
    print(f"Jhakas! {updated_count} products automatically Men/Women category mein update ho gaye hain.")