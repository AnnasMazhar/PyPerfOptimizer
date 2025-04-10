# Optimization Code Examples

This document provides specific code examples showing how to apply the optimization techniques identified by PyPerfOptimizer. Each example includes the original code, the profiling insights, and the optimized implementation.

## 1. Algorithmic Optimization Examples

### 1.1 Recursive Fibonacci Optimization

**Original Code (Inefficient):**
```python
def fibonacci(n):
    """Recursive implementation of Fibonacci."""
    if n <= 1:
        return n
    else:
        return fibonacci(n-1) + fibonacci(n-2)

# Call example
result = fibonacci(35)  # Takes several seconds
```

**PyPerfOptimizer Insight:**
```
CPU Profiling Results:
- 29,860,703 function calls for n=35
- Exponential time complexity detected
- Redundant calculations of same values
Recommendation: Apply memoization to cache previous results
```

**Optimized Code:**
```python
from functools import lru_cache

@lru_cache(maxsize=None)
def fibonacci_optimized(n):
    """Memoized implementation of Fibonacci."""
    if n <= 1:
        return n
    else:
        return fibonacci_optimized(n-1) + fibonacci_optimized(n-2)

# Alternatively, using PyPerfOptimizer's optimization decorator
from pyperfoptimizer.optimizers import optimize

@optimize(memoize=True)
def fibonacci_auto_optimized(n):
    """Automatically optimized Fibonacci."""
    if n <= 1:
        return n
    else:
        return fibonacci_auto_optimized(n-1) + fibonacci_auto_optimized(n-2)

# Or using iteration (most efficient)
def fibonacci_iterative(n):
    """Iterative implementation of Fibonacci."""
    if n <= 1:
        return n
    a, b = 0, 1
    for _ in range(2, n + 1):
        a, b = b, a + b
    return b

# Call examples
result1 = fibonacci_optimized(35)      # Takes milliseconds 
result2 = fibonacci_auto_optimized(35) # Takes milliseconds
result3 = fibonacci_iterative(35)      # Takes microseconds
```

### 1.2 Sort Optimization

**Original Code (Inefficient):**
```python
def find_top_items(items, key_func, n=10):
    """Find the top N items based on a key function."""
    # Sort the entire list, then take the first N items
    sorted_items = sorted(items, key=key_func, reverse=True)
    return sorted_items[:n]

# Example usage with 100,000 items
import random
data = [random.randint(1, 1000000) for _ in range(100000)]
top_10 = find_top_items(data, lambda x: x)
```

**PyPerfOptimizer Insight:**
```
CPU Profiling Results:
- O(n log n) sorting operation detected for partial result
- Only top N elements needed, but full sort performed
Recommendation: Use heapq.nlargest for top-N selection
```

**Optimized Code:**
```python
import heapq

def find_top_items_optimized(items, key_func, n=10):
    """Find the top N items using heapq.nlargest."""
    return heapq.nlargest(n, items, key=key_func)

# Alternatively, using PyPerfOptimizer's optimization transformer
from pyperfoptimizer.optimizers import optimize_function

# This automatically transforms the function using static code analysis
find_top_items_auto_optimized = optimize_function(find_top_items)

# Example usage
top_10_optimized = find_top_items_optimized(data, lambda x: x)
top_10_auto = find_top_items_auto_optimized(data, lambda x: x)
```

## 2. Memory Optimization Examples

### 2.1 Memory Leak Fix

**Original Code (With Memory Leak):**
```python
class DataProcessor:
    """A class that processes data and has a memory leak."""
    _history = []  # Class variable that accumulates data
    
    def __init__(self, name):
        self.name = name
        
    def process_item(self, item):
        """Process an item and store in history."""
        result = self._transform(item)
        DataProcessor._history.append(result)  # Accumulates without bound
        return result
        
    def _transform(self, item):
        """Transform an item."""
        return {"original": item, "processed": item * 2, "processor": self.name}

# Usage example
processor = DataProcessor("main")
for i in range(1000000):
    processor.process_item(i)  # Memory usage grows continuously
```

