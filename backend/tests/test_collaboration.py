from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from uuid import uuid4
from PIL import Image
from fastapi.testclient import TestClient
from app.main import create_app


class Collaboration(unittest.TestCase):
    def test_shared_trip(self):
        with TemporaryDirectory() as root:
            app=create_app(Path(root))
            with TestClient(app,base_url="https://testserver") as car:
                v="/api/v1"
                t=car.post(v+"/trips",json={"title":"바다"}).json()
                path=v+"/trips/"+t["tripId"]
                car.headers["Authorization"]="Bearer "+t["vehicleToken"]
                people=[TestClient(app,base_url="https://testserver") for _ in range(4)]
                for i,p in enumerate(people):
                    response=p.post(v+"/join",json={"nickname":str(i),"token":t["claimToken" if i==0 else "inviteToken"]})
                    self.assertEqual(response.status_code,200,response.text)
                a,b,*_=people
                self.assertEqual(len(car.get(path).json()["members"]),4)
                self.assertEqual(b.post(v+"/join",json={"nickname":"other","token":t["claimToken"]}).status_code,404)
                buf=BytesIO()
                Image.new("RGB",(4,4)).save(buf,"PNG")
                def send(client,data,key):
                    return client.post(path+"/photos",files={"file":("x.png",data,"image/png")},headers={"Idempotency-Key":key})
                key=str(uuid4())
                photo=send(a,buf.getvalue(),key).json()["photoId"]
                self.assertEqual(send(a,buf.getvalue(),key).json()["photoId"],photo)
                self.assertEqual(send(a,b"oops",str(uuid4())).status_code,422)
                outsider=TestClient(app,base_url="https://testserver")
                self.assertEqual(send(outsider,buf.getvalue(),key).status_code,401)
                other=outsider.post(v+"/trips",json={"title":"다른 여행"}).json()
                outsider.headers["Authorization"]="Bearer "+other["vehicleToken"]
                self.assertEqual(outsider.get(path+"/photos").status_code,401)
                url=path+"/photos/"+photo
                self.assertEqual(car.put(url+"/vote").status_code,403)
                token=car.post(path+"/pair-code").json()["token"]
                self.assertEqual(a.put(path+"/vehicle-session/actor",json={"token":token}).status_code,200)
                with ThreadPoolExecutor(5) as pool:
                    replies=list(pool.map(lambda p:p.put(url+"/vote"),[*people,car]))
                self.assertTrue(all(r.status_code==200 for r in replies))
                self.assertEqual(car.get(path+"/photos").json()["items"][0]["voteCount"],4)
                self.assertEqual(car.delete(url+"/vote").json()["voteCount"],3)
                self.assertEqual(a.get(path+"/photos").json()["items"][0]["myVote"],0)
                selection=dict(orderedPhotoIds=[photo],coverPhotoId=photo,expectedRevision=0)
                self.assertEqual(b.put(path+"/album",json=selection).status_code,403)
                self.assertEqual(car.put(path+"/album",json=selection).status_code,200)
                self.assertEqual(b.get(url+"/download").content,buf.getvalue())
                self.assertEqual(a.put(path+"/album",json=selection).status_code,409)
                for p in people: p.close()
                outsider.close()
            with TestClient(create_app(Path(root)),headers=car.headers) as restored:
                self.assertEqual(restored.get(path+"/album").json()["orderedPhotoIds"],[photo])
