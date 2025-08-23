available_sort_fields = ["rating", "date"]
available_sort_orders = ["asc", "desc"]
page_size = 10
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

    target_dict["num_of_filled_stars"] = [{"val": val} for val in range(int(num_of_filled_stars_final))]
    target_dict["need_half_star"] = need_half_star
    target_dict["empty_stars"] = [{"val": val} for val in range(int(empty_stars))]


web_item_code = frappe.form_dict["web_item_code"]
data.web_item_code = web_item_code
data.is_logged_in = frappe.user != "Guest"
data.can_access_cart = frappe.call("webshop.webshop.shopping_cart.cart.can_access_cart") and frappe.user != "Guest"

data.item_details = frappe.call(
    "webshop.webshop.doctype.website_item.website_item.get_item_details",
    item_code = web_item_code,
    user = frappe.session.user,
    short = True
)

data.not_found = True
if data.item_details:
    data.not_found = False

try:
    page = frappe.form_dict["page"]
except KeyError:
    page = 1
data.page = page

try:
    sort_by = frappe.form_dict["sort_by"]
except KeyError:
    sort_by = None
data.sort_by = sort_by

try:
    sort_order = frappe.form_dict["order"]
except KeyError:
    sort_order = None
data.sort_order = sort_order

print("customer review query params: ", page, sort_by, sort_order)

if sort_by not in available_sort_fields or sort_order not in available_sort_orders:
    sort_by = sort_order = None

offset = (int(page) - 1) * page_size
print("page: ", page, (int(page) - 1) * page_size)
reviews_and_ratings = frappe.call("webshop.webshop.doctype.item_review.item_review.get_item_reviews", web_item = web_item_code, start = 0 + offset, page_length = page_size, sort_by = sort_by if sort_by != "date" else "published_on", sort_order = sort_order)

if not len(reviews_and_ratings["reviews"]) and int(page) != 1:
    offset = 0
    reviews_and_ratings = frappe.call("webshop.webshop.doctype.item_review.item_review.get_item_reviews", web_item = web_item_code, start = 0 + offset, end = 20 + offset)

if reviews_and_ratings:
    rating = reviews_and_ratings["average_rating"]
    process_and_assign_rating(reviews_and_ratings, rating)
    
    reviews_and_ratings["average_rating"] = round(reviews_and_ratings["average_rating"], 2)
    reviews_per_rating = reviews_and_ratings["reviews_per_rating"]
    reviews_and_ratings["reviews_per_rating"] = [{"index": index + 1, "val": val} for index, val in enumerate(reviews_per_rating)]
    
    for review in reviews_and_ratings["reviews"]:
        rating = review["rating"] * 5
        process_and_assign_rating(review, rating)

data.reviews_and_ratings = reviews_and_ratings
data.total_fetched = len(reviews_and_ratings["reviews"])
data.start = offset + 1
data.end = offset + page_size if offset + page_size < reviews_and_ratings["total_reviews"] else reviews_and_ratings["total_reviews"]
data.sort_select_content = "Sort By"
data.sort_icon = "arrow-down-a-z" if sort_order and sort_order == "asc" else "arrow-down-z-a"
data.available_sort_fields_map = [{"val" : f"{field[0].upper()}{field[1:]}"} for field in available_sort_fields]
data.next_available = offset + page_size < reviews_and_ratings["total_reviews"]
data.prev_available = offset > 0
data.item_url = f"/item/{web_item_code}"