**PyPerfOptimizer Insight:**
```
Memory Profiling Results:
- Unbounded growth detected in DataProcessor._history
- Class variable accumulation pattern identified
- Memory increases by approximately 48 bytes per iteration
Recommendation: 
1. Convert class variable to instance variable
2. Implement size limit or periodic cleanup
```

**Optimized Code:**
```python
class DataProcessor:
    """A class that processes data with controlled memory usage."""
    
    def __init__(self, name, history_limit=1000):
        self.name = name
        self._history = []  # Instance variable, not shared across instances
        self._history_limit = history_limit
        
    def process_item(self, item):
        """Process an item and store in bounded history."""
        result = self._transform(item)
        
        # Implement size limiting
        if len(self._history) >= self._history_limit:
            self._history.pop(0)  # Remove oldest item if limit reached
            
        self._history.append(result)
        return result
        
    def _transform(self, item):
        """Transform an item."""
        return {"original": item, "processed": item * 2, "processor": self.name}
    
    @property
    def history(self):
        """Return a copy of history to prevent external modification."""
        return self._history.copy()

# Alternatively, using PyPerfOptimizer's memory safety wrapper
from pyperfoptimizer.optimizers import memory_safe

@memory_safe(detect_leaks=True, bounded_collections=True)
class DataProcessorAutoOptimized:
    """Automatically memory-optimized data processor."""
    _history = []  # Will be transformed to instance variable
    
    def __init__(self, name):
        self.name = name
        
    def process_item(self, item):
        """Process an item and store in history."""
        result = self._transform(item)
        self._history.append(result)  # Will be bounded automatically
        return result
        
    def _transform(self, item):
        """Transform an item."""
        return {"original": item, "processed": item * 2, "processor": self.name}
```

### 2.2 Large Data Processing

**Original Code (Memory Intensive):**
```python
def process_large_dataset(data):
    """Process a large dataset with excessive memory usage."""
    # Create multiple intermediate copies of the data
    filtered_data = [x for x in data if x > 0]
    squared_data = [x**2 for x in filtered_data]
    normalized_data = [(x - min(squared_data)) / (max(squared_data) - min(squared_data)) 
                      for x in squared_data]
    
    # Calculate statistics
    mean = sum(normalized_data) / len(normalized_data)
    variance = sum((x - mean)**2 for x in normalized_data) / len(normalized_data)
    std_dev = variance ** 0.5
    
    return {
        'filtered': filtered_data,
        'squared': squared_data,
        'normalized': normalized_data,
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev
    }
```

**PyPerfOptimizer Insight:**
```
Memory Profiling Results:
- Multiple full-sized copies of data created
- Repeated calculations of min/max
- Redundant storage of intermediate results
Recommendation: 
1. Use generators for intermediate steps
2. Calculate statistics in a single pass
3. Avoid storing unnecessary intermediate results
```

**Optimized Code:**
```python
def process_large_dataset_optimized(data):
    """Process a large dataset with minimal memory usage."""
    # Use generators instead of lists for intermediate steps
    filtered_data = (x for x in data if x > 0)
    squared_data = (x**2 for x in filtered_data)
    
    # Calculate min/max in a single pass
    squared_list = list(squared_data)  # Only one materialized list
    if not squared_list:
        return {'mean': 0, 'variance': 0, 'std_dev': 0}
        
    min_val = min(squared_list)
    max_val = max(squared_list)
    range_val = max_val - min_val if max_val > min_val else 1
    
    # Use generator for normalized data
    normalized_data = ((x - min_val) / range_val for x in squared_list)
    
    # Calculate statistics in a single pass
    count = 0
    sum_val = 0
    sum_squared = 0
    
    for x in normalized_data:
        count += 1
        sum_val += x
        sum_squared += x**2
    
    mean = sum_val / count if count > 0 else 0
    variance = (sum_squared / count) - (mean**2) if count > 0 else 0
    std_dev = variance ** 0.5
    
    return {
        'mean': mean,
        'variance': variance,
        'std_dev': std_dev
    }

# Using NumPy for even better performance and memory efficiency
import numpy as np

def process_large_dataset_numpy(data):
    """Process a large dataset using NumPy for memory efficiency."""
    # Convert to numpy array once
    data_array = np.array(data)
    
    # Filter
    filtered = data_array[data_array > 0]
    
    # Square
    squared = filtered ** 2
    
    # Normalize
    min_val = squared.min()
    max_val = squared.max()
    range_val = max_val - min_val if max_val > min_val else 1
    normalized = (squared - min_val) / range_val
    
    # Calculate statistics
    return {
        'mean': normalized.mean(),
        'variance': normalized.var(),
        'std_dev': normalized.std()
    }
```

