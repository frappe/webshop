
import os

target_dir = os.path.abspath("shop")

replacements = {
    "webshop_settings": "shop_settings",
    "Webshop": "Shop",
    "webshop_cart": "shop_cart",
    "webshop-web.bundle": "shop-web.bundle"
}

print(f"Scanning {target_dir}...")

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
