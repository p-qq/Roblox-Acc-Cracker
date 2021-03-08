import requests

print("Click 'New registration' at https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps/ApplicationsListBlade")
print("Use the following settings:")
print("- Name: any")
print("- Who can use this application or access this API?: Personal Microsoft accounts only")
print("- Redirect URI: http://localhost/")
print("Click 'Register'.\n")

print("Copy the 'Application (client) ID' and paste it below")
client_id = input("Client/Application ID: ").strip()

print("\nOn the left side of the page click 'Certificates & secrets', then 'New client secret'")
print("Copy the Value field and paste it below:")
client_secret = input("Client secret: ").strip()
client_url = f"https://login.live.com/oauth20_authorize.srf?client_id={client_id}&response_type=code&redirect_uri=http://localhost/&scope=XboxLive.signin%20XboxLive.offline_access"

print("\nGo to the following url and click 'Yes':")
print(client_url)

print("\nYou should now be on 'This site can’t be reached', just copy the link of the page and paste it below:")
code = input("URL: ").strip().split("code=")[-1].split("&")[0]

print("\n\n")

session = requests.Session()


access_token = session.post(
    url="https://login.live.com/oauth20_token.srf",
    data={
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": "http://localhost/"
    }
).json()["access_token"]

xbl_auth = session.post(
    url="https://user.auth.xboxlive.com/user/authenticate",
    headers={"Accept": "application/json"},
    json={
       "RelyingParty": "http://auth.xboxlive.com",
        "TokenType": "JWT",
        "Properties": {
            "AuthMethod": "RPS",
            "SiteName": "user.auth.xboxlive.com",
            "RpsTicket": "d=" + access_token,
        }
    }
).json()

roblox_auth = session.post(
    url="https://xsts.auth.xboxlive.com/xsts/authorize",
    headers={"Accept": "application/json"},
    json={
        "Properties": {
            "SandboxId": "RETAIL",
            "UserTokens": [
                xbl_auth["Token"]
            ]
        },
        "RelyingParty": "https://api.roblox.com/",
        "TokenType": "JWT"
    }
).json()

token = "XBL3.0 x=%s;%s" % (
    roblox_auth["DisplayClaims"]["xui"][0]["uhs"],
    roblox_auth["Token"]
)

with open("token.txt", "w") as fp:
    fp.write(token)

print(token)
print("Token obtained and saved!")