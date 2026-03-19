from math import ceil
from typing import Optional, Literal

from fastapi import FastAPI, Query, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="Fashion Store API")

# ----------------------------
# In-memory data
# ----------------------------

products = [
    {
        "id": 1,
        "name": "Classic Black T-Shirt",
        "price": 799,
        "category": "Topwear",
        "brand": "UrbanStyle",
        "size": "M",
        "is_available": True
    },
    {
        "id": 2,
        "name": "Blue Denim Jeans",
        "price": 1499,
        "category": "Bottomwear",
        "brand": "DenimCo",
        "size": "L",
        "is_available": True
    },
    {
        "id": 3,
        "name": "White Sneakers",
        "price": 2499,
        "category": "Footwear",
        "brand": "StepUp",
        "size": "8",
        "is_available": True
    },
    {
        "id": 4,
        "name": "Red Hoodie",
        "price": 1899,
        "category": "Winterwear",
        "brand": "CozyFit",
        "size": "XL",
        "is_available": False
    },
    {
        "id": 5,
        "name": "Floral Summer Dress",
        "price": 2199,
        "category": "Dresses",
        "brand": "GlowFashion",
        "size": "S",
        "is_available": True
    },
    {
        "id": 6,
        "name": "Leather Handbag",
        "price": 2799,
        "category": "Accessories",
        "brand": "LuxCarry",
        "size": "Free Size",
        "is_available": True
    }
]

orders = []
cart = []

order_counter = 1


# ----------------------------
# Pydantic models
# ----------------------------

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=10)
    address: str = Field(..., min_length=10)
    shipping_type: Literal["standard", "express"] = "standard"


class NewProduct(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    brand: str = Field(..., min_length=2)
    size: str = Field(..., min_length=1)
    is_available: bool = True


class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    address: str = Field(..., min_length=10)
    shipping_type: Literal["standard", "express"] = "standard"


# ----------------------------
# Helper functions
# ----------------------------

def find_product(product_id: int):
    for product in products:
        if product["id"] == product_id:
            return product
    return None


def calculate_total(price: int, quantity: int, shipping_type: str = "standard"):
    subtotal = price * quantity
    shipping_charge = 0

    if shipping_type == "express":
        shipping_charge = 100
    elif shipping_type == "standard":
        shipping_charge = 40

    return {
        "subtotal": subtotal,
        "shipping_charge": shipping_charge,
        "total_price": subtotal + shipping_charge
    }


def filter_products_logic(
    category: Optional[str] = None,
    max_price: Optional[int] = None,
    brand: Optional[str] = None,
    is_available: Optional[bool] = None
):
    filtered = products

    if category is not None:
        filtered = [
            product for product in filtered
            if product["category"].lower() == category.lower()
        ]

    if max_price is not None:
        filtered = [
            product for product in filtered
            if product["price"] <= max_price
        ]

    if brand is not None:
        filtered = [
            product for product in filtered
            if product["brand"].lower() == brand.lower()
        ]

    if is_available is not None:
        filtered = [
            product for product in filtered
            if product["is_available"] == is_available
        ]

    return filtered


# ----------------------------
# Day 1 - GET routes
# ----------------------------

@app.get("/")
def home():
    return {"message": "Welcome to TrendHive Fashion Store"}


@app.get("/products")
def get_all_products():
    return {
        "products": products,
        "total": len(products)
    }


@app.get("/orders")
def get_all_orders():
    return {
        "orders": orders,
        "total_orders": len(orders)
    }


@app.get("/products/summary")
def product_summary():
    available_count = sum(1 for product in products if product["is_available"])
    unavailable_count = len(products) - available_count
    categories = list({product["category"] for product in products})

    return {
        "total_products": len(products),
        "available_products": available_count,
        "unavailable_products": unavailable_count,
        "categories": categories
    }


# ----------------------------
# Day 3 - filter route
# Keep fixed routes above /products/{product_id}
# ----------------------------

@app.get("/products/filter")
def filter_products(
    category: Optional[str] = None,
    max_price: Optional[int] = Query(default=None, gt=0),
    brand: Optional[str] = None,
    is_available: Optional[bool] = None
):
    filtered = filter_products_logic(category, max_price, brand, is_available)

    return {
        "filtered_products": filtered,
        "count": len(filtered)
    }


# ----------------------------
# Day 6 - search / sort / page / browse
# Keep above /products/{product_id}
# ----------------------------

@app.get("/products/search")
def search_products(keyword: str):
    keyword = keyword.lower()
    matched = [
        product for product in products
        if keyword in product["name"].lower()
        or keyword in product["category"].lower()
        or keyword in product["brand"].lower()
    ]

    if not matched:
        return {
            "message": "No matching products found",
            "total_found": 0,
            "products": []
        }

    return {
        "total_found": len(matched),
        "products": matched
    }


@app.get("/products/sort")
def sort_products(
    sort_by: str = "price",
    order: str = "asc"
):
    allowed_sort_fields = ["price", "name", "category"]
    allowed_order = ["asc", "desc"]

    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort_by value")

    if order not in allowed_order:
        raise HTTPException(status_code=400, detail="Invalid order value")

    sorted_products = sorted(
        products,
        key=lambda x: x[sort_by],
        reverse=(order == "desc")
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "products": sorted_products
    }


@app.get("/products/page")
def paginate_products(
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=3, ge=1, le=10)
):
    total = len(products)
    total_pages = ceil(total / limit)
    start = (page - 1) * limit
    paginated_items = products[start:start + limit]

    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "products": paginated_items
    }


