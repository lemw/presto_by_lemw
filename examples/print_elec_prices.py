import network
import time
import urequests
import secrets
from presto import Presto

# Initialize Presto
presto = Presto(full_res=True)
display = presto.display
WIDTH, HEIGHT = display.get_bounds()

BLACK = display.create_pen(0, 0, 0)
WHITE = display.create_pen(255, 255, 255)

def connect_wifi():
    print("Connecting to WiFi...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(secrets.WIFI_SSID, secrets.WIFI_PASSWORD)
    
    # Wait for connection
    max_wait = 10
    while max_wait > 0:
        if wlan.isconnected(): 
            print(f"Connected to {secrets.WIFI_SSID}")
            break
        max_wait -= 1
        print(f"Waiting for connection... {max_wait} attempts left")
        time.sleep(1)

def get_data(date_str):
    print(f"Fetching data for {date_str}...")
    url = f"https://www.elprisetjustnu.se/api/v1/prices/{date_str}_SE3.json"
    try:
        r = urequests.get(url)
        if r.status_code == 200:
            print("Data received, parsing JSON...")
            data = r.json()
            r.close()
            print(f"Received {len(data)} entries for {date_str}")
            return data
        else:
            print(f"HTTP error: {r.status_code}")
        r.close()
    except Exception as e:
        print(f"Error fetching data: {e}")
    return []

def run():
    connect_wifi()
    
    # Show connection status on screen
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    display.text(f"Connected to {secrets.WIFI_SSID}", 10, 10)
    presto.update()
    time.sleep(1)
    
    # Get current date info
    now = time.localtime()
    today = "{:04d}/{:02d}-{:02d}".format(now[0], now[1], now[2])
    today_iso = f"{now[0]:04d}-{now[1]:02d}-{now[2]:02d}"
    print(f"Today's date: {today}")
    
    # Calculate tomorrow's date
    tomorrow_ts = time.time() + 86400
    tm = time.localtime(tomorrow_ts)
    tomorrow = "{:04d}/{:02d}-{:02d}".format(tm[0], tm[1], tm[2])
    tomorrow_iso = f"{tm[0]:04d}-{tm[1]:02d}-{tm[2]:02d}"
    print(f"Tomorrow's date: {tomorrow}")

    # Show fetching status
    display.text("Fetching today's and tomorrow's data...", 10, 30)
    presto.update()

    # Fetch tomorrow's data (usually available after 14:00)
    all_prices = get_data(today)
    all_prices += get_data(tomorrow)

    # Show processing status
    display.text("Processing data...", 10, 50)
    presto.update()

    print(f"Total raw entries: {len(all_prices)}")

    # Consolidate data hour by hour
    hour_prices = {}
    for entry in all_prices:
        t = entry['time_start']
        hour = t[:13]  # "2024-01-20T21"
        if hour not in hour_prices:
            hour_prices[hour] = []
        hour_prices[hour].append(entry['SEK_per_kWh'])
    
    consolidated = []
    for hour in sorted(hour_prices):
        prices = hour_prices[hour]
        avg_price = sum(prices) / len(prices)
        time_start = hour + ":00:00"
        consolidated.append({'time_start': time_start, 'SEK_per_kWh': avg_price})
    
    all_prices = consolidated
    print(f"Consolidated to {len(all_prices)} hourly entries")

    # Group by day
    today_entries = [e for e in all_prices if e['time_start'].startswith(today_iso)]
    tomorrow_entries = [e for e in all_prices if e['time_start'].startswith(tomorrow_iso)]

    # Show displaying status
    display.text("Displaying prices...", 10, 70)
    presto.update()
    time.sleep(1)

    # Now display the prices
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    
    if not all_prices:
        print("No data found")
        display.text("No data found", 10, 10)
    else:
        print("Displaying prices...")
        display.text("SE3 Prices (SEK/kWh)", 10, 10)
        
        # Column headers
        display.text("Today", 10, 30, scale=2)
        display.text("Tomorrow", 250, 30, scale=2)
        
        # Calculate min and max prices for color scaling
        min_price = min(entry['SEK_per_kWh'] for entry in all_prices)
        max_price = max(entry['SEK_per_kWh'] for entry in all_prices)
        
        line_height = 14  # Adjusted for alignment
        
        # Start columns at y=20 for more space
        y_start = 45
        
        # Display today's entries, aligned by hour
        x = 10
        for entry in today_entries:
            t = entry['time_start']
            hour_num = int(t[11:13])
            y = y_start + hour_num * line_height
            if y > HEIGHT - 16:  # Skip if below screen
                continue
            display_time = f"{t[11:16]}"  # Just time, since date is header
            price = entry['SEK_per_kWh']
            txt = f"{display_time}: {price:.2f}"
            
            # Calculate color
            if max_price > min_price:
                norm = (price - min_price) / (max_price - min_price)
            else:
                norm = 0.0
            
            if norm <= 0.5:
                r = int(510 * norm)
                g = 255
                b = 0
            else:
                r = 255
                g = int(255 - 510 * (norm - 0.5))
                b = 0
            
            color = display.create_pen(r, g, b)
            display.set_pen(color)
            
            display.text(txt, x, y, scale=2)
        
        # Display tomorrow's entries, aligned by hour
        x = 250
        for entry in tomorrow_entries:
            t = entry['time_start']
            hour_num = int(t[11:13])
            y = y_start + hour_num * line_height
            if y > HEIGHT - 16:  # Skip if below screen
                continue
            display_time = f"{t[11:16]}"
            price = entry['SEK_per_kWh']
            txt = f"{display_time}: {price:.2f}"
            
            # Calculate color
            if max_price > min_price:
                norm = (price - min_price) / (max_price - min_price)
            else:
                norm = 0.0
            
            if norm <= 0.5:
                r = int(510 * norm)
                g = 255
                b = 0
            else:
                r = 255
                g = int(255 - 510 * (norm - 0.5))
                b = 0
            
            color = display.create_pen(r, g, b)
            display.set_pen(color)
            
            display.text(txt, x, y, scale=2)

    presto.update()

run()