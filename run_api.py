from fastapi import FastAPI, HTTPException, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import uvicorn
import logging
import random
import asyncio

# Telethon Imports
from telethon import TelegramClient, errors
from telethon.sessions import StringSession

# Core Imports
from app.core.database import SessionLocal, get_db, Base, engine
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.settings_repo import SettingsRepository
from app.repositories.group_repo import GroupRepository
from app.models.order import Order, OrderSourceGroup
from app.models.group import Group
from app.models.agent import Agent
from app.models.common import OrderStatus
from app.models import agent, group, member, order, logs, settings

# Initialize DB
Base.metadata.create_all(bind=engine)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Telegram Automation API v3.1", version="3.1")

app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- GLOBAL STATE FOR PENDING LOGINS ---
# This dictionary stores temporary TelegramClient instances waiting for code verification.
# Key: Phone Number, Value: Client Instance
PENDING_LOGIN_CLIENTS = {}

# --- Pydantic Models for Auth ---
class LoginRequest(BaseModel):
    phone: str
    api_id: str
    api_hash: str

class VerifyCodeRequest(BaseModel):
    phone: str
    code: str
    phone_code_hash: str

class VerifyPasswordRequest(BaseModel):
    phone: str
    password: str

# --- HELPERS ---
def generate_unique_order_id(db: Session) -> int:
    while True:
        new_id = random.randint(100000, 999999)
        if not db.query(Order).filter(Order.id == new_id).first():
            return new_id

async def save_agent_session(client: TelegramClient, phone: str, api_id: str, api_hash: str, db: Session):
    """Helper to save the authenticated session to DB."""
    session_str = client.session.save()
    me = await client.get_me()
    
    existing_agent = db.query(Agent).filter(Agent.phone == phone).first()
    
    if existing_agent:
        existing_agent.session_string = session_str
        existing_agent.api_id = api_id
        existing_agent.api_hash = api_hash
        existing_agent.user_id = me.id
        existing_agent.is_active = True
        existing_agent.is_banned = False
    else:
        new_agent = Agent(
            phone=phone,
            api_id=api_id,
            api_hash=api_hash,
            session_string=session_str,
            user_id=me.id,
            is_active=True
        )
        db.add(new_agent)
    
    db.commit()

# --- AUTH ROUTES (NEW) ---

@app.post("/api/v1/auth/request-code")
async def request_code(data: LoginRequest):
    """Step 1: Initialize Client and Request Code from Telegram."""
    try:
        # Create a new client session (Memory based initially)
        client = TelegramClient(StringSession(), data.api_id, data.api_hash)
        await client.connect()
        
        if not await client.is_user_authorized():
            sent = await client.send_code_request(data.phone)
            # Store client in memory for next step
            PENDING_LOGIN_CLIENTS[data.phone] = {
                "client": client,
                "hash": sent.phone_code_hash,
                "api_id": data.api_id,
                "api_hash": data.api_hash
            }
            return {"status": "success", "phone_code_hash": sent.phone_code_hash}
        else:
            return {"status": "error", "message": "This session is already authorized."}
            
    except Exception as e:
        print(f"Auth Error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/auth/verify-code")
async def verify_code(data: VerifyCodeRequest, db: Session = Depends(get_db)):
    """Step 2: Verify the SMS code."""
    context = PENDING_LOGIN_CLIENTS.get(data.phone)
    if not context:
        raise HTTPException(status_code=400, detail="Session expired or not found. Restart login.")
    
    client = context["client"]
    try:
        await client.sign_in(data.phone, data.code, phone_code_hash=data.phone_code_hash)
        
        # If successful, save to DB
        await save_agent_session(client, data.phone, context["api_id"], context["api_hash"], db)
        
        # Cleanup
        await client.disconnect()
        del PENDING_LOGIN_CLIENTS[data.phone]
        
        return {"status": "success", "message": "Agent added successfully!"}

    except errors.SessionPasswordNeededError:
        return {"status": "2fa_required", "message": "Two-Step Verification required."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/v1/auth/verify-password")
async def verify_password(data: VerifyPasswordRequest, db: Session = Depends(get_db)):
    """Step 3 (Optional): Verify 2FA Password."""
    context = PENDING_LOGIN_CLIENTS.get(data.phone)
    if not context:
        raise HTTPException(status_code=400, detail="Session expired.")
    
    client = context["client"]
    try:
        await client.sign_in(password=data.password)
        
        # If successful, save to DB
        await save_agent_session(client, data.phone, context["api_id"], context["api_hash"], db)
        
        # Cleanup
        await client.disconnect()
        del PENDING_LOGIN_CLIENTS[data.phone]
        
        return {"status": "success", "message": "Agent added successfully!"}
    except Exception as e:
        return {"status": "error", "message": f"Password Error: {str(e)}"}


# --- EXISTING DASHBOARD ROUTES ---

@app.get("/api/v1/dashboard/stats")
def get_stats(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return {
        "active_orders": 0,
        "active_agents": 0,
        "total_adds": 0,
        "system_health": "100%"
    }

@app.get("/api/v1/orders")
def get_orders(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_order_details()

@app.post("/api/v1/orders")
async def create_order(data: Dict[str, Any], db: Session = Depends(get_db)):
    # ... (Order creation logic same as previous) ...
    # 1. Generate ID
    order_id = generate_unique_order_id(db)
    target_link = data.get('target_link')
    
    target_group = db.query(Group).filter(Group.invite_link == target_link).first()
    if not target_group:
        target_group = Group(id=random.randint(1000,999999), title="New Target", invite_link=target_link, type="supergroup")
        db.add(target_group)
        db.commit()

    new_order = Order(
        id=order_id,
        target_group_id=target_group.id,
        desired_count=int(data.get('desired_count', 100)),
        status=OrderStatus.PENDING_AGENT
    )
    db.add(new_order)
    
    source_links = data.get('source_links', "").split(',')
    for link in source_links:
        link = link.strip()
        if link:
            s_group = db.query(Group).filter(Group.invite_link == link).first()
            if not s_group:
                s_group = Group(id=random.randint(1000,999999), title="Source Group", invite_link=link, type="supergroup")
                db.add(s_group)
                db.commit()
            
            osg = OrderSourceGroup(order_id=new_order.id, source_group_id=s_group.id)
            db.add(osg)

    db.commit()
    return {"status": "success", "id": order_id}

@app.post("/api/v1/orders/{order_id}/action")
def order_action(order_id: int, action: Dict[str, str], db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    act_type = action.get('type')
    if act_type == 'pause': order.status = OrderStatus.PAUSED
    elif act_type == 'resume': order.status = OrderStatus.IN_PROGRESS
    elif act_type == 'stop': order.status = OrderStatus.CANCELLED
    db.commit()
    return {"status": "success", "new_status": order.status.value}

@app.get("/api/v1/agents")
def get_agents(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_agent_performance_summary()

@app.get("/api/v1/members")
def get_members(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_all_members()

@app.get("/api/v1/groups")
def get_groups(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_all_groups()

@app.get("/api/v1/settings")
def get_settings(db: Session = Depends(get_db)):
    repo = SettingsRepository(db)
    repo.initialize_defaults()
    return {
        "worker_check_interval": repo.get_setting("worker_check_interval"),
        "batch_size": repo.get_setting("batch_size"),
        "sleep_delay_min": repo.get_setting("sleep_delay_min"),
        "sleep_delay_max": repo.get_setting("sleep_delay_max"),
        "daily_limit_per_agent": repo.get_setting("daily_limit_per_agent"),
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4747)