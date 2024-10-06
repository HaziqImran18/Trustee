import firebase_admin
from firebase_admin import credentials

def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    if not firebase_admin._apps:
        config = {
            'apiKey': 'AIzaSyBFK1kO0AMsop_RqnQueC_52FGTakylYxc',
            'authDomain': 'trustee-80268.firebaseapp.com',
            'projectId': 'trustee-80268',
            'storageBucket': 'trustee-80268.appspot.com',
            'messagingSenderId': '837210156817',
            'appId': '1:837210156817:web:781666ef9d1557968766b0'
        }
        cred = credentials.Certificate('trustee-80268-firebase-adminsdk-5obef-31100bcff7.json')  # Use None for API key authentication
        firebase_admin.initialize_app(cred, options=config)

initialize_firebase()