import time
import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

cred = credentials.Certificate("fire.json")

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})
#Update class x times
freq=5

#class, duration
li = [
    [1.5, 'baby uwu', 'crying_baby','sheep', 'crying_baby'],
]

def run(li, freq):   
    t1  = time.time()
    refs = [
        db.reference("Sound").child("sound1").child("classification"),
        db.reference("Sound").child("sound2").child("classification"),
        db.reference("Sound").child("sound3").child("classification"),
        db.reference("Sound").child("sound4").child("classification")
    ]

    for i in li:
        t = i[0]
        v = i[1:]
        while(time.time()-t1 < t):
            for a in range(len(v)):
                refs[a].set(v[a])
                print(v[a])
                if(time.time()-t1 < t): a = len(v)

        # for j in range(freq):
        #     for a in range(len(v)):
        #         refs[a].set(v[a])
        #         print(v[a])
        #     time.sleep(t/freq)

    print(time.time()-t1)

run(li, freq)