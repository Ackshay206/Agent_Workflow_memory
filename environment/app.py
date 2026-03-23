"""
FastAPI web server that serves real HTML pages for the simulated environment.
The agent uses Playwright to navigate these pages, extract the DOM, and
interact with elements — just like a real web agent.

Run from project root:
    python -m environment.app

Then visit http://localhost:3000 in a browser to see the pages.
"""

from fastapi import FastAPI, Form, Query
from fastapi.responses import HTMLResponse
from typing import Optional

try:
    from .pages import (
        FLIGHT_HOME, FLIGHT_RESULTS, FLIGHT_CONFIRM,
        SHOP_HOME, SHOP_RESULTS, SHOP_PRODUCT, SHOP_CART,
        RESTO_HOME, RESTO_RESULTS, RESTO_CONFIRM, RESTO_DONE,
        SHARED_STYLE, HOME_PAGE,
    )
except ImportError:
    from pages import (
        FLIGHT_HOME, FLIGHT_RESULTS, FLIGHT_CONFIRM,
        SHOP_HOME, SHOP_RESULTS, SHOP_PRODUCT, SHOP_CART,
        RESTO_HOME, RESTO_RESULTS, RESTO_CONFIRM, RESTO_DONE,
        SHARED_STYLE, HOME_PAGE,
    )

app = FastAPI(title="Simulated Web Environment")


def styled(html: str) -> str:
    """Prepend shared CSS to any HTML page."""
    return SHARED_STYLE + html


# ---------------------------------------------------------------------------
# Home page
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home():
    return styled(HOME_PAGE)


# ---------------------------------------------------------------------------
# Flight Search
# ---------------------------------------------------------------------------

@app.get("/flights", response_class=HTMLResponse)
async def flights_home():
    return styled(FLIGHT_HOME)


@app.get("/flights/results", response_class=HTMLResponse)
async def flights_results(
    origin: Optional[str] = Query(""),
    destination: Optional[str] = Query(""),
    date: Optional[str] = Query(""),
    passengers: Optional[str] = Query("1"),
    trip_type: Optional[str] = Query("round-trip"),
):
    if not origin or not destination or not date:
        return styled(
            FLIGHT_HOME.replace(
                "</form>",
                '<p class="error-msg">Please fill in all required fields.</p></form>'
            )
        )

    return styled(
        FLIGHT_RESULTS.format(
            origin=origin, destination=destination,
            date=date, passengers=passengers,
        )
    )


@app.get("/flights/confirm", response_class=HTMLResponse)
async def flights_confirm(
    flight: Optional[str] = Query(""),
    origin: Optional[str] = Query(""),
    destination: Optional[str] = Query(""),
    date: Optional[str] = Query(""),
    passengers: Optional[str] = Query("1"),
):
    return styled(
        FLIGHT_CONFIRM.format(
            flight=flight, origin=origin, destination=destination,
            date=date, passengers=passengers,
        )
    )


# ---------------------------------------------------------------------------
# Product Search
# ---------------------------------------------------------------------------

@app.get("/shop", response_class=HTMLResponse)
async def shop_home():
    return styled(SHOP_HOME)


@app.get("/shop/results", response_class=HTMLResponse)
async def shop_results(
    query: Optional[str] = Query(""),
    sort_by: Optional[str] = Query("relevance"),
):
    if not query:
        return styled(
            SHOP_HOME.replace(
                "</form>",
                '<p class="error-msg">Please enter a search term.</p></form>'
            )
        )

    sel = {
        "sel_relevance": 'selected' if sort_by == "relevance" else "",
        "sel_price_asc": 'selected' if sort_by == "price low to high" else "",
        "sel_price_desc": 'selected' if sort_by == "price high to low" else "",
        "sel_rating": 'selected' if sort_by == "rating" else "",
    }

    return styled(SHOP_RESULTS.format(query=query, **sel))


@app.get("/shop/product", response_class=HTMLResponse)
async def shop_product(
    id: Optional[str] = Query(""),
    name: Optional[str] = Query("Product"),
    price: Optional[str] = Query("0.00"),
    query: Optional[str] = Query(""),
):
    return styled(
        SHOP_PRODUCT.format(id=id, name=name, price=price, query=query)
    )


@app.post("/shop/cart", response_class=HTMLResponse)
async def shop_cart(
    product_name: str = Form("Item"),
):
    return styled(SHOP_CART.format(product_name=product_name))


# ---------------------------------------------------------------------------
# Restaurant Reservation
# ---------------------------------------------------------------------------

@app.get("/restaurant", response_class=HTMLResponse)
async def resto_home():
    return styled(RESTO_HOME)


@app.get("/restaurant/results", response_class=HTMLResponse)
async def resto_results(
    city: Optional[str] = Query(""),
    date: Optional[str] = Query(""),
    time: Optional[str] = Query("7:00 PM"),
    party_size: Optional[str] = Query("2"),
):
    if not city or not date:
        return styled(
            RESTO_HOME.replace(
                "</form>",
                '<p class="error-msg">Please fill in city and date.</p></form>'
            )
        )

    return styled(
        RESTO_RESULTS.format(
            city=city, date=date, time=time, party_size=party_size,
        )
    )


@app.get("/restaurant/confirm", response_class=HTMLResponse)
async def resto_confirm(
    name: Optional[str] = Query("Restaurant"),
    city: Optional[str] = Query(""),
    date: Optional[str] = Query(""),
    time: Optional[str] = Query(""),
    party_size: Optional[str] = Query("2"),
):
    return styled(
        RESTO_CONFIRM.format(
            name=name, city=city, date=date, time=time, party_size=party_size,
        )
    )


@app.post("/restaurant/done", response_class=HTMLResponse)
async def resto_done(
    name: str = Form("Restaurant"),
    city: str = Form(""),
    date: str = Form(""),
    time: str = Form(""),
    party_size: str = Form("2"),
):
    return styled(
        RESTO_DONE.format(
            name=name, city=city, date=date, time=time, party_size=party_size,
        )
    )


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    print("Simulated web environment running on http://localhost:3000")
    print()
    print("  ✈  http://localhost:3000/flights")
    print("  🛒  http://localhost:3000/shop")
    print("  🍽  http://localhost:3000/restaurant")
    print()
    uvicorn.run(app, host="0.0.0.0", port=3000)
