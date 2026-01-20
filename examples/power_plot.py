import time
import urequests
import network
from presto import Presto
from ezwifi import EzWiFi
import secrets

# --- Settings ---
AREA = "SE3"
WIDTH, HEIGHT = 480, 480  # Presto Resolution

# Initialize Hardware
presto = Presto()
display = presto.display

# Define Colors
BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)
GREY = display.create_pen(80, 80, 80)
RED = display.create_pen(255, 70, 70)
YELLOW = display.create_pen(255, 255, 70)
GREEN = display.create_pen(70, 255, 70)

def connect_wifi():
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text("Connecting to WiFi...", 40, 220, scale=1)
    presto.update()
    
    ez = EzWiFi()
    # Explicitly attempt connection
    if ez.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD):
        return True
    return False

def fetch_prices():
    try:
        # Get data from mgrey.se API
        res = urequests.get("https://mgrey.se/espot?format=json")
        data = res.json()
        res.close()
        # Returns list of (hour, price_sek)
        return [(p['hour'], p['price_sek']) for p in data.get(AREA, [])]
    except Exception as e:
        print("API Error:", e)
        return None

def draw_gui(prices):
    display.set_pen(BLACK)
    display.clear()
    
    if not prices:
        display.set_pen(RED)
        display.text("Data Unavailable", 100, 220, scale=1)
        presto.update()
        return

    # Values for scaling
    vals = [p[1] for p in prices]
    max_p, min_p = max(vals), min(vals)
    top_6 = sorted(prices, key=lambda x: x[1], reverse=True)[:6]
    top_6_hours = [p[0] for p in top_6]

    # Layout Margins (Scaled for 480px)
    LEFT_M = 80
    BOTTOM_M = 100
    TOP_M = 100
    G_WIDTH = WIDTH - LEFT_M - 40
    G_HEIGHT = HEIGHT - BOTTOM_M - TOP_M
    
    # Draw Axes
    display.set_pen(GREY)
    display.line(LEFT_M, HEIGHT - BOTTOM_M, WIDTH - 20, HEIGHT - BOTTOM_M) # X
    display.line(LEFT_M, TOP_M, LEFT_M, HEIGHT - BOTTOM_M)                # Y
    
    # Draw Bars
    count = len(prices)
    step = G_WIDTH / count
    bar_w = max(2, int(step - 4))
    
    for i, (hour, price) in enumerate(prices):
        x = int(LEFT_M + (i * step))
        # Calculate height relative to price range
        norm_h = int(((price - min_p) / (max_p - min_p + 0.1)) * G_HEIGHT)
        y = (HEIGHT - BOTTOM_M) - norm_h
        
        # Color Coding
        ratio = (price - min_p) / (max_p - min_p + 0.1)
        if ratio > 0.7: color = RED
        elif ratio > 0.3: color = YELLOW
        else: color = GREEN
        
        display.set_pen(color)
        display.rectangle(x, y, bar_w, norm_h)
        
        # Label Top 6 Most Expensive
        if hour in top_6_hours:
            display.set_pen(WHITE)
            # Adjust text position so it doesn't go off screen
            display.text(f"{price:.1f}", x - 10, y - 30, scale=1)
            
        # X-Axis Time Labels (every 4-6 hours to avoid crowding)
        if i % 6 == 0:
            display.set_pen(GREY)
            display.text(f"{hour:02d}", x, HEIGHT - BOTTOM_M + 20, scale=1)

    # UI Header & Labels
    display.set_pen(WHITE)
    display.text(f"SE3 Spot Price", 30, 30, scale=1)
    display.text("ore/kWh", 350, 45, scale=1)
    
    # Y-Axis Max/Min Labels
    display.set_pen(RED)
    display.text(f"{max_p:.1f}", 10, TOP_M, scale=1)
    display.set_pen(GREEN)
    display.text(f"{min_p:.1f}", 10, HEIGHT - BOTTOM_M - 20, scale=1)

    presto.update()

# --- Main Execution ---
if connect_wifi():
    data = fetch_prices()
    draw_gui(data)
else:
    display.set_pen(RED)
    display.text("WiFi Failed", 150, 220, scale=1)
    presto.update()