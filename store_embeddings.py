"""
Demo Script: Register Users and Save Face Embeddings to MongoDB
This script demonstrates how to enroll users and store their face embeddings
"""

import cv2
import numpy as np
from security_system import IntelligentSecuritySystem
import os

def create_sample_users():
    """
    Create sample users and register them in the system
    This demonstrates how face embeddings are saved to MongoDB
    """
    print("\n" + "="*80)
    print(" USER REGISTRATION & FACE EMBEDDING STORAGE DEMO")
    print("="*80 + "\n")
    
    # Initialize the security system
    system = IntelligentSecuritySystem()
    
    print("\n--- Registration Methods ---\n")
    print("You can register users in 3 ways:")
    print("1. From webcam capture")
    print("2. From image file")
    print("3. From synthetic/test image\n")
    
    # Method 1: Register from webcam
    print("\n" + "="*80)
    print("METHOD 1: REGISTER USER FROM WEBCAM")
    print("="*80)
    
    choice = input("\nDo you want to register a user from webcam? (y/n): ").strip().lower()
    
    if choice == 'y':
        register_from_webcam(system)
    
    # Method 2: Register from image file
    print("\n" + "="*80)
    print("METHOD 2: REGISTER USER FROM IMAGE FILE")
    print("="*80)
    
    choice = input("\nDo you want to register a user from an image file? (y/n): ").strip().lower()
    
    if choice == 'y':
        register_from_image_file(system)
    
    # Method 3: Create sample test users with synthetic data
    print("\n" + "="*80)
    print("METHOD 3: CREATE SAMPLE TEST USERS")
    print("="*80)
    
    choice = input("\nDo you want to create sample test users? (y/n): ").strip().lower()
    
    if choice == 'y':
        create_test_users(system)
    
    # Display system status
    print("\n" + "="*80)
    print(" SYSTEM STATUS AFTER REGISTRATION")
    print("="*80)
    status = system.get_system_status()
    print(f"\nRegistered Users: {status['registered_users']}")
    print(f"Database Statistics:")
    for key, value in status['database'].items():
        print(f"  {key}: {value}")
    
    # Show what's stored in MongoDB
    print("\n" + "="*80)
    print(" MONGODB STORAGE DETAILS")
    print("="*80)
    show_mongodb_storage(system)
    
    system.cleanup()