## 3. Database Optimization Examples

### 3.1 N+1 Query Problem

**Original Code (Inefficient):**
```python
def get_users_with_orders(user_ids):
    """Get users and their orders with inefficient querying."""
    users = []
    for user_id in user_ids:
        # Separate query for each user
        user = db.execute("SELECT id, name, email FROM users WHERE id = ?", 
                         [user_id]).fetchone()
        
        if user:
            # Separate query for each user's orders
            orders = db.execute("SELECT id, product_name, amount FROM orders WHERE user_id = ?", 
                               [user_id]).fetchall()
            
            user_data = {
                'id': user[0],
                'name': user[1],
                'email': user[2],
                'orders': orders
            }
            users.append(user_data)
    
    return users
```

**PyPerfOptimizer Insight:**
```
Database Profiling Results:
- N+1 query pattern detected
- For 100 users, executing 101 queries (1 per user + 1 per user's orders)
- Excessive round-trips to database
Recommendation:
1. Use IN clause for batch user fetching
2. Join users with orders or use a subquery
```

**Optimized Code:**
```python
def get_users_with_orders_optimized(user_ids):
    """Get users and their orders with efficient batch querying."""
    if not user_ids:
        return []
    
    # Convert user_ids to string for SQL IN clause
    user_ids_str = ','.join('?' for _ in user_ids)
    
    # Fetch all users in a single query
    users_query = f"SELECT id, name, email FROM users WHERE id IN ({user_ids_str})"
    users_result = db.execute(users_query, user_ids).fetchall()
    
    # Create mapping of user_id to user data
    users_map = {user[0]: {'id': user[0], 'name': user[1], 
                          'email': user[2], 'orders': []} 
                for user in users_result}
    
    # Fetch all orders for these users in a single query
    orders_query = f"SELECT user_id, id, product_name, amount FROM orders WHERE user_id IN ({user_ids_str})"
    orders_result = db.execute(orders_query, user_ids).fetchall()
    
    # Assign orders to their respective users
    for order in orders_result:
        user_id = order[0]
        if user_id in users_map:
            users_map[user_id]['orders'].append({
                'id': order[1],
                'product_name': order[2],
                'amount': order[3]
            })
    
    # Return as list of users
    return list(users_map.values())

# Using SQLAlchemy with relationship loading
from sqlalchemy.orm import joinedload

def get_users_with_orders_sqlalchemy(user_ids):
    """Get users and their orders using SQLAlchemy eager loading."""
    # Query users with eager loading of orders
    users = (db.session.query(User)
             .options(joinedload(User.orders))
             .filter(User.id.in_(user_ids))
             .all())
    
    # Convert to dictionaries
    return [
        {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'orders': [
                {
                    'id': order.id,
                    'product_name': order.product_name,
                    'amount': order.amount
                }
                for order in user.orders
            ]
        }
        for user in users
    ]
```

### 3.2 Query Optimization with Indexing

**Original Code (Inefficient):**
```python
def search_products(min_price=None, max_price=None, category=None, keyword=None):
    """Search for products with inefficient query."""
    query = "SELECT id, name, description, price, category FROM products WHERE 1=1"
    params = []
    
    if min_price is not None:
        query += " AND price >= ?"
        params.append(min_price)
    
    if max_price is not None:
        query += " AND price <= ?"
        params.append(max_price)
    
    if category is not None:
        query += " AND category = ?"
        params.append(category)
    
    if keyword is not None:
        query += " AND (name LIKE ? OR description LIKE ?)"
        keyword_param = f"%{keyword}%"
        params.append(keyword_param)
        params.append(keyword_param)
    
    return db.execute(query, params).fetchall()
```

