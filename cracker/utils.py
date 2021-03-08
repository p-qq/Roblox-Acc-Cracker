def extract_roblosecurity(response):
    for key, value in response.headers.items():
        if key.lower() == "set-cookie" and value.startswith(".ROBLOSECURITY"):
            return value.split("=")[1].split(";")[0]