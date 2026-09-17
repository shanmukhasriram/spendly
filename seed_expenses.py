import sqlite3
import random
from datetime import datetime, timedelta
import sys
from database.db import get_db

def seed_expenses(user_id):
    categories = [
        ("Food", 200, 1500),
        ("Transport", 50, 500),
        ("Bills", 500, 5000),
        ("Entertainment", 100, 2000),
        ("Health", 200, 3000),
        ("Shopping", 500, 10000),
        ("Other", 50, 1000)
    ]
    
    descriptions = {
        "Food": ["Lunch at KFC", "Grocery from BigBasket", "Dinner with friends", "Cafe Coffee Day", "Zomato order"],
        "Transport": ["Petrol refill", "Uber ride", "Auto rickshaw", "Metro recharge", "Bus ticket"],
        "Bills": ["Electricity bill", "Internet bill", "Mobile recharge", "Water bill", "Rent"],
        "Entertainment": ["Movie ticket", "Netflix subscription", "Gaming zone", "Book purchase", "Concert ticket"],
        "Health": ["Pharmacy medicines", "Doctor consultation", "Lab test", "Gym membership", "Vitamin supplements"],
        "Shopping": ["New shoes", "T-shirt from Zara", "Kitchen utensils", "Amazon order", "Gift for friend"],
        "Other": ["Gift wrap", "Charity donation", "Parking fee", "Stationery", "Miscellaneous"]
    }

    num_expenses = random.randint(5, 15)
    seeded_count = 0

    with get_db() as conn:
        for _ in range(num_expenses):
            cat_info = random.choice(categories)
            category = cat_info[0]
            amount = round(random.uniform(cat_info[1], cat_info[2]), 2)
            description = random.choice(descriptions[category])
            
            # Generate a random date in the last 30 days
            days_ago = random.randint(0, 30)
            date = (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")
            
            conn.execute(
                "INSERT INTO expenses (user_id, amount, category, description, date) VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, category, description, date)
            )
            seeded_count += 1
        
        conn.commit()
    
    print(f"Successfully seeded {seeded_count} expenses for User ID {user_id}!")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python seed_expenses.py <user_id>")
        sys.exit(1)
    
    try:
        uid = int(sys.argv[1])
        seed_expenses(uid)
    except ValueError:
        print("Error: User ID must be an integer.")