**PyPerfOptimizer Insight:**
```
Database Profiling Results:
- Missing indexes detected on:
  * products(price)
  * products(category)
- Text search without full-text index
- Query plan shows full table scan
Recommendations:
1. Add appropriate indexes
2. Use full-text search for keyword search
3. Optimize query order for best index usage
```

**Optimized Code:**
```python
# First, add necessary indexes (one-time operation)
"""
CREATE INDEX IF NOT EXISTS idx_products_price ON products(price);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category);
CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(name, description, content='products');
"""

def search_products_optimized(min_price=None, max_price=None, category=None, keyword=None):
    """Search for products with optimized query using indexes."""
    # Start with the most selective conditions for better index usage
    if keyword is not None:
        # Use virtual FTS table for text search
        query = """
            SELECT p.id, p.name, p.description, p.price, p.category
            FROM products p
            JOIN products_fts fts ON p.id = fts.rowid
            WHERE fts.name MATCH ? OR fts.description MATCH ?
        """
        params = [keyword, keyword]
        
        if category is not None:
            query += " AND p.category = ?"
            params.append(category)
        
        if min_price is not None:
            query += " AND p.price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND p.price <= ?"
            params.append(max_price)
            
        return db.execute(query, params).fetchall()
    
    elif category is not None:
        # Category is usually more selective than price range
        query = """
            SELECT id, name, description, price, category
            FROM products
            WHERE category = ?
        """
        params = [category]
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
            
        return db.execute(query, params).fetchall()
    
    else:
        # Price range only
        query = "SELECT id, name, description, price, category FROM products WHERE 1=1"
        params = []
        
        if min_price is not None:
            query += " AND price >= ?"
            params.append(min_price)
        
        if max_price is not None:
            query += " AND price <= ?"
            params.append(max_price)
            
        return db.execute(query, params).fetchall()
```

## 4. API Performance Optimization

### 4.1 Serialization Optimization

**Original Code (Inefficient):**
```python
def get_dashboard_data(user_id):
    """Get dashboard data with inefficient serialization."""
    # Fetch user data
    user = get_user(user_id)
    
    # Fetch various dashboard components
    recent_orders = get_recent_orders(user_id)
    notifications = get_notifications(user_id)
    recommendations = get_recommendations(user_id)
    account_summary = get_account_summary(user_id)
    
    # Manual JSON serialization
    dashboard = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'avatar': user.avatar,
            'preferences': user.preferences,
        },
        'recent_orders': [
            {
                'id': order.id,
                'date': order.date.strftime('%Y-%m-%d %H:%M:%S'),
                'product': order.product.name,
                'amount': float(order.amount),
                'status': order.status,
            }
            for order in recent_orders
        ],
        'notifications': [
            {
                'id': notification.id,
                'type': notification.type,
                'message': notification.message,
                'read': notification.read,
                'date': notification.date.strftime('%Y-%m-%d %H:%M:%S'),
            }
            for notification in notifications
        ],
        'recommendations': [
            {
                'id': rec.id,
                'product': rec.product.name,
                'image': rec.product.image,
                'price': float(rec.product.price),
                'discount': float(rec.discount) if rec.discount else None,
            }
            for rec in recommendations
        ],
        'account': {
            'balance': float(account_summary.balance),
            'pending': float(account_summary.pending),
            'last_payment': account_summary.last_payment.strftime('%Y-%m-%d') if account_summary.last_payment else None,
            'next_payment': account_summary.next_payment.strftime('%Y-%m-%d') if account_summary.next_payment else None,
        }
    }
    
    return json.dumps(dashboard)
```

**PyPerfOptimizer Insight:**
```
API Profiling Results:
- Inefficient manual serialization
- Redundant string formatting operations
- Multiple nested loops for data transformation
- Repeated date formatting operations
Recommendations:
1. Use a dedicated serializer/schema library
2. Implement caching for repetitive transformations
3. Avoid nested serialization loops
```

