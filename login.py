import js
import asyncio
from pyodide.ffi import create_proxy, to_js
from pyscript import window, document
from urllib.parse import urlencode

def sign_in(event):
    event.preventDefault()
    asyncio.ensure_future(_sign_in_async(event))

async def _sign_in_async(event):

    ip       = document.getElementById("ip").value.strip()
    email    = document.getElementById("email").value.strip()
    password = document.getElementById("password").value.strip()

    # Hide all previous errors
    for error_id in ["ipError", "emailError", "passwordError"]:
        document.getElementById(error_id).style.display = "none"

    # Validate — stop if anything is empty
    valid = True
    if not ip:
        document.getElementById("ipError").style.display = "block"
        valid = False
    if not email:
        document.getElementById("emailError").style.display = "block"
        valid = False
    if not password:
        document.getElementById("passwordError").style.display = "block"
        valid = False
    if not valid:
        return

    # Change the button
    btn = document.getElementById("loginButton")
    btn.textContent = "Connecting..."
    btn.disabled = True
    
    print("[Login] Requesting token from Keycloak...")
    token_url = f"http://{ip}:7777/keycloak/realms/fleeter-server/protocol/openid-connect/token"
    body= urlencode({
        "grant_type": "password",
        "client_id": "fleeter-panel",
        "username": email,
        "password": password,
        "scope": "openid profile",
    })

    try:
        response = await js.fetch(token_url, to_js({
            "method": "POST",
            "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            "body": body
        }))
        if not response.ok:
            raise Exception(f"HTTP error! status: {response.status}")
        data = await response.json()
        token = data.access_token
        print("[Login] Token received from Keycloak.")
    except Exception as e:
        print(f"[Login] Failed to get token: {e}")
        btn.textContent = "Sign In"
        btn.disabled = False
        document.getElementById("ipError").style.display = "block"
        document.getElementById("ipError").textContent = "Failed to authenticate with Keycloak."
        return
    
    print("[Login] Connecting to Socket.IO server...")
    socket = window.io(f"http://{ip}:7777/enforcer", to_js({
        "path":        "/socket",
        "reconnection": False,
        "timeout":      5000,
        "auth":         {"token": token}
    }))

    def on_connect():
        print("[Login] Connected! Redirecting to dashboard...")
        window.localStorage.setItem("fleeter_ip", ip)  # store IP for the dashboard
        window.localStorage.setItem("fleeter_token", token)  # store token for future authenticated requests
        socket.disconnect()  # we just needed to verify the server is reachable
        window.location.href = "dashboard.html"  # redirect to dashboard

    def on_connect_error(error):
        print(f"[Login] Connection failed: {error}")
        btn.textContent = "Sign In"
        btn.disabled = False
        document.getElementById("ipError").style.display = "block"
        document.getElementById("ipError").textContent = "Failed to connect to the server."

    socket.on("connect",       create_proxy(on_connect))
    socket.on("connect_error", create_proxy(on_connect_error))

# Attach the function to the form's submit event
form = document.querySelector(".login-form")
form.addEventListener("submit", create_proxy(sign_in))

#password toggle icon function
def toggle_password(event):
    pwd = document.getElementById("password")
    icon = document.querySelector("#passwordToggle .eye-i i")

    if pwd.type == "password":
        pwd.type = "text"
        icon.classList.remove("fa-eye")
        icon.classList.add("fa-eye-slash")
    else:
        pwd.type = "password"
        icon.classList.remove("fa-eye-slash")
        icon.classList.add("fa-eye")

toggle_btn = document.getElementById("passwordToggle")
toggle_btn.addEventListener("click", create_proxy(toggle_password))
