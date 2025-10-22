import requests
import time
import random

# The "front door" of our server
BASE_URL = "http://localhost"

def simulate_user_actions(user_id):
    """Simulates one user browsing."""
    try:
        # 1. User browses categories, diets, and cuisines
        print(f"User {user_id}: GET /categories")
        requests.get(f"{BASE_URL}/categories") #
        time.sleep(0.1)

        print(f"User {user_id}: GET /diets")
        requests.get(f"{BASE_URL}/diets") #
        time.sleep(0.1)

        print(f"User {user_id}: GET /cuisines")
        requests.get(f"{BASE_URL}/cuisines") #
        time.sleep(0.1)

        # 2. User searches for a recipe
        search_term = random.choice(["chicken", "fish", "pasta", "sweet", "grill"])
        print(f"User {user_id}: GET /recipe?search_query={search_term}")
        requests.get(f"{BASE_URL}/recipe?search_query={search_term}") #
        time.sleep(0.1)

        # 3. User uses the chatbot
        chat_query = random.choice(["hello", "seasonal", "how to make soup"])
        print(f"User {user_id}: POST /chatbot/query")
        requests.post(f"{BASE_URL}/chatbot/query", json={"query": chat_query}) #
        time.sleep(0.1)

    except Exception as e:
        print(f"User {user_id}: Error during browsing: {e}")

def simulate_authentication(user_id):
    """Simulates one user signing up and getting an OTP."""
    try:
        # 1. User signs up with a new, random phone number and username
        phone_num = f"+919{random.randint(100000000, 999999999)}"
        user_name = f"user_{user_id}"
        signup_data = {
            "user_name": user_name,
            "phone_number": phone_num,
            "email": f"{user_name}@example.com",
            "full_name": f"Test User {user_id}"
        }
        print(f"User {user_id}: POST /signUp")
        requests.post(f"{BASE_URL}/signUp", json=signup_data) #
        time.sleep(0.1)

        # 2. User immediately requests an OTP
        print(f"User {user_id}: POST /send-login-otp")
        requests.post(f"{BASE_URL}/send-login-otp", json={"phone_number": phone_num}) #
        time.sleep(0.1)

    except Exception as e:
        print(f"User {user_id}: Error during auth: {e}")

def generate_all_traffic(num_users=50):
    print(f"--- Starting Benign Traffic Generation for {num_users} Users ---")

    for i in range(num_users):
        print(f"\n--- Simulating User {i+1} ---")

        try:
            # Simulate a mix of traffic.
            # Every user will browse.
            simulate_user_actions(i+1)

            # Some users will also sign up (e.g., 1 in 3)
            if i % 3 == 0:
                simulate_authentication(i+1)

        except requests.exceptions.ConnectionError:
            print(f"\n[ERROR] Connection failed. Is Nginx running?")
            print("Make sure your 'my-waf-server' container is running.")
            print("Run: docker start my-waf-server")
            return # Stop the script

    print("\n--- Benign Traffic Generation Complete ---")


if __name__ == "__main__":
    # Let's simulate 50 users.
    # This will create (50 * 5) + (approx 16 * 2) = ~282 log entries
    generate_all_traffic(num_users=50)