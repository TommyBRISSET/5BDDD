import httpx

BASE_URL = "http://127.0.0.1:8000"

with httpx.Client(base_url=BASE_URL) as client:
    login_response = client.post(
        "/login", data={"username": "alice", "password": "secret"}
    )
    print(f"Status /login : {login_response.status_code}")

    if login_response.status_code != 200:
        print(f"Échec de connexion : {login_response.text}")
        exit(1)

    data = login_response.json()
    token = data.get("access_token")
    print(f"Token récupéré : {token[:20]}...\n")

    headers = {"Authorization": f"Bearer {token}"}
    private_response = client.get("/private", headers=headers)

    print(f"Status /private : {private_response.status_code}")
    print(f"Réponse         : {private_response.json()}")