**Optimized Code:**
```python
# Using Pydantic for efficient serialization
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import orjson

class UserData(BaseModel):
    id: int
    name: str
    email: str
    avatar: str
    preferences: dict

class OrderData(BaseModel):
    id: int
    date: datetime
    product: str
    amount: float
    status: str

class NotificationData(BaseModel):
    id: int
    type: str
    message: str
    read: bool
    date: datetime

class RecommendationData(BaseModel):
    id: int
    product: str
    image: str
    price: float
    discount: Optional[float] = None

class AccountData(BaseModel):
    balance: float
    pending: float
    last_payment: Optional[datetime] = None
    next_payment: Optional[datetime] = None

class Dashboard(BaseModel):
    user: UserData
    recent_orders: List[OrderData]
    notifications: List[NotificationData]
    recommendations: List[RecommendationData]
    account: AccountData
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime('%Y-%m-%d %H:%M:%S')
        }
        orjson_option = orjson.OPT_SERIALIZE_NUMPY | orjson.OPT_NAIVE_UTC

def get_dashboard_data_optimized(user_id):
    """Get dashboard data with efficient serialization."""
    # Fetch user data
    user = get_user(user_id)
    
    # Fetch various dashboard components (same as before)
    recent_orders = get_recent_orders(user_id)
    notifications = get_notifications(user_id)
    recommendations = get_recommendations(user_id)
    account_summary = get_account_summary(user_id)
    
    # Create Pydantic models
    user_data = UserData(
        id=user.id,
        name=user.name,
        email=user.email,
        avatar=user.avatar,
        preferences=user.preferences
    )
    
    orders_data = [
        OrderData(
            id=order.id,
            date=order.date,
            product=order.product.name,
            amount=order.amount,
            status=order.status
        )
        for order in recent_orders
    ]
    
    notifications_data = [
        NotificationData(
            id=notification.id,
            type=notification.type,
            message=notification.message,
            read=notification.read,
            date=notification.date
        )
        for notification in notifications
    ]
    
    recommendations_data = [
        RecommendationData(
            id=rec.id,
            product=rec.product.name,
            image=rec.product.image,
            price=rec.product.price,
            discount=rec.discount
        )
        for rec in recommendations
    ]
    
    account_data = AccountData(
        balance=account_summary.balance,
        pending=account_summary.pending,
        last_payment=account_summary.last_payment,
        next_payment=account_summary.next_payment
    )
    
    # Create and serialize dashboard in one step
    dashboard = Dashboard(
        user=user_data,
        recent_orders=orders_data,
        notifications=notifications_data,
        recommendations=recommendations_data,
        account=account_data
    )
    
    # Use orjson for faster serialization
    return orjson.dumps(dashboard.dict())
```

### 4.2 API Response Caching

**Original Code (Inefficient):**
```python
def get_product_details(product_id):
    """Get detailed product information without caching."""
    # Fetch product from database
    product = db.execute(
        "SELECT id, name, description, price, category FROM products WHERE id = ?", 
        [product_id]
    ).fetchone()
    
    if not product:
        return None
    
    # Fetch additional data with separate queries
    images = db.execute(
        "SELECT id, url, alt_text FROM product_images WHERE product_id = ?",
        [product_id]
    ).fetchall()
    
    specs = db.execute(
        "SELECT name, value FROM product_specs WHERE product_id = ?",
        [product_id]
    ).fetchall()
    
    reviews = db.execute(
        "SELECT id, user_id, rating, comment, created_at FROM reviews WHERE product_id = ?",
        [product_id]
    ).fetchall()
    
    # Calculate average rating
    avg_rating = 0
    if reviews:
        avg_rating = sum(review[2] for review in reviews) / len(reviews)
    
    # Build response
    response = {
        'id': product[0],
        'name': product[1],
        'description': product[2],
        'price': product[3],
        'category': product[4],
        'images': [{'id': img[0], 'url': img[1], 'alt_text': img[2]} for img in images],
        'specifications': [{'name': spec[0], 'value': spec[1]} for spec in specs],
        'reviews': [
            {
                'id': review[0],
                'user_id': review[1],
                'rating': review[2],
                'comment': review[3],
                'created_at': review[4].strftime('%Y-%m-%d %H:%M:%S')
            }
            for review in reviews
        ],
        'average_rating': avg_rating
    }
    
    return response
```

