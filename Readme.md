# How to use GitHub's Oauth2 to allow only authenticated access to your API


## Demo

The server

    python server_using_external_oauth2.py

simulates an API (call `/api`) that requires authentication using GitHub's Oauth2 at a Oauth2 App.
In order to run it, you will need to create one and supply its id and a client secret via

    CLIENT_ID = "abc123..."
    CLIENT_SECRET = "xyz987..."

in file `github_oauth_app_secrets.py`.
To just test the server, visit its `/` in a browser -- it should ask you to login and afterwards you can access `/api`.

The client

    github_oauth_app_secrets.py

simulates a single-page app running on a different web server.
Follow the flow of redirects when visiting its `/` in a browser and clicking the login link.


## What I would like to have

When a user wants to use my API, they have to authenticate using GitHub's Oauth2 mechanism.
The API (server) can then only allow "selected" GitHub users to use the API.
Users/clients of the API should be able to use the API from whatever webserver/locally running single-page app/...


## Issues with just re-directing the user to GitHub's Oauth:

In my first naive attempt, I asked the users to login by providing the link to
[GitHub's authorize page](https://github.com/login/oauth/authorize).
Unfortunately, once the user has authorized there, they are re-directed to the Web-Server running my API.
This is because when you register the Oauth App on Github, you need to set a `redirect_url`.
Later, after the login at GitHub the redirect has to happen to this `redirect_url` or a subdirectory of that url
(see [the documentation](https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps#redirect-urls)).

If my client is a single-page app, I want them to provide a "login" button, which takes the user to log in at GitHub and then re-direct to the single-page app.
This is not possible, unless the single-page app is running in a subdirectory of the `redirect_url` -- and since I cannot know all URLs of single-page apps using the API, this is not feasible.


## The solution

Provide a route `/api/login` which clients can use.
They need to provide a `redirect_url`.
Upon `GET`ing `/api/login?redirect_url=<single-page-app>/subpage` they get re-directed to the GitHub login and once that completes, they are re-directed to the `<single-page-app>/subpage` they initially provided.
Since this re-direct is controlled by the API server, the restrictions of GitHub's Oauth2 server do not apply and thus we can re-direct wherever we want.
During the re-direct, the necessary cookies are set that allow for other uses of the API.



# Setting up an Oauth2 App on GitHub

See [the documentation](https://docs.github.com/en/developers/apps/building-oauth-apps/authorizing-oauth-apps)

- create oauth app in [github settings](https://github.com/settings/applications/new)
    - callback url: the user will get redirected to here (or a subdirectory of it if `redirect_uri` is specified); for local testing use url lvh.me, which is an "alias" for localhost
    - App is `test-oauth` with client id `8c1fb860abc247220ed7`, homepage url `http://lvh.me:6000`, callback url `http://lvh.me:6000/callback`

Note: Test this in a private browsing session, otherwise you're probably signed in in github already and you don't see the login page.

using the webserver in private browsing and enabling the webapp yielded a redirect to

    /callback?code=14996a46fbfd0d89af80&state=asdflkjxvoivaerxdf

Next step is to get an access token.

- You'll need to configure a client secret in the github settings.

Make a request to

    https://github.com/login/oauth/access_token


and you'll receive a token.

You can set this token to a cookie, then the client will send it with every request.

You can check this token using
[GitHub's API](https://docs.github.com/en/enterprise-server@3.0/rest/reference/apps#check-a-token)).