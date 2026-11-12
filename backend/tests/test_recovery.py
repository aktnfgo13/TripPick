import unittest
from tempfile import TemporaryDirectory
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import create_app

class RecoveryTest(unittest.TestCase):
    def test_rotation_limit_and_disabled(self):
        with TemporaryDirectory() as root:
            app=create_app(Path(root))
            with TestClient(app,base_url="https://testserver") as owner, TestClient(app,base_url="https://testserver") as guest:
                trip=owner.post("/api/v1/trips",json={"title":"기차"}).json()
                base="/api/v1/trips/"+trip["tripId"]
                for c,key in [(owner,"claimToken"),(guest,"inviteToken")]:
                    c.post("/api/v1/join",json={"token":trip[key],"nickname":"name"})
                self.assertEqual(guest.post(base+"/recovery/issue").status_code,403)
                code=owner.post(base+"/recovery/issue").json()["code"]
                for _ in range(5):
                    self.assertEqual(guest.post(base+"/recovery",json={"code":"bad"}).status_code,403)
                self.assertEqual(guest.post(base+"/recovery",json={"code":code}).status_code,429)
                code=owner.post(base+"/recovery/issue").json()["code"]
                self.assertEqual(guest.post(base+"/recovery",json={"code":code}).status_code,200)
                self.assertEqual(guest.get(base).json()["role"],"owner")
                self.assertEqual(owner.get(base).status_code,401)
                self.assertEqual(guest.post(base+"/recovery",json={"code":code}).status_code,403)
                app.state.recovery_enabled=False
                self.assertEqual(guest.post(base+"/recovery/issue").status_code,404)
                self.assertEqual(guest.get(base).status_code,200)
