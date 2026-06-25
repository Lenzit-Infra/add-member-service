from telethon import TelegramClient
from telethon.sessions import StringSession
from sqlalchemy.orm import Session
from app.models.agent import Agent
from app.core.telegram_proxy import get_proxy

# Global state for pending logins (In-memory)
PENDING_LOGIN_CLIENTS = {}

class AuthService:
    async def initiate_login(self, phone: str, api_id: str, api_hash: str):
        client = TelegramClient(StringSession(), api_id, api_hash, proxy=get_proxy())
        await client.connect()
        
        if not await client.is_user_authorized():
            sent = await client.send_code_request(phone)
            PENDING_LOGIN_CLIENTS[phone] = {
                "client": client,
                "phone_code_hash": sent.phone_code_hash,
                "api_id": api_id,
                "api_hash": api_hash
            }
            return sent.phone_code_hash
        return None  # Already authorized

    async def verify_code(self, phone: str, code: str, db: Session):
        context = PENDING_LOGIN_CLIENTS.get(phone)
        if not context:
            raise Exception("Session expired or not found")
        
        client = context["client"]
        await client.sign_in(phone, code, phone_code_hash=context["phone_code_hash"])
        await self._save_session(client, phone, context, db)
        return True

    async def _save_session(self, client, phone, context, db: Session):
        session_str = client.session.save()
        me = await client.get_me()
        
        agent = db.query(Agent).filter(Agent.phone == phone).first()
        if agent:
            agent.session_string = session_str
            agent.is_active = True
        else:
            new_agent = Agent(
                phone=phone,
                api_id=context["api_id"],
                api_hash=context["api_hash"],
                session_string=session_str,
                user_id=me.id,
                is_active=True
            )
            db.add(new_agent)
        db.commit()
        await client.disconnect()
        del PENDING_LOGIN_CLIENTS[phone]