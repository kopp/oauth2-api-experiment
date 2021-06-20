from flask import Flask, url_for, request, Response, redirect, jsonify
from urllib.parse import urlencode, parse_qs
from requests import post
from string import ascii_lowercase, digits
from random import choices
from collections import namedtuple
from uuid import uuid4

from github_oauth_app_secrets import CLIENT_SECRET, CLIENT_ID

PORT = 6000

app = Flask(__name__, static_url_path="", static_folder="")
app.config["SERVER_NAME"] = f"lvh.me:{PORT}"


class CookieKey:
    token = "authentication-token"
    client_id = "client-id"


# TODO: how to log out?
# Use https://docs.github.com/en/enterprise-server@3.0/rest/reference/apps#delete-an-app-authorization

secret_states_used = set()
# TODO: make a dict with client_id as key and secret(s) as value(s)

api_login_redirect_url: dict[str, str] = {}  # client_id -> redirect_url


def make_secret_state():
    characters = ascii_lowercase + digits
    random_string = "".join(choices(characters, k=20))
    print("Generated random string: ", random_string)
    return random_string


def make_client_id():
    uuid = uuid4()
    return uuid.urn


def make_oauth_authorize_url():
    """
    Make the URL to call for login.
    """
    base = "https://github.com/login/oauth/authorize"
    state = make_secret_state()
    secret_states_used.add(state)
    params = urlencode(
        {
            "client_id": CLIENT_ID,
            "redirect_uri": url_for("callback", _external=True),
            "scope": "read:user",
            "state": state,
        }
    )
    url = "{}?{}".format(base, params)
    print("url: ", url)
    return url


Token = namedtuple("Token", ["token", "scope", "type"])


def post_to_oauth_access_token_url(code):
    """
    Make the URL to exchange a code with an access token.
    """
    base = "https://github.com/login/oauth/access_token"
    print(f"Making POST to {base}.")
    response = post(
        base,
        json={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "redirect_uri": url_for("callback", _external=True),
        },
    )
    print(f"Got response {response}.")
    if response.ok:
        token_values = parse_qs(response.text)
        return Token(token_values["access_token"][0], token_values["scope"][0], token_values["token_type"][0])
    else:
        return None


def check_oauth_token_is_valid(token):
    base = "https://api.github.com"
    api = f"/applications/{CLIENT_ID}/token"
    url = base + api
    response = post(url, auth=(CLIENT_ID, CLIENT_SECRET), json={"access_token": token})
    return response.ok


def is_authenticated():
    token = request.cookies.get(CookieKey.token)
    if token is None:
        return False
    is_valid = check_oauth_token_is_valid(token)
    return is_valid


@app.route("/api")
def api():
    if is_authenticated():
        if request.method == "GET":
            return {"content": "Here you can brose my shiny api."}
        else:
            return f"method {request.method} not implemented"
    else:
        return Response(401)


@app.route("/welcome")
def welcome():
    token = request.cookies.get(CookieKey.token)
    if token is not None:
        is_valid = check_oauth_token_is_valid(token)
        if not is_valid:
            return (
                "You do have a cookie -- but it does not seem to be valid.  <a href='{}'>Re-login</a> please.".format(
                    make_oauth_authorize_url()
                )
            )
        else:
            return "Welcome -- you're authenticated now."
    else:
        return "You are not authenticated :("


@app.route("/callback")
def callback():
    state = request.args.get("state")
    code = request.args.get("code")
    print(f"Callback called with state {state} and code {code}.")
    if not state in secret_states_used:
        print(f"This looks fishy: The state {state} is not the one we sent! {secret_states_used}.")
    else:
        secret_states_used.remove(state)
    token = post_to_oauth_access_token_url(code)
    if token is None:
        return Response(status=500)
    else:
        client_id = request.cookies.get(CookieKey.client_id)
        if client_id is not None and client_id in api_login_redirect_url:
            redirect_response = redirect(api_login_redirect_url[client_id])
        else:
            # logged in without specifying "our" redirect_url
            redirect_response = redirect(url_for("welcome"))
        redirect_response.set_cookie(CookieKey.token, token.token)
        return redirect_response


@app.route("/index.html")
@app.route("/")
def index():
    return f"""
    <p><a href='{make_oauth_authorize_url()}'>website login</a></p>
    """


@app.route("/api/login/status")
def login_status():
    if is_authenticated():
        return {"status": "authenticated"}
    else:
        return {"status": "not authenticated"}


@app.route("/api/login")
def login():
    """
    GET this with a parameter redirect_url.
    If authenticated, it will directly redirect to the given url.
    If not authenticated, redirect to a login page and after successfully
    logging in, redirect to the given url.
    """
    redirect_url = request.args.get("redirect_url")
    if redirect_url is None:
        print("No redirect_url given")
        return Response(status=400)

    if is_authenticated():
        return redirect(redirect_url)

    redirect_response = redirect(make_oauth_authorize_url())

    # if no client id found, add one
    client_id = request.cookies.get(CookieKey.client_id)
    if client_id is None:
        client_id = make_client_id()
        redirect_response.set_cookie(CookieKey.client_id, client_id)

    # store redirect url so that we can redirect there after the login succeeded
    if client_id in api_login_redirect_url and api_login_redirect_url[client_id] != redirect_url:
        return Response(status=400)

    api_login_redirect_url[client_id] = redirect_url

    return redirect_response


if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=PORT,
    )