**PyPerfOptimizer Insight:**
```
API Profiling Results:
- Expensive database operations for each request
- Static data being repeatedly fetched
- Multiple database round-trips
- No caching for frequently accessed products
Recommendations:
1. Implement response caching with appropriate TTL
2. Use JOIN queries to reduce database round-trips
3. Implement cache invalidation on product updates
```

**Optimized Code:**
```python
import time
import json
from functools import lru_cache

# In-memory cache with expiration
cache = {}
CACHE_TTL = 300  # 5 minutes in seconds

def get_cached_response(key, ttl=CACHE_TTL):
    """Get a cached response if valid."""
    if key in cache:
        data, timestamp = cache[key]
        if time.time() - timestamp < ttl:
            return data
    return None

def set_cached_response(key, data, ttl=CACHE_TTL):
    """Cache a response with the current timestamp."""
    cache[key] = (data, time.time())

def invalidate_product_cache(product_id):
    """Invalidate cache for a specific product."""
    if product_id in cache:
        del cache[product_id]

def get_product_details_optimized(product_id, use_cache=True):
    """Get detailed product information with caching."""
    # Check cache first
    if use_cache:
        cached_data = get_cached_response(product_id)
        if cached_data:
            return cached_data
    
    # Use a single JOIN query to fetch everything at once
    query = """
        SELECT 
            p.id, p.name, p.description, p.price, p.category,
            pi.id as image_id, pi.url as image_url, pi.alt_text,
            ps.name as spec_name, ps.value as spec_value,
            r.id as review_id, r.user_id, r.rating, r.comment, r.created_at
        FROM products p
        LEFT JOIN product_images pi ON p.id = pi.product_id
        LEFT JOIN product_specs ps ON p.id = ps.product_id
        LEFT JOIN reviews r ON p.id = r.product_id
        WHERE p.id = ?
    """
    
    rows = db.execute(query, [product_id]).fetchall()
    
    if not rows or rows[0][0] is None:
        return None
    
    # Initialize the response with product details
    response = {
        'id': rows[0][0],
        'name': rows[0][1],
        'description': rows[0][2],
        'price': rows[0][3],
        'category': rows[0][4],
        'images': [],
        'specifications': [],
        'reviews': [],
        'average_rating': 0
    }
    
    # Sets to track unique IDs to avoid duplicates from the JOIN
    image_ids = set()
    spec_names = set()
    review_ids = set()
    
    # Total rating for average calculation
    total_rating = 0
    review_count = 0
    
    # Process each row to extract the joined data
    for row in rows:
        # Add image if present and not already added
        if row[5] is not None and row[5] not in image_ids:
            image_ids.add(row[5])
            response['images'].append({
                'id': row[5],
                'url': row[6],
                'alt_text': row[7]
            })
        
        # Add spec if present and not already added
        if row[8] is not None and row[8] not in spec_names:
            spec_names.add(row[8])
            response['specifications'].append({
                'name': row[8],
                'value': row[9]
            })
        
        # Add review if present and not already added
        if row[10] is not None and row[10] not in review_ids:
            review_ids.add(row[10])
            if row[13] is not None:  # Ensure we have a rating
                total_rating += row[13]
                review_count += 1
                
            response['reviews'].append({
                'id': row[10],
                'user_id': row[11],
                'rating': row[13],
                'comment': row[14],
                'created_at': row[15].strftime('%Y-%m-%d %H:%M:%S') if row[15] else None
            })
    
    # Calculate average rating
    if review_count > 0:
        response['average_rating'] = total_rating / review_count
    
    # Cache the response before returning
    if use_cache:
        set_cached_response(product_id, response)
    
    return response

# For frequently accessed products, use an LRU cache decorator
@lru_cache(maxsize=100)
def get_product_details_lru_cached(product_id):
    """Get detailed product information with LRU caching."""
    # Call the optimized function without its own caching
    return get_product_details_optimized(product_id, use_cache=False)
```

## 5. Machine Learning Pipeline Optimization

### 5.1 Data Preprocessing Optimization