@app.get("/products/browse")
def browse_products(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    brand: Optional[str] = None,
    max_price: Optional[int] = Query(default=None, gt=0),
    is_available: Optional[bool] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=4, ge=1, le=10)
):
    allowed_sort_fields = ["price", "name", "category"]
    allowed_order = ["asc", "desc"]

    if sort_by not in allowed_sort_fields:
        raise HTTPException(status_code=400, detail="Invalid sort_by value")

    if order not in allowed_order:
        raise HTTPException(status_code=400, detail="Invalid order value")

    filtered = filter_products_logic(category, max_price, brand, is_available)

    if keyword is not None:
        keyword = keyword.lower()
        filtered = [
            product for product in filtered
            if keyword in product["name"].lower()
            or keyword in product["category"].lower()
            or keyword in product["brand"].lower()
        ]

    sorted_items = sorted(
        filtered,
        key=lambda x: x[sort_by],
        reverse=(order == "desc")
    )

    total = len(sorted_items)
    total_pages = ceil(total / limit) if total > 0 else 1
    start = (page - 1) * limit
    final_items = sorted_items[start:start + limit]

    return {
        "keyword": keyword,
        "category": category,
        "brand": brand,
        "max_price": max_price,
        "is_available": is_available,
        "sort_by": sort_by,
        "order": order,
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": total_pages,
        "products": final_items
    }


# ----------------------------
# Day 1 - variable route
# ----------------------------

@app.get("/products/{product_id}")
def get_product_by_id(product_id: int):
    product = find_product(product_id)
    if not product:
        return {"error": "Product not found"}
    return product


# ----------------------------
# Day 2 + Day 3 - POST order
# ----------------------------

