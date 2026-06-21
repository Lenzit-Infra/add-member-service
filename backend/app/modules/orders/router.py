from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.repositories.analytics_repo import AnalyticsRepository
from app.repositories.order_repo import OrderRepository
from app.models.order import Order, OrderStatus, OrderSourceGroup
from .schemas import OrderCreate, OrderAction

router = APIRouter()

@router.get("/")
def get_orders(db: Session = Depends(get_db)):
    repo = AnalyticsRepository(db)
    return repo.get_order_details()

@router.post("/")
async def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):
    # اینجا برای سادگی فعلا کلاینت تلگرام را None رد میکنیم چون سرویس شما قبلا CLI بود
    # در معماری صحیح، OrderService نباید در لحظه ساخت نیاز به کلاینت داشته باشد.
    # باید فقط در دیتابیس ثبت کند و ورکر آن را پردازش کند.
    
    from app.models.order import Order, OrderStatus, OrderSourceGroup
    from app.models.group import Group
    import random

    # Logic Simple شده برای ثبت سفارش در دیتابیس (بدون نیاز به چک کردن لحظه ای تلگرام)
    new_id = random.randint(100000, 999999)
    
    # 1. Save Target (Simplified)
    target_grp = db.query(Group).filter(Group.invite_link == order_data.target_link).first()
    if not target_grp:
        target_grp = Group(id=random.randint(1000,999999), invite_link=order_data.target_link, title="Pending Target")
        db.add(target_grp)
        db.commit()

    order = Order(
        id=new_id,
        target_group_id=target_grp.id,
        desired_count=order_data.desired_count,
        status=OrderStatus.PENDING_AGENT
    )
    db.add(order)
    
    for link in order_data.source_links:
        s_grp = db.query(Group).filter(Group.invite_link == link).first()
        if not s_grp:
            s_grp = Group(id=random.randint(1000,999999), invite_link=link, title="Pending Source")
            db.add(s_grp)
            db.commit()
        db.add(OrderSourceGroup(order_id=order.id, source_group_id=s_grp.id))
    
    db.commit()
    return {"status": "success", "order_id": new_id}

ACTION_TO_STATUS = {
    "pause": OrderStatus.PAUSED,
    "resume": OrderStatus.IN_PROGRESS,
    "cancel": OrderStatus.CANCELLED,
}

@router.post("/{order_id}/action")
def order_action(order_id: int, action: OrderAction, db: Session = Depends(get_db)):
    new_status = ACTION_TO_STATUS.get(action.type)
    if not new_status:
        raise HTTPException(status_code=400, detail=f"Unknown action type: {action.type}")

    repo = OrderRepository(db)
    repo.update_order_status(order_id, new_status)
    return {"status": "success", "order_id": order_id, "new_status": new_status.value}

DELETABLE_STATUSES = {OrderStatus.CANCELLED, OrderStatus.FINISHED}

@router.delete("/{order_id}")
def delete_order(order_id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status not in DELETABLE_STATUSES:
        raise HTTPException(
            status_code=400,
            detail="Cancel the order before deleting it — only cancelled or finished orders can be deleted."
        )

    db.query(OrderSourceGroup).filter(OrderSourceGroup.order_id == order_id).delete()
    db.delete(order)
    db.commit()
    return {"status": "success", "order_id": order_id}