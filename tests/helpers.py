"""Small helpers that drive the web app like a user would (no browser needed)."""


def register(client, username="rahim", full_name="Rahim Uddin", password="secret123"):
    return client.post(
        "/register/patient",
        data={"username": username, "password": password, "full_name": full_name},
        follow_redirects=True,
    )


def login(client, username, password, role=None):
    data = {"username": username, "password": password}
    if role:
        data["role"] = role
    return client.post("/login", data=data, follow_redirects=True)


def logout(client):
    client.get("/logout")


def book(client, doctor="Dr. Karim", time="10:00", follow=False):
    return client.post("/book", data={"doctor": doctor, "time": time}, follow_redirects=follow)