**Original Code (Inefficient):**
```python
def preprocess_dataset(csv_path):
    """Preprocess a dataset with inefficient operations."""
    # Load CSV into pandas
    import pandas as pd
    import numpy as np
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    
    df = pd.read_csv(csv_path)
    
    # Handle missing values
    df['age'].fillna(df['age'].mean(), inplace=True)
    df['income'].fillna(df['income'].median(), inplace=True)
    df['education'].fillna(df['education'].mode()[0], inplace=True)
    
    # One-hot encode categorical features
    categorical_cols = ['gender', 'occupation', 'education', 'marital_status']
    for col in categorical_cols:
        dummies = pd.get_dummies(df[col], prefix=col)
        df = pd.concat([df, dummies], axis=1)
        df.drop(col, axis=1, inplace=True)
    
    # Scale numerical features
    numerical_cols = ['age', 'income', 'debt', 'savings']
    scaler = StandardScaler()
    df[numerical_cols] = scaler.fit_transform(df[numerical_cols])
    
    # Create polynomial features
    for col in numerical_cols:
        df[f'{col}_squared'] = df[col] ** 2
    
    # Split features and target
    X = df.drop('target', axis=1)
    y = df['target']
    
    return X, y
```

**PyPerfOptimizer Insight:**
```
Machine Learning Pipeline Profiling Results:
- Inefficient CSV loading (53% of execution time)
- Redundant data copies in one-hot encoding
- Sequential feature transformations
- Memory-intensive polynomial feature creation
Recommendations:
1. Use optimized CSV loading
2. Pipeline transformations
3. Reduce data copies
4. Use sparse matrices for one-hot encoding
```

**Optimized Code:**
```python
def preprocess_dataset_optimized(csv_path):
    """Preprocess a dataset with efficient operations."""
    import pandas as pd
    import numpy as np
    from sklearn.compose import ColumnTransformer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler, OneHotEncoder
    from sklearn.impute import SimpleImputer
    
    # Load CSV more efficiently with only needed columns and dtypes
    dtypes = {
        'age': 'float32',
        'income': 'float32',
        'debt': 'float32',
        'savings': 'float32',
        'gender': 'category',
        'occupation': 'category',
        'education': 'category',
        'marital_status': 'category',
        'target': 'int8'
    }
    
    df = pd.read_csv(
        csv_path, 
        dtype=dtypes,
        usecols=list(dtypes.keys())
    )
    
    # Define column types
    categorical_cols = ['gender', 'occupation', 'education', 'marital_status']
    numerical_cols = ['age', 'income', 'debt', 'savings']
    
    # Create preprocessor with single pipeline
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', Pipeline([
                ('imputer', SimpleImputer(strategy='median')),
                ('scaler', StandardScaler())
            ]), numerical_cols),
            ('cat', Pipeline([
                ('imputer', SimpleImputer(strategy='most_frequent')),
                ('onehot', OneHotEncoder(sparse=True, handle_unknown='ignore'))
            ]), categorical_cols)
        ]
    )
    
    # Split features and target
    X = df.drop('target', axis=1)
    y = df['target']
    
    # Apply transformations efficiently
    X_transformed = preprocessor.fit_transform(X)
    
    return X_transformed, y, preprocessor  # Return preprocessor for test set transformation
```

### 5.2 Model Training Optimization

**Original Code (Inefficient):**
```python
def train_model(X, y):
    """Train a machine learning model inefficiently."""
    from sklearn.model_selection import GridSearchCV
    from sklearn.ensemble import RandomForestClassifier
    
    # Define parameter grid
    param_grid = {
        'n_estimators': [10, 50, 100, 200],
        'max_depth': [None, 10, 20, 30],
        'min_samples_split': [2, 5, 10],
        'min_samples_leaf': [1, 2, 4]
    }
    
    # Initialize model
    model = RandomForestClassifier(random_state=42)
    
    # Perform grid search with 5-fold cross-validation
    grid_search = GridSearchCV(
        model, param_grid, cv=5, scoring='accuracy', verbose=1
    )
    
    # Fit the model
    grid_search.fit(X, y)
    
    # Get best model
    best_model = grid_search.best_estimator_
    
    return best_model
```

