# app/controllers/order_controller.py
from app.services.order_service import OrderService
from app.core.database import SessionLocal
from telethon import TelegramClient

async def create_order_cli(client: TelegramClient):
    """
    Command Line Interface to create a new order.
    """
    print("\n--- NEW ORDER CREATION ---")
    
    # 1. Get Target Group Input
    target_link = input("Enter TARGET Group Link (Where members will be added): ").strip()
    
    # 2. Get Source Groups Input
    source_links_input = input("Enter SOURCE Group Links (Comma-separated or one per line):\n").strip()
    source_links = [link.strip() for link in source_links_input.replace('\n', ',').split(',') if link.strip()]
    
    if not source_links:
        print("Error: Must provide at least one source group link.")
        return

    # 3. Get Desired Count
    try:
        desired_count = int(input("Enter Desired Member Count for this Order: ").strip())
        if desired_count <= 0: raise ValueError
    except ValueError:
        print("Error: Desired count must be a positive number.")
        return

    # 4. Initialize Service and Execute
    db = SessionLocal()
    order_service = OrderService(db, client)
    
    new_order = await order_service.create_new_order(target_link, source_links, desired_count)
    
    if new_order:
        print(f"\nSUCCESS: Order {new_order.id} is now IN_PROGRESS.")
        print("The background worker can start processing this order.")
    else:
        print("\nFAILURE: Order could not be created. Check logs for validation errors.")