def register_from_webcam(system):
    """Register a user by capturing their face from webcam"""
    print("\nOpening webcam...")
    print("Instructions:")
    print("  - Look at the camera")
    print("  - Press SPACE to capture")
    print("  - Press ESC to cancel")
    
    cap = cv2.VideoCapture(0)
    
    if not cap.isOpened():
        print("✗ Could not open webcam")
        return
    
    captured_frame = None
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Display frame
        display_frame = frame.copy()
        cv2.putText(display_frame, "Press SPACE to capture, ESC to cancel", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow('Webcam - Face Registration', display_frame)
        
        key = cv2.waitKey(1) & 0xFF
        
        if key == 27:  # ESC
            print("Registration cancelled")
            break
        elif key == 32:  # SPACE
            captured_frame = frame.copy()
            print("✓ Frame captured!")
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    if captured_frame is not None:
        # Get user details
        print("\n--- Enter User Details ---")
        user_id = input("User ID: ").strip()
        name = input("Full Name: ").strip()
        email = input("Email: ").strip()
        print("\nAvailable roles: guest, resident, admin, security")
        role = input("Role: ").strip()
        
        # Register user
        success = system.register_user(user_id, name, email, role, captured_frame)
        
        if success:
            print(f"\n✓ User {name} registered successfully!")
            print(f"  Face embedding saved to MongoDB")
            print(f"  User ID: {user_id}")
            print(f"  Role: {role}")

def register_from_image_file(system):
    """Register a user from an image file"""
    image_path = input("\nEnter path to image file: ").strip()
    
    if not os.path.exists(image_path):
        print(f"✗ File not found: {image_path}")
        return
    
    # Load image
    image = cv2.imread(image_path)
    
    if image is None:
        print("✗ Could not load image")
        return
    
    print(f"✓ Image loaded: {image.shape}")
    
    # Get user details
    print("\n--- Enter User Details ---")
    user_id = input("User ID: ").strip()
    name = input("Full Name: ").strip()
    email = input("Email: ").strip()
    print("\nAvailable roles: guest, resident, admin, security")
    role = input("Role: ").strip()
    
    # Register user
    success = system.register_user(user_id, name, email, role, image)
    
    if success:
        print(f"\n✓ User {name} registered successfully!")
        print(f"  Face embedding saved to MongoDB")
        print(f"  User ID: {user_id}")
        print(f"  Role: {role}")

def create_test_users(system):
    """Create test users with sample data"""
    print("\nNote: This uses sample face images for testing")
    print("In production, you would use real face photos\n")
    
    # Create sample users
    test_users = [
        {
            'user_id': 'user001',
            'name': 'John Doe',
            'email': 'john.doe@example.com',
            'role': 'admin'
        },
        {
            'user_id': 'user002',
            'name': 'Jane Smith',
            'email': 'jane.smith@example.com',
            'role': 'resident'
        },
        {
            'user_id': 'user003',
            'name': 'Bob Johnson',
            'email': 'bob.johnson@example.com',
            'role': 'guest'
        }
    ]
    
    # Try to load sample images or create synthetic ones
    for user in test_users:
        print(f"\nRegistering {user['name']}...")
        
        # Try to find a sample image in test_data folder
        possible_paths = [
            f"test_data/{user['user_id']}.jpg",
            f"test_data/{user['user_id']}.png",
            f"test_data/sample_face.jpg"
        ]
        
        image = None
        for path in possible_paths:
            if os.path.exists(path):
                image = cv2.imread(path)
                if image is not None:
                    print(f"  Using image: {path}")
                    break
        
        if image is None:
            print(f"  No sample image found. Skipping {user['name']}")
            print(f"  To register this user, place their face photo in test_data/")
            continue
        
        success = system.register_user(
            user['user_id'],
            user['name'],
            user['email'],
            user['role'],
            image
        )

def show_mongodb_storage(system):
    """Show what's stored in MongoDB"""
    print("\nWhat gets stored in MongoDB when you register a user:\n")
    
    # Show users collection
    users = system.db.get_all_users()
    if users:
        print(f"1. USERS COLLECTION ({len(users)} users):")
        print("-" * 60)
        for user in users:
            print(f"   User ID: {user['user_id']}")
            print(f"   Name: {user['name']}")
            print(f"   Email: {user['email']}")
            print(f"   Role: {user['role']}")
            print(f"   Created: {user.get('created_at', 'N/A')}")
            print()
    else:
        print("1. USERS COLLECTION: Empty")
    
    # Show embeddings collection
    embeddings = system.db.get_embeddings()
    if embeddings:
        print(f"\n2. EMBEDDINGS COLLECTION ({len(embeddings)} embeddings):")
        print("-" * 60)
        for emb in embeddings:
            print(f"   User ID: {emb['user_id']}")
            print(f"   Embedding Shape: {emb['embedding'].shape}")
            print(f"   Embedding Type: 128-dimensional vector")
            print(f"   Sample values: {emb['embedding'][:5]}...")
            print(f"   Created: {emb.get('created_at', 'N/A')}")
            print()
    else:
        print("\n2. EMBEDDINGS COLLECTION: Empty")
    
    # Show structure
    print("\n3. MONGODB DOCUMENT STRUCTURE:")
    print("-" * 60)
    print("""
    Users Collection:
    {
        "_id": ObjectId("..."),
        "user_id": "user001",
        "name": "John Doe",
        "email": "john.doe@example.com",
        "role": "admin",
        "status": "active",
        "created_at": ISODate("2024-..."),
        "updated_at": ISODate("2024-...")
    }
    
    Embeddings Collection:
    {
        "_id": ObjectId("..."),
        "user_id": "user001",
        "embedding": [0.123, -0.456, 0.789, ...],  // 128 float values
        "metadata": {},
        "created_at": ISODate("2024-...")
    }
    
    The embedding is a 128-dimensional face feature vector extracted
    using the DeepFace (Facenet) model. This vector uniquely
    represents the person's facial features and is used for
    matching during recognition.
    """)

def direct_api_example():
    """
    Show how to directly use the database API to save embeddings
    """
    print("\n" + "="*80)
    print(" DIRECT DATABASE API EXAMPLE")
    print("="*80 + "\n")
    
    from database.mongodb_handler import SecurityDatabase
    
    # Initialize database
    db = SecurityDatabase()
    
    print("Example: Manually storing a face embedding\n")
    
    # Create a sample embedding (in reality, this comes from face_recognition)
    sample_embedding = np.random.rand(128)  # 128-dimensional vector
    
    print("1. Create embedding vector:")
    print(f"   Shape: {sample_embedding.shape}")
    print(f"   Type: {type(sample_embedding)}")
    print(f"   Sample: {sample_embedding[:5]}...\n")
    
    print("2. Store in MongoDB:")
    print("   db.store_embedding(user_id, embedding_vector, metadata)")
    
    success = db.store_embedding(
        user_id="demo_user",
        embedding=sample_embedding,
        metadata={'source': 'demo', 'quality': 'high'}
    )
    
    if success:
        print("   ✓ Embedding stored successfully!\n")
    
    print("3. Retrieve from MongoDB:")
    print("   embeddings = db.get_embeddings(user_id='demo_user')")
    
    retrieved = db.get_embeddings(user_id="demo_user")
    if retrieved:
        print(f"   ✓ Retrieved {len(retrieved)} embedding(s)")
        print(f"   Embedding shape: {retrieved[0]['embedding'].shape}")
    
    # Cleanup demo data
    db.db.embeddings.delete_many({"user_id": "demo_user"})
    
    db.close()

if __name__ == "__main__":
    print("\n" + "="*80)
    print(" FACE EMBEDDING REGISTRATION & MONGODB STORAGE")
    print("="*80)
    print("\nThis demo shows you how to:")
    print("1. Register users in the system")
    print("2. Capture and process their face images")
    print("3. Extract face embeddings (128-d vectors)")
    print("4. Store embeddings in MongoDB")
    print("5. Retrieve embeddings for recognition")
    
    try:
        create_sample_users()
        
        print("\n\n" + "="*80)
        print(" ADDITIONAL: DIRECT API USAGE")
        print("="*80)
        
        choice = input("\nWant to see direct database API example? (y/n): ").strip().lower()
        if choice == 'y':
            direct_api_example()
        
    except KeyboardInterrupt:
        print("\n\nDemo interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*80)
    print(" DEMO COMPLETE")
    print("="*80)
    print("\nYour face embeddings are now stored in MongoDB!")
    print("They can be used for face recognition in the security system.\n")