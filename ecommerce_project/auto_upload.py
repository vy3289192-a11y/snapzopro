import random
from eco import app, db, Product

def generate_women_premium_store():
    with app.app_context():
        # Premium Brands aur Colors
        brands = ["ZARA", "H&M", "Mango", "Urbanic", "Forever 21", "Biba", "Vero Moda", "Only", "Levis", "FabIndia"]
        colors = ["Midnight Black", "Blush Pink", "Emerald Green", "Ruby Red", "Sapphire Blue", "Lavender", "Mustard", "Pearl White", "Olive", "Maroon"]
        
        # Ekdum modern aur new fashion wale styles
        topwear_styles = ["Ruffle Dress", "Casual Crop Top", "Chiffon Blouse", "Oversized T-Shirt", "Cotton Kurti", "Ribbed Tank Top", "Peplum Top", "Maxi Dress", "Sleeveless Tunic", "Knitted Sweater"]
        bottomwear_styles = ["Wide Leg Jeans", "Cargo Pants", "Flared Trousers", "Pleated Skirt", "Denim Shorts", "Palazzo Pants", "Skinny Jeans", "Yoga Leggings", "Linen Culottes", "A-Line Skirt"]

        # 100% Verified, Asli Women's Fashion HD Photos (Koi kachra nahi)
        topwear_images = [
            "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=600",
            "https://images.unsplash.com/photo-1434389670869-c41926b4cb09?w=600",
            "https://images.unsplash.com/photo-1550639525-c97d455acf70?w=600",
            "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=600",
            "https://images.unsplash.com/photo-1618244972963-dbee1a7edc95?w=600",
            "https://images.unsplash.com/photo-1525507119028-ed4c629a60a3?w=600",
            "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=600",
            "https://images.unsplash.com/photo-1496747611176-843222e1e57c?w=600"
        ]
        
        bottomwear_images = [
            "https://images.unsplash.com/photo-1584370848010-d7fe6bc767eb?w=600",
            "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=600",
            "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=600",
            "https://images.unsplash.com/photo-1573041935830-4eeb95a8f4c2?w=600",
            "https://images.unsplash.com/photo-1551854838-212c50b4c3ae?w=600",
            "https://images.unsplash.com/photo-1604644401890-0bd678c83788?w=600",
            "https://images.unsplash.com/photo-1541099649105-f69ad21f3246?w=600",
            "https://images.unsplash.com/photo-1582552938357-32b906df40cb?w=600"
        ]

        generated_names = set()
        
        # --- 50 UNIQUE TOPWEAR BANANA ---
        count_top = 0
        while count_top < 50:
            name = f"{random.choice(brands)} Premium {random.choice(colors)} {random.choice(topwear_styles)}"
            
            # Agar ye naam pehle nahi bana hai, tabhi aage badho (NO DUPLICATE GUARANTEE)
            if name not in generated_names:
                generated_names.add(name)
                img = topwear_images[count_top % len(topwear_images)]
                
                product = Product(name=name, category="Women Topwear", mrp=1999, selling_price=99, stock=random.randint(10, 50), image_url=img)
                db.session.add(product)
                count_top += 1
        
        # --- 50 UNIQUE BOTTOMWEAR BANANA ---
        count_bottom = 0
        while count_bottom < 50:
            name = f"{random.choice(brands)} Premium {random.choice(colors)} {random.choice(bottomwear_styles)}"
            
            if name not in generated_names:
                generated_names.add(name)
                img = bottomwear_images[count_bottom % len(bottomwear_images)]
                
                product = Product(name=name, category="Women Bottomwear", mrp=1999, selling_price=99, stock=random.randint(10, 50), image_url=img)
                db.session.add(product)
                count_bottom += 1

        db.session.commit()
        print(f"🔥 MISSION SUCCESS! 100 Unique Women Products Added (50 Topwear, 50 Bottomwear) at ₹99!")

if __name__ == '__main__':
    generate_women_premium_store()