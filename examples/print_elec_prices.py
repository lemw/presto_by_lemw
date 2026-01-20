import network
import time
import urequests
import secrets
import math
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

def fetch_and_process_data(today, tomorrow):
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
    
    return all_prices

def display_prices(all_prices, today_entries, tomorrow_entries):
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
        
        line_height = 15  # For better spacing
        
        # Start columns at y=45 as requested
        y_start = 45
        
        # Display today's entries, aligned by hour
        x = 10
        for entry in today_entries:
            t = entry['time_start']
            hour_num = int(t[11:13])
            y = y_start + hour_num * line_height - 1
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
            y = y_start + hour_num * line_height - 1
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

def display_plot(all_prices):
    display.set_pen(BLACK)
    display.clear()
    display.set_pen(WHITE)
    
    prices = [e['SEK_per_kWh'] for e in all_prices]
    min_p = min(prices)
    max_p = max(prices)
    plot_width = WIDTH - 60  # Leave space for axis
    plot_height = HEIGHT - 20
    x_offset = 60
    y_offset = 10
    
    # Draw axes
    display.line(x_offset, y_offset, x_offset, y_offset + plot_height)  # Vertical axis
    display.line(x_offset, y_offset + plot_height, x_offset + plot_width, y_offset + plot_height)  # Horizontal axis
    
    # Draw scale on left
    num_ticks = 5
    for i in range(num_ticks + 1):
        tick_y = y_offset + plot_height - i * plot_height // num_ticks
        tick_value = min_p + i * (max_p - min_p) / num_ticks
        display.line(x_offset - 5, tick_y, x_offset, tick_y)  # Tick mark
        display.text(f"{tick_value:.2f}", 5, tick_y - 5, scale=1)
    
    # Draw the plot lines (2 pixels wide)
    for i in range(len(prices) - 1):
        x1 = x_offset + i * plot_width // (len(prices) - 1)
        y1 = y_offset + plot_height - int((prices[i] - min_p) / (max_p - min_p) * plot_height)
        x2 = x_offset + (i + 1) * plot_width // (len(prices) - 1)
        y2 = y_offset + plot_height - int((prices[i + 1] - min_p) / (max_p - min_p) * plot_height)
        display.line(x1, y1, x2, y2)
        display.line(x1, y1 + 1, x2, y2 + 1)  # Second line for 2-pixel width

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

    all_prices = fetch_and_process_data(today, tomorrow)

    # Group by day
    today_entries = [e for e in all_prices if e['time_start'].startswith(today_iso)]
    tomorrow_entries = [e for e in all_prices if e['time_start'].startswith(tomorrow_iso)]

    # Initial display
    display_prices(all_prices, today_entries, tomorrow_entries)
    presto.update()

    state = 'prices'
    last_touched = False
    start_x = None
    start_y = None

    while True:
        presto.touch_poll()
        touched = presto.touch_a.touched
        
        if touched and not last_touched:
            start_x = presto.touch_a.x
            start_y = presto.touch_a.y
        elif not touched and last_touched:
            if start_x is not None:
                end_x = presto.touch_a.x
                end_y = presto.touch_a.y
                dx = end_x - start_x
                dy = end_y - start_y
                distance = math.sqrt(dx**2 + dy**2)
                angle = math.atan2(dy, dx) * 180 / math.pi % 360
                print(f"Swipe detected: distance {distance:.1f}, angle {angle:.1f}")
                if distance > 30 and 60 <= angle <= 120:
                    # Refresh data
                    display.set_pen(BLACK)
                    display.clear()
                    display.set_pen(WHITE)
                    all_prices = fetch_and_process_data(today, tomorrow)
                    today_entries = [e for e in all_prices if e['time_start'].startswith(today_iso)]
                    tomorrow_entries = [e for e in all_prices if e['time_start'].startswith(tomorrow_iso)]
                    display_prices(all_prices, today_entries, tomorrow_entries)
                    presto.update()
                    state = 'prices'
            start_x = None
            start_y = None

        if state == 'prices':
            if touched and not last_touched:
                display_plot(all_prices)
                presto.update()
                state = 'plot'
        elif state == 'plot':
            if touched and not last_touched:
                display_prices(all_prices, today_entries, tomorrow_entries)
                presto.update()
                state = 'prices'

        last_touched = touched
        time.sleep(0.1)  # Small delay to debounce

run()