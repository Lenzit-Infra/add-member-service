# run_utility.py
import asyncio
from app.repositories.db_utility import clear_all_data, drop_all_tables
# Import models to ensure they are loaded
from app.models import agent, group, member, order, logs 

def display_menu():
    print("\n--- DATABASE UTILITY MENU ---")
    print("1. Clear ALL Data (Delete records, keep tables)")
    print("2. DROP ALL Tables and Recreate Schema (Hard Reset)")
    print("3. Exit")
    choice = input("Enter your choice: ").strip()
    return choice

def main():
    """Main function to run the utility menu."""
    choice = display_menu()
    
    if choice == '1':
        clear_all_data()
    elif choice == '2':
        drop_all_tables()
    elif choice == '3':
        print("Exiting utility.")
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main()