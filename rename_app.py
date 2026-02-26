
import os

target_dir = os.path.abspath("shop")

# Content Replacements
replacements = {
    "webshop.webshop": "shop.shop",
    # 'app_name = "webshop"': 'app_name = "shop"', # Handled
    "from webshop": "from shop",
    "import webshop": "import shop",
    '"module": "Webshop"': '"module": "Shop"',
    "webshop.patches": "shop.patches",
    "webshop-web.bundle.css": "shop-web.bundle.css",
    "webshop-web.bundle.scss": "shop-web.bundle.scss",
    "webshop_cart.scss": "shop_cart.scss",
    # Javascript namespace
    "frappe.provide(\"webshop.webshop": "frappe.provide(\"shop.shop",
    "webshop.webshop.shopping_cart": "shop.shop.shopping_cart",
    "webshop.webshop.": "shop.shop."
}

print(f"Scanning {target_dir}...")

# 1. Replace Content
for root, dirs, files in os.walk(target_dir):
    for f_name in files:
        if f_name.endswith(('.py', '.js', '.json', '.html', '.css', '.scss', '.md', '.txt')):
            f_path = os.path.join(root, f_name)
            try:
                with open(f_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_content = content
                for old, new in replacements.items():
                    new_content = new_content.replace(old, new)
                
                if new_content != content:
                    print(f"Modifying content in {f_name}")
                    with open(f_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
            except Exception as e:
                print(f"Skipping {f_path}: {e}")

# 2. Rename Files and Directories
# Process bottom-up to handle children before parents
for root, dirs, files in os.walk(target_dir, topdown=False):
    for f_name in files:
        if "webshop" in f_name:
            new_name = f_name.replace("webshop", "shop")
            old_path = os.path.join(root, f_name)
            new_path = os.path.join(root, new_name)
            print(f"Renaming file {old_path} -> {new_path}")
            os.rename(old_path, new_path)
    
    for d_name in dirs:
        if "webshop" in d_name:
            new_name = d_name.replace("webshop", "shop")
            old_path = os.path.join(root, d_name)
            new_path = os.path.join(root, new_name)
            print(f"Renaming directory {old_path} -> {new_path}")
            os.rename(old_path, new_path)
