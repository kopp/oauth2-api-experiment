from flask import Flask, url_for, request, Response, redirect, jsonify
from urllib.parse import urlencode
from requests import get

from server_using_external_oauth2 import CookieKey

PORT = 7000

API_BASE = "http://lvh.me:6000"
API_LOGIN = "/api/login"

app = Flask(__name__, static_url_path="", static_folder="")
app.config["SERVER_NAME"] = f"lvh.me:{PORT}"


@app.route("/useapi")
def use_api():
    print("this is use_api")
    token = request.cookies.get(CookieKey.token)
    response = get(API_BASE + "/api", cookies={CookieKey.token: token})
    from IPython import embed

    if "content" in response.json():
        return "Response: " + response.json()["content"]
    else:
        return "Response looks strange: " + response.text


def make_api_login_with_redirect_to(route_name):
    params = urlencode({"redirect_url": url_for(route_name, _external=True)})
    url = f"{API_BASE}{API_LOGIN}?{params}"
    return url


@app.route("/index.html")
@app.route("/")
def index():
    return f"""
    <p><a href='{make_api_login_with_redirect_to("use_api")}'>api login</a></p>
    """


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=PORT,
    )
