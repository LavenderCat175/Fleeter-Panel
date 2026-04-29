#Commit 29/05: Finished the login.py file. Still needs the following: 1. Polishing (currently holds on for dear life and some deepseek prompts) 2. The actual login logic (currently it just checks for the IP. If what I understand is correct, the email & password logic is currently not implemented. Could maybe handle that in the future)
#by the way: pyodide is a pain. I hardly understand any of the documentation and i want to commit sudoku. Some lifechoices were reconsidered during the developement process. Money may have been invested ina premium AI plan.  
import js
from pyodide.ffi import create_proxy, to_js
from pyscript import window, document

#Should run when the user hits "Sign In"

def sign_in(event):
    event.preventDefault()  # Stops the form from submitting and refreshing the page

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

    # Connect to the server using SocketIO
    print(f"[Login] Attempting connection to http://{ip}:3030/enforcer ...")
    socket = window.io(
        f"http://{ip}:3030/enforcer",
        to_js({"reconnection": False, "timeout": 5000})
        # reconnection: False to prevent automatic retries, timeout: 5000ms before giving up
    )

    def on_connect():
        print("[Login] Connected! Redirecting to dashboard...")
        window.localStorage.setItem("fleeter_ip", ip)  # store IP for the dashboard
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