@app.post("/orders")
def place_order(order: OrderRequest):
    global order_counter

    product = find_product(order.product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["is_available"]:
        raise HTTPException(status_code=400, detail="Product is out of stock")

    bill = calculate_total(product["price"], order.quantity, order.shipping_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "product_id": order.product_id,
        "product_name": product["name"],
        "quantity": order.quantity,
        "address": order.address,
        "shipping_type": order.shipping_type,
        "subtotal": bill["subtotal"],
        "shipping_charge": bill["shipping_charge"],
        "total_price": bill["total_price"]
    }

    orders.append(new_order)
    order_counter += 1

    return {
        "message": "Order placed successfully",
        "order": new_order
    }


# ----------------------------
# Day 4 - CRUD products
# ----------------------------

@app.post("/products")
def add_product(product: NewProduct, response: Response):
    for existing_product in products:
        if existing_product["name"].lower() == product.name.lower():
            raise HTTPException(status_code=400, detail="Product with this name already exists")

    new_id = max(p["id"] for p in products) + 1 if products else 1

    new_product = {
        "id": new_id,
        "name": product.name,
        "price": product.price,
        "category": product.category,
        "brand": product.brand,
        "size": product.size,
        "is_available": product.is_available
    }

    products.append(new_product)
    response.status_code = 201
    return new_product


@app.put("/products/{product_id}")
def update_product(
    product_id: int,
    price: Optional[int] = Query(default=None, gt=0),
    is_available: Optional[bool] = None
):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if price is not None:
        product["price"] = price

    if is_available is not None:
        product["is_available"] = is_available

    return {
        "message": "Product updated successfully",
        "product": product
    }


@app.delete("/products/{product_id}")
def delete_product(product_id: int):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    products.remove(product)

    return {
        "message": f"Product '{product['name']}' deleted successfully"
    }


# ----------------------------
# Day 5 - Cart workflow
# ----------------------------

@app.post("/cart/add")
def add_to_cart(
    product_id: int = Query(..., gt=0),
    quantity: int = Query(default=1, gt=0, le=10)
):
    product = find_product(product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    if not product["is_available"]:
        raise HTTPException(status_code=400, detail="Product is out of stock")

    for item in cart:
        if item["product_id"] == product_id:
            item["quantity"] += quantity
            item["item_total"] = item["price"] * item["quantity"]
            return {
                "message": "Cart quantity updated",
                "cart_item": item
            }

    cart_item = {
        "product_id": product["id"],
        "product_name": product["name"],
        "price": product["price"],
        "quantity": quantity,
        "item_total": product["price"] * quantity
    }

    cart.append(cart_item)

    return {
        "message": "Item added to cart",
        "cart_item": cart_item
    }


@app.get("/cart")
def view_cart():
    grand_total = sum(item["item_total"] for item in cart)

    return {
        "cart_items": cart,
        "grand_total": grand_total
    }


@app.delete("/cart/{product_id}")
def remove_cart_item(product_id: int):
    for item in cart:
        if item["product_id"] == product_id:
            cart.remove(item)
            return {"message": "Item removed from cart"}

    raise HTTPException(status_code=404, detail="Item not found in cart")


@app.post("/cart/checkout")
def checkout_cart(checkout: CheckoutRequest, response: Response):
    global order_counter

    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty")

    placed_orders = []
    grand_total = 0

    for item in cart:
        bill = calculate_total(item["price"], item["quantity"], checkout.shipping_type)

        order = {
            "order_id": order_counter,
            "customer_name": checkout.customer_name,
            "product_id": item["product_id"],
            "product_name": item["product_name"],
            "quantity": item["quantity"],
            "address": checkout.address,
            "shipping_type": checkout.shipping_type,
            "subtotal": bill["subtotal"],
            "shipping_charge": bill["shipping_charge"],
            "total_price": bill["total_price"]
        }

        orders.append(order)
        placed_orders.append(order)
        grand_total += bill["total_price"]
        order_counter += 1

    cart.clear()
    response.status_code = 201

    return {
        "message": "Checkout completed successfully",
        "placed_orders": placed_orders,
        "grand_total": grand_total
    }


# ----------------------------
# Day 6 - Orders search/sort
# ----------------------------

@app.get("/orders/search")
def search_orders(customer_name: str):
    matched = [
        order for order in orders
        if customer_name.lower() in order["customer_name"].lower()
    ]

    return {
        "total_found": len(matched),
        "orders": matched
    }


@app.get("/orders/sort")
def sort_orders(order: str = "asc"):
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail="Invalid order value")

    sorted_orders = sorted(
        orders,
        key=lambda x: x["total_price"],
        reverse=(order == "desc")
    )

    return {
        "order": order,
        "orders": sorted_orders
    }