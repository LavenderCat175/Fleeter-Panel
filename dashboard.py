import js
from pyscript import window, document
from pyodide.ffi import create_proxy, to_js

#Demo mode: Creates a set of tiles and ignores the server connection. For testing the ui only. 
DEMO_MODE = True

DEMO_DEVICES = [
    {"device_id": "a1b2c3d4e5f6g7h8", "blocked": False},
    {"device_id": "b2c3d4e5f6g7h8i9", "blocked": True},
    {"device_id": "c3d4e5f6g7h8i9j0", "blocked": False},
    {"device_id": "d4e5f6g7h8i9j0k1", "blocked": False},
    {"device_id": "e5f6g7h8i9j0k1l2", "blocked": True},
]

def load_demo_tiles():
    for device in DEMO_DEVICES:
        create_tile(device["device_id"], device["blocked"])

known_devices = {}
device_blocked = {}
tile_counter = 0
active_device_id = None
socket = None

def init():
    global socket

    if DEMO_MODE:
        print("[Demo] Running in demo mode — no server connection.")
        load_demo_tiles()
        return

    ip = window.localStorage.getItem("fleeter_ip")

    if not ip:
        print("[Dashboard] No server IP found. Redirecting to login...")
        window.location.href = "login.html"
        return
    
    print(f"[Dashboard] Found server IP: {ip}. Connecting to SocketIO...")

    socket = window.io(  # assigns to the global socket variable
        f"http://{ip}:3030/enforcer",
        to_js({"reconnection": True, "timeout": 5000}) # reconnection: True to automatically retry, timeout: 5000ms before giving up
    )

    def on_connect():
        print("[Dashboard] Connected to server! Listening for device updates...")
        socket.emit("dashboard_connected")  # Notify server that dashboard is ready
    
    def on_disconnect():
        print("[Dashboard] Disconnected from server. Attempting to reconnect...")
        socket.connect()  # Attempt to reconnect
    
    def on_heartbeat(data):
        device_id = data.device_id
        blocked = bool(data.blocked)

        if device_id not in known_devices:
            print(f"[Dashboard] New device detected: {device_id}")
            create_tile(device_id, blocked)
        else:
            update_tile(device_id, blocked)

    socket.on("connect", create_proxy(on_connect))
    socket.on("disconnect", create_proxy(on_disconnect))
    socket.on("heartbeat", create_proxy(on_heartbeat))

def create_tile(device_id, blocked):
    global tile_counter
    tile_counter += 1
    n = tile_counter
    known_devices[device_id] = n
    device_blocked[device_id] = blocked

    color_n = ((n - 1) % 5) + 1 # Cycle through 5 colors
    status = "busy" if blocked else "online"
    status_text = "blocked" if blocked else "active"
    short_id = device_id[:12]  # Show only first 12 chars for brevity

    tile_html = f"""
    <label class="tile" data-computer="{color_n}" data-status="{status}" data-device-id="{device_id}">
        <div class="tile-inner">
            <div class="tile-front">
                <div class="tile-picture">
                    <i class="fas fa-desktop"></i>
                </div>
                <div class="tile-content">
                    <div class="tile-title">Device {n}</div>
                    <div class="tile-subtitle">
                        <span class="status-dot"></span> {short_id} · {status_text}
                    </div>
                </div>
            </div>
            <div class="tile-back">
                <i class="fas fa-eye"></i>
                <h3>Device {n}</h3>
                <p>manage this computer</p>
            </div>
        </div>
    </label>
    """
    document.querySelector(".tile-grid").insertAdjacentHTML("beforeend", tile_html)
    
    tile_element = document.querySelector(f'[data-device-id="{device_id}"]')
    tile_element.addEventListener("click", create_proxy(lambda e, did=device_id: open_sidebar(did)))

def update_tile(device_id, blocked):
    device_blocked[device_id] = blocked

    status = "busy" if blocked else "online"
    status_text = "blocked" if blocked else "active"
    short_id = device_id[:12]

    tile = document.querySelector(f'[data-device-id="{device_id}"]')
    tile.setAttribute("data-status", status)
    tile.querySelector(".tile-subtitle").innerHTML = (
        f'<span class="status-dot"></span> {short_id} · {status_text}'
    )

    if device_id == active_device_id:
        btn = document.getElementById("blockButton")
        btn.innderHTML = '<i class="fas fa-lock-open"></i> Unblock screen' if blocked else '<i class="fas fa-ban"></i> Block screen'



def open_sidebar(device_id):
    global active_device_id
    active_device_id = device_id
    n = known_devices[device_id]

    print(f"[Dashboard] Opening sidebar for device {device_id} (Device {n})")

    # Unflip any previously flipped tile, then flip the clicked one
    prev = document.querySelector(".tile-inner.flipped")
    if prev:
        prev.classList.remove("flipped")
    tile = document.querySelector(f'[data-device-id="{device_id}"]')
    tile.querySelector(".tile-inner").classList.add("flipped")

    # Push the tile grid to make room for the sidebar
    document.querySelector(".tile-container").style.marginRight = "380px"

    blocked = device_blocked.get(device_id, False)

    document.getElementById("sidebarComputerName").textContent = f"Device {n}"
    document.getElementById("sidebarDeviceId").textContent = device_id
    document.getElementById("sidebarStatus").textContent = "Blocked" if blocked else "Active"
    document.getElementById("sidebarStatusBadge").textContent = "🔴 Blocked" if blocked else "🟢 Active"

    btn = document.getElementById("blockButton")
    btn.innerHTML = '<i class="fas fa-lock-open"></i> Unblock screen' if blocked else '<i class="fas fa-ban"></i> Block screen'

    document.querySelector(".info-sidebar").style.transform = "translateX(0)"


def toggle_block(event):
    if not active_device_id:
        return

    new_blocked = not device_blocked.get(active_device_id, False)
    device_blocked[active_device_id] = new_blocked

    print(f"[Dashboard] {'Blocking' if new_blocked else 'Unblocking'} device {active_device_id}")

    if not DEMO_MODE:
        socket.emit("fleet_control", to_js({
            "devices": [active_device_id],
            "orders": {"control": {"blocked": new_blocked}}
        }))

    # Update button text
    btn = document.getElementById("blockButton")
    btn.innerHTML = '<i class="fas fa-lock-open"></i> Unblock screen' if new_blocked else '<i class="fas fa-ban"></i> Block screen'

    # Update tile status dot
    tile = document.querySelector(f'[data-device-id="{active_device_id}"]')
    status = "busy" if new_blocked else "online"
    status_text = "blocked" if new_blocked else "active"
    short_id = active_device_id[:12]
    tile.setAttribute("data-status", status)
    tile.querySelector(".tile-subtitle").innerHTML = (
        f'<span class="status-dot"></span> {short_id} · {status_text}'
    )


def close_sidebar(event):
    print("[Dashboard] Closing sidebar")

    # Unflip the active tile
    prev = document.querySelector(".tile-inner.flipped")
    if prev:
        prev.classList.remove("flipped")

    # Pull the tile grid back
    document.querySelector(".tile-container").style.marginRight = "0"

    document.querySelector(".info-sidebar").style.transform = "translateX(100%)"

document.getElementById("closeSidebar").addEventListener("click", create_proxy(close_sidebar))
document.getElementById("blockButton").addEventListener("click", create_proxy(toggle_block))

init()