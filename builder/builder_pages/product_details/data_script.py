# --------------------------------------------------
# Utility / Helper Functions
# --------------------------------------------------

def process_and_assign_rating(target_dict, rating):
    """
    Processes a rating, calculates star information (filled, half, empty),
    and assigns the results to the target dictionary.

    Args:
        target_dict (dict): The dictionary to assign the rating fields to.
        rating (float): The rating value to process (should be <= 5).
    """

    if rating > 5:
        raise ValueError("Rating should be less than or equal to 5")

    num_of_filled_stars = round(rating * 2) / 2
    need_half_star = not num_of_filled_stars.is_integer()
    diff_from_5 = 5 - num_of_filled_stars

    if diff_from_5 % 1 != 0.0:
        diff_from_5 = diff_from_5 - 0.5

    empty_stars = round(diff_from_5)

    # Adjust num_of_filled_stars if a half star is needed
    num_of_filled_stars_final = num_of_filled_stars - 0.5 if need_half_star else num_of_filled_stars

    target_dict["num_of_filled_stars"] = [{"val": val} for val in range(int(num_of_filled_stars_final))] # has to be array of dicts for repeating
    target_dict["need_half_star"] = need_half_star # boolean
    target_dict["empty_stars"] = [{"val": val} for val in range(int(empty_stars))]

def convert_variant_list(variants):
    new_variants = []
    for variant in variants:
        new_variant = {
            "attribute": variant["attribute"],
            "value": [{"val": value} for value in variant["values"]] # could not be values as it is a builtin func
        }
        new_variants.append(new_variant)
    return new_variants


# --------------------------------------------------
# Get current session info
# --------------------------------------------------

current_user = frappe.session.user
url = frappe.get_url();
code = frappe.form_dict.productid


# --------------------------------------------------
# Get item details and its variants
# --------------------------------------------------

details = frappe.call("webshop.webshop.doctype.website_item.website_item.get_item_details",item_code=code,user=current_user)
variants = frappe.call("webshop.webshop.variant_selector.utils.get_attributes_and_values",item_code=details["web_item_name"])

# Assign route to recommened items (relative route)
for product in details["recommended_items"]:
    item_name = product["website_item"]
    product["route"] = f"{item_name}"
    

# --------------------------------------------------
# Get reviews info and assign stars info
# --------------------------------------------------

if details.cart_settings.enable_reviews:
    rating = details["reviews_and_ratings"]["average_rating"]
    process_and_assign_rating(details["reviews_and_ratings"], rating)
    
    details["reviews_and_ratings"]["average_rating"] = round(details["reviews_and_ratings"]["average_rating"], 2)
    reviews_per_rating = details["reviews_and_ratings"]["reviews_per_rating"]
    details["reviews_and_ratings"]["reviews_per_rating"] = [{"index": index + 1, "val": val} for index, val in enumerate(reviews_per_rating)]
    
    for review in details["reviews_and_ratings"]["reviews"]:
        rating = review["rating"] * 5
        process_and_assign_rating(review, rating)
    
    # Get current user review/rating
    details["reviews_and_ratings"]["current_user_review"] = frappe.call("webshop.webshop.doctype.item_review.item_review.get_user_specific_review",web_item=code)
    if details["reviews_and_ratings"]["current_user_review"]:
        current_user_rating = details["reviews_and_ratings"]["current_user_review"]["rating"] * 5
        process_and_assign_rating(details["reviews_and_ratings"]["current_user_review"], current_user_rating)


# --------------------------------------------------
# Assign values
# --------------------------------------------------

data.details = details
data.variants = convert_variant_list(variants) if len(convert_variant_list(variants)) > 0 else 0

data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"

# Get if current item is wishlisted by current user
data.is_wishlisted = frappe.call("webshop.webshop.doctype.website_item.website_item.if_item_wishlisted",item_code=details["item_code"]) if details.cart_settings.enable_recommendations else False

data.more_reviews_available =  details["reviews_and_ratings"]["total_reviews"] > 10
data.all_reviews_url = f"/customer-review/{code}"

# Pass on required data to client side
data.page_data = {
    "url": url,
    "name": details["web_item_name"],
    "web_item_code": details["name"],
    "code": details["item_code"],
    "has_variant": details["has_variants"],
    "my_rating": details["reviews_and_ratings"]["current_user_review"]["rating"] * 5 if details.cart_settings.enable_reviews and details["reviews_and_ratings"]["current_user_review"] else 2.5
}