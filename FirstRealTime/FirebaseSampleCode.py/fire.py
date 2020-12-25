import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Fetch the service account key JSON file contents
cred = credentials.Certificate('FirstRealTime/FirebaseSampleCode.py/soundy-8d98a-firebase-adminsdk-o03jf-c7fede8ea2.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://soundy-8d98a-default-rtdb.firebaseio.com/'
})

# As an admin, the app has access to read and write all data, regradless of Security Rules
ref = db.reference('x_and_y')
ref.set({
    'sound1': {
        'cords':'0 1',
        'visibility':'true',
        'color':'#db6400'
    },
    'sound2': {
        'cords':'1 0',
        'visibility':'false',
        'color':'#e6b566'
    },
    'sound3': {
        'cords':'0.536 0.844',
        'visibility':'true',
        'color':'#70af85'
    },
    'sound4': {
        'cords':'-1 0',
        'visibility':'false',
        'color':'#ff4646'
    },
})
print(ref.get())
