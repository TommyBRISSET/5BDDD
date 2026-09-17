import httpx

BASE_URL = "http://127.0.0.1:8000"


def run_tests():
    with httpx.Client(base_url=BASE_URL) as client:
        print("Connexion Alice")
        login_alice = client.post(
            "/login", data={"username": "alice", "password": "secret"}
        )
        login_alice.raise_for_status()

        token_alice = login_alice.json()["access_token"]
        headers_alice = {"Authorization": f"Bearer {token_alice}"}

        private_alice = client.get("/private", headers=headers_alice)
        private_alice.raise_for_status()
        print(f"Alice /private : {private_alice.json()}")

        new_item = {"name": "Clavier Gamer", "price": 89.99, "is_offer": True}
        create_res = client.post("/items/", json=new_item, headers=headers_alice)
        create_res.raise_for_status()
        print(f"Alice création item : {create_res.json()}")

        print("\nConnexion Bob")
        login_bob = client.post(
            "/login", data={"username": "bob", "password": "secret"}
        )
        login_bob.raise_for_status()

        token_bob = login_bob.json()["access_token"]
        headers_bob = {"Authorization": f"Bearer {token_bob}"}

        private_bob = client.get("/private", headers=headers_bob)
        private_bob.raise_for_status()
        print(f"Bob /private : {private_bob.json()}")

        items_res = client.get("/items/", headers=headers_bob)
        items_res.raise_for_status()
        print(f"Bob liste items : {len(items_res.json())} item(s) récupéré(s)")

        print("Bob tente de créer un item...")
        try:
            interdit_res = client.post(
                "/items/",
                json={"name": "Objet interdit", "price": 10.0, "is_offer": False},
                headers=headers_bob,
            )
            interdit_res.raise_for_status()
            print("Erreur : Bob a pu créer un item")
        except httpx.HTTPStatusError as exc:
            print(f"Bloqué par l'API comme prévu ({exc.response.status_code}) : {exc.response.json()['detail']}")


if __name__ == "__main__":
    run_tests()