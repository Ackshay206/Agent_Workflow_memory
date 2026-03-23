"""
HTML templates for each page. These are real web pages that Playwright can
navigate, read the DOM, and interact with (click, type, select).

Each template uses simple, semantic HTML with clear labels and IDs so the
agent can parse the accessibility tree easily.

IMPORTANT ARCHITECTURE NOTE:
- SHARED_STYLE uses normal CSS braces { } and is NEVER passed to .format()
- Page templates that need dynamic values use {placeholders} and get .format() called
- Templates are combined with SHARED_STYLE at render time in app.py, NOT at definition time
  This avoids the CSS brace / Python format brace collision entirely.
"""

# ---------------------------------------------------------------------------
# Shared CSS — uses normal { } braces, never passed to .format()
# ---------------------------------------------------------------------------

SHARED_STYLE = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * { box-sizing: border-box; margin: 0; padding: 0; }

    body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        min-height: 100vh;
        color: #2d3748;
    }

    .container {
        max-width: 720px;
        margin: 40px auto;
        padding: 24px;
    }

    h1 {
        margin-bottom: 24px;
        color: #ffffff;
        font-size: 28px;
        font-weight: 700;
        text-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 28px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15),
                    0 2px 8px rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }

    label {
        display: block;
        font-weight: 600;
        margin: 14px 0 6px;
        color: #4a5568;
        font-size: 13px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }

    input[type="text"], input[type="date"], input[type="number"], select {
        width: 100%;
        padding: 12px 16px;
        border: 2px solid #e2e8f0;
        border-radius: 10px;
        font-size: 15px;
        font-family: 'Inter', sans-serif;
        color: #2d3748;
        background: #f7fafc;
        transition: all 0.2s ease;
        outline: none;
    }

    input[type="text"]:focus, input[type="date"]:focus,
    input[type="number"]:focus, select:focus {
        border-color: #667eea;
        background: #ffffff;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.15);
    }

    button, .btn {
        display: inline-block;
        padding: 12px 28px;
        margin-top: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        font-size: 15px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        cursor: pointer;
        text-decoration: none;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.35);
    }

    button:hover, .btn:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
    }

    button:active, .btn:active {
        transform: translateY(0);
    }

    .result-item {
        display: block;
        padding: 18px 20px;
        margin: 10px 0;
        background: rgba(255, 255, 255, 0.95);
        border: 2px solid rgba(102, 126, 234, 0.1);
        border-radius: 12px;
        text-decoration: none;
        color: #2d3748;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
    }

    .result-item:hover {
        background: #ffffff;
        border-color: #667eea;
        transform: translateY(-2px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.2);
    }

    .success-box {
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        border: none;
        border-radius: 16px;
        padding: 36px;
        text-align: center;
        color: #1a4731;
        box-shadow: 0 8px 32px rgba(67, 233, 123, 0.3);
    }

    .success-box h1 {
        color: #1a4731;
        text-shadow: none;
        font-size: 32px;
    }

    .price {
        font-weight: 700;
        color: #667eea;
        font-size: 16px;
    }

    .rating { color: #f6ad55; font-weight: 600; }

    .error-msg {
        color: #e53e3e;
        margin-top: 10px;
        font-weight: 500;
        background: #fff5f5;
        padding: 10px 14px;
        border-radius: 8px;
        border: 1px solid #feb2b2;
    }

    .home-hero {
        text-align: center;
        padding: 60px 20px;
    }

    .home-hero h1 {
        font-size: 42px;
        margin-bottom: 12px;
    }

    .home-hero p {
        color: rgba(255,255,255,0.85);
        font-size: 18px;
        margin-bottom: 36px;
    }

    .site-cards {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 20px;
    }

    .site-card {
        background: rgba(255,255,255,0.95);
        backdrop-filter: blur(10px);
        border-radius: 16px;
        padding: 32px 20px;
        text-align: center;
        text-decoration: none;
        color: #2d3748;
        transition: all 0.3s ease;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        border: 2px solid transparent;
    }

    .site-card:hover {
        transform: translateY(-6px);
        box-shadow: 0 12px 40px rgba(0,0,0,0.2);
        border-color: #667eea;
    }

    .site-card .icon {
        font-size: 48px;
        display: block;
        margin-bottom: 16px;
    }

    .site-card .label {
        font-weight: 700;
        font-size: 16px;
        color: #4a5568;
    }

    .subtitle {
        color: rgba(255,255,255,0.8);
        font-size: 15px;
        margin-bottom: 20px;
    }
</style>
"""

# ---------------------------------------------------------------------------
# Home Page — no .format() needed, standalone template
# ---------------------------------------------------------------------------

HOME_PAGE = """
<div class="container home-hero">
    <h1>🌐 Simulated Web Environment</h1>
    <p>Choose a site to browse:</p>
    <div class="site-cards">
        <a class="site-card" href="/flights">
            <span class="icon">✈️</span>
            <span class="label">Travel Site</span>
        </a>
        <a class="site-card" href="/shop">
            <span class="icon">🛒</span>
            <span class="label">Shopping Site</span>
        </a>
        <a class="site-card" href="/restaurant">
            <span class="icon">🍽️</span>
            <span class="label">Restaurant Site</span>
        </a>
    </div>
</div>
"""

# ---------------------------------------------------------------------------
# Flight Search Pages
# ---------------------------------------------------------------------------

FLIGHT_HOME = """
<div class="container">
    <h1>✈ Travel Site — Flight Search</h1>
    <div class="card">
        <form action="/flights/results" method="GET">
            <label for="trip_type">Trip Type</label>
            <select id="trip_type" name="trip_type">
                <option value="round-trip">Round Trip</option>
                <option value="one-way">One Way</option>
                <option value="multi-city">Multi City</option>
            </select>

            <label for="origin">From</label>
            <input type="text" id="origin" name="origin" placeholder="Departure city">

            <label for="destination">To</label>
            <input type="text" id="destination" name="destination" placeholder="Destination city">

            <label for="date">Departure Date</label>
            <input type="date" id="date" name="date">

            <label for="passengers">Number of Adults</label>
            <input type="number" id="passengers" name="passengers" value="1" min="1" max="9">

            <button type="submit" id="search_btn">Search Flights</button>
        </form>
    </div>
</div>
"""

FLIGHT_RESULTS = """
<div class="container">
    <h1>✈ Flight Results: {origin} → {destination}</h1>
    <p class="subtitle">Showing flights on {date} for {passengers} adult(s)</p>

    <a class="result-item" id="result_1" href="/flights/confirm?flight=AA123&origin={origin}&destination={destination}&date={date}&passengers={passengers}">
        <strong>Flight AA123</strong> — {origin} → {destination}<br>
        <span class="price">$199</span> · Departs 8:00 AM · Duration 2h 45m
    </a>

    <a class="result-item" id="result_2" href="/flights/confirm?flight=UA456&origin={origin}&destination={destination}&date={date}&passengers={passengers}">
        <strong>Flight UA456</strong> — {origin} → {destination}<br>
        <span class="price">$245</span> · Departs 12:30 PM · Duration 2h 30m
    </a>

    <a class="result-item" id="result_3" href="/flights/confirm?flight=DL789&origin={origin}&destination={destination}&date={date}&passengers={passengers}">
        <strong>Flight DL789</strong> — {origin} → {destination}<br>
        <span class="price">$178</span> · Departs 5:15 PM · Duration 3h 10m
    </a>
</div>
"""

FLIGHT_CONFIRM = """
<div class="container">
    <div class="success-box">
        <h1>✅ Flight Selected!</h1>
        <p style="margin-top:12px; font-size:18px;">
            <strong>{flight}</strong>: {origin} → {destination}<br>
            Date: {date} · Passengers: {passengers}
        </p>
        <p style="margin-top:16px; font-weight:600;" id="done_message">✅ SUCCESS: Flight booking task completed successfully!</p>
    </div>
</div>
"""

# ---------------------------------------------------------------------------
# Product Search Pages
# ---------------------------------------------------------------------------

SHOP_HOME = """
<div class="container">
    <h1>🛒 ShopSite — Product Search</h1>
    <div class="card">
        <form action="/shop/results" method="GET">
            <label for="search_box">Search Products</label>
            <input type="text" id="search_box" name="query" placeholder="What are you looking for?">

            <button type="submit" id="search_btn">Search</button>
        </form>
    </div>
</div>
"""

SHOP_RESULTS = """
<div class="container">
    <h1>🛒 Results for "{query}"</h1>
    <div class="card">
        <form action="/shop/results" method="GET" style="display:flex; gap:10px; align-items:end;">
            <input type="hidden" name="query" value="{query}">
            <div style="flex:1;">
                <label for="sort_by">Sort By</label>
                <select id="sort_by" name="sort_by">
                    <option value="relevance" {sel_relevance}>Relevance</option>
                    <option value="price low to high" {sel_price_asc}>Price: Low to High</option>
                    <option value="price high to low" {sel_price_desc}>Price: High to Low</option>
                    <option value="rating" {sel_rating}>Rating</option>
                </select>
            </div>
            <button type="submit" id="apply_sort_btn">Apply</button>
        </form>
    </div>

    <a class="result-item" id="product_1" href="/shop/product?id=1&name=Budget+{query}&price=29.99&query={query}">
        <strong>Budget {query}</strong><br>
        <span class="price">$29.99</span> · <span class="rating">★ 3.8</span>
    </a>

    <a class="result-item" id="product_2" href="/shop/product?id=2&name=Premium+{query}&price=89.99&query={query}">
        <strong>Premium {query}</strong><br>
        <span class="price">$89.99</span> · <span class="rating">★ 4.6</span>
    </a>

    <a class="result-item" id="product_3" href="/shop/product?id=3&name=Mid-range+{query}&price=54.99&query={query}">
        <strong>Mid-range {query}</strong><br>
        <span class="price">$54.99</span> · <span class="rating">★ 4.2</span>
    </a>
</div>
"""

SHOP_PRODUCT = """
<div class="container">
    <h1>🛒 {name}</h1>
    <div class="card">
        <p style="font-size:28px; margin-bottom:8px;" class="price">${price}</p>
        <p style="margin-top:8px; color:#718096;">High-quality product with great reviews.</p>
        <form action="/shop/cart" method="POST">
            <input type="hidden" name="product_id" value="{id}">
            <input type="hidden" name="product_name" value="{name}">
            <input type="hidden" name="query" value="{query}">
            <button type="submit" id="add_to_cart_btn">Add to Cart</button>
        </form>
        <a class="btn" href="/shop/results?query={query}" id="back_btn"
           style="background:linear-gradient(135deg,#718096,#4a5568); margin-left:8px;">Back to Results</a>
    </div>
</div>
"""

SHOP_CART = """
<div class="container">
    <div class="success-box">
        <h1>✅ Item Added to Cart!</h1>
        <p style="margin-top:12px; font-size:18px;">
            <strong>{product_name}</strong> has been added to your cart.
        </p>
        <p style="margin-top:16px; font-weight:600;" id="done_message">✅ SUCCESS: Shopping task completed successfully!</p>
    </div>
</div>
"""

# ---------------------------------------------------------------------------
# Restaurant Reservation Pages
# ---------------------------------------------------------------------------

RESTO_HOME = """
<div class="container">
    <h1>🍽 TableFinder — Restaurant Reservations</h1>
    <div class="card">
        <form action="/restaurant/results" method="GET">
            <label for="city">City</label>
            <input type="text" id="city" name="city" placeholder="Enter city">

            <label for="date">Date</label>
            <input type="date" id="date" name="date">

            <label for="time">Time</label>
            <select id="time" name="time">
                <option value="6:00 PM">6:00 PM</option>
                <option value="6:30 PM">6:30 PM</option>
                <option value="7:00 PM">7:00 PM</option>
                <option value="7:30 PM">7:30 PM</option>
                <option value="8:00 PM">8:00 PM</option>
                <option value="8:30 PM">8:30 PM</option>
                <option value="9:00 PM">9:00 PM</option>
            </select>

            <label for="party_size">Party Size</label>
            <input type="number" id="party_size" name="party_size" value="2" min="1" max="20">

            <button type="submit" id="find_btn">Find Tables</button>
        </form>
    </div>
</div>
"""

RESTO_RESULTS = """
<div class="container">
    <h1>🍽 Restaurants in {city}</h1>
    <p class="subtitle">{date} at {time} · Party of {party_size}</p>

    <a class="result-item" id="resto_1"
       href="/restaurant/confirm?name=Luigis+Italian&city={city}&date={date}&time={time}&party_size={party_size}">
        <strong>Luigi's Italian</strong><br>
        Italian · {city} · Table available at {time} · <span class="rating">★ 4.5</span>
    </a>

    <a class="result-item" id="resto_2"
       href="/restaurant/confirm?name=Sakura+Sushi&city={city}&date={date}&time={time}&party_size={party_size}">
        <strong>Sakura Sushi</strong><br>
        Japanese · {city} · Table available at {time} · <span class="rating">★ 4.7</span>
    </a>

    <a class="result-item" id="resto_3"
       href="/restaurant/confirm?name=The+Grill+House&city={city}&date={date}&time={time}&party_size={party_size}">
        <strong>The Grill House</strong><br>
        American · {city} · Table available at {time} · <span class="rating">★ 4.3</span>
    </a>
</div>
"""

RESTO_CONFIRM = """
<div class="container">
    <h1>🍽 Confirm Reservation</h1>
    <div class="card">
        <p><strong>{name}</strong></p>
        <p style="color:#718096; margin-top:4px;">{city} · {date} · {time} · Party of {party_size}</p>
        <form action="/restaurant/done" method="POST">
            <input type="hidden" name="name" value="{name}">
            <input type="hidden" name="city" value="{city}">
            <input type="hidden" name="date" value="{date}">
            <input type="hidden" name="time" value="{time}">
            <input type="hidden" name="party_size" value="{party_size}">
            <button type="submit" id="confirm_btn">Confirm Reservation</button>
        </form>
    </div>
</div>
"""

RESTO_DONE = """
<div class="container">
    <div class="success-box">
        <h1>✅ Reservation Confirmed!</h1>
        <p style="margin-top:12px; font-size:18px;">
            <strong>{name}</strong><br>
            {city} · {date} · {time} · Party of {party_size}
        </p>
        <p style="margin-top:16px; font-weight:600;" id="done_message">✅ SUCCESS: Restaurant reservation task completed successfully!</p>
    </div>
</div>
"""