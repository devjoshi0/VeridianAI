import firebase_admin
from firebase_admin import credentials, firestore
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_firebase_connection():
    """Test Firebase connection and basic operations"""
    print("🧪 Testing Firebase Connection...")
    
    try:
        # Try to initialize Firebase
        service_account_key = os.getenv('FIREBASE_SERVICE_ACCOUNT_KEY')
        if service_account_key:
            import json
            cred_dict = json.loads(service_account_key)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase initialized with environment variable")
        else:
            print("⚠️ No FIREBASE_SERVICE_ACCOUNT_KEY found, trying default credentials...")
            firebase_admin.initialize_app()
            print("✅ Firebase initialized with default credentials")
        
        # Test Firestore connection
        db = firestore.client()
        
        # Try to read from a collection (this will fail if no connection)
        test_ref = db.collection('test').document('connection_test')
        
        # Write a test document
        test_ref.set({
            'test': True,
            'message': 'Firebase connection successful!'
        })
        print("✅ Successfully wrote to Firestore")
        
        # Read the test document
        doc = test_ref.get()
        if doc.exists:
            print("✅ Successfully read from Firestore")
            print(f"   Data: {doc.to_dict()}")
        
        # Clean up test document
        test_ref.delete()
        print("✅ Successfully deleted test document")
        
        print("\n🎉 Firebase connection test PASSED!")
        return True
        
    except Exception as e:
        print(f"❌ Firebase connection test FAILED: {e}")
        print("\n📋 Troubleshooting steps:")
        print("1. Make sure you have FIREBASE_SERVICE_ACCOUNT_KEY in your .env file")
        print("2. Verify your Firebase project is set up correctly")
        print("3. Check that Firestore is enabled in your Firebase project")
        return False

if __name__ == "__main__":
    test_firebase_connection() 