**PyPerfOptimizer Insight:**
```
Machine Learning Pipeline Profiling Results:
- Exhaustive grid search with 144 combinations
- Sequential parameter evaluation
- Inefficient cross-validation
- High memory usage during training
Recommendations:
1. Use RandomizedSearchCV instead of exhaustive grid search
2. Implement parallel processing
3. Use more efficient cross-validation strategy
4. Optimize model hyperparameters iteratively
```

**Optimized Code:**
```python
def train_model_optimized(X, y):
    """Train a machine learning model efficiently."""
    from sklearn.model_selection import RandomizedSearchCV
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.model_selection import StratifiedKFold
    import numpy as np
    from joblib import parallel_backend
    
    # Define parameter distributions
    param_dist = {
        'n_estimators': np.logspace(1, 3, num=10, base=10, dtype=int),
        'max_depth': [None, *list(np.linspace(10, 100, num=5, dtype=int))],
        'min_samples_split': [2, 5, 10, 15, 20],
        'min_samples_leaf': [1, 2, 4, 8],
        'max_features': ['auto', 'sqrt', 'log2']
    }
    
    # Initialize model with better defaults
    model = RandomForestClassifier(
        random_state=42,
        n_jobs=-1,  # Use all cores
        oob_score=True,  # Out-of-bag estimation
        bootstrap=True
    )
    
    # Use stratified k-fold for more consistent evaluation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    
    # Use randomized search with early stopping
    n_iter = 30  # Try 30 combinations instead of exhaustive 144
    search = RandomizedSearchCV(
        model, 
        param_distributions=param_dist, 
        n_iter=n_iter,
        cv=cv, 
        scoring='accuracy', 
        verbose=1,
        random_state=42,
        n_jobs=-1,  # Parallel processing
        return_train_score=True
    )
    
    # Use parallel backend for training
    with parallel_backend('loky', n_jobs=-1):
        search.fit(X, y)
    
    # Get best model
    best_model = search.best_estimator_
    
    # Optional: Fine-tune around best parameters
    best_params = search.best_params_
    fine_tune_params = {
        'n_estimators': [
            max(10, int(best_params['n_estimators'] * 0.8)),
            best_params['n_estimators'],
            min(1000, int(best_params['n_estimators'] * 1.2))
        ],
        'max_depth': (
            [int(best_params['max_depth'] * 0.8), best_params['max_depth'], int(best_params['max_depth'] * 1.2)]
            if best_params['max_depth'] is not None else [None, 10, 20]
        )
    }
    
    # Fine-tuning with grid search
    from sklearn.model_selection import GridSearchCV
    fine_tune = GridSearchCV(
        best_model, 
        fine_tune_params, 
        cv=cv, 
        scoring='accuracy',
        verbose=1,
        n_jobs=-1
    )
    
    with parallel_backend('loky', n_jobs=-1):
        fine_tune.fit(X, y)
    
    return fine_tune.best_estimator_
```

## Conclusion

These examples demonstrate how PyPerfOptimizer identifies specific performance bottlenecks and suggests concrete optimizations. Each optimization approach is tailored to the specific performance issue detected by the profiling tools:

1. **Algorithmic Optimizations**:
   - Memoization for recursive algorithms
   - Specialized data structures for specific operations
   - Time-space tradeoffs for better performance

2. **Memory Optimizations**:
   - Bounds on collection sizes
   - Generator expressions instead of materialized lists
   - Conversion of class variables to instance variables
   - Efficient data structures (NumPy arrays, sparse matrices)

3. **Database Optimizations**:
   - Batch queries to eliminate N+1 problems
   - Proper indexing strategies
   - Query reordering for index utilization
   - Connection pooling and resource management

4. **API Performance**:
   - Efficient serialization with specialized libraries
   - Response caching with appropriate invalidation
   - Reduction in data transformations
   - Optimized data formatting

5. **Machine Learning Pipeline**:
   - Efficient data loading and preprocessing
   - Parallel and randomized hyperparameter search
   - Pipeline-based transformations
   - Optimized memory usage during training

By applying these optimizations as suggested by PyPerfOptimizer, developers can achieve significant performance improvements across various types of Python applications.