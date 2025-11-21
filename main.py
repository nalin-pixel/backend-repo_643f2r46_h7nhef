import os
from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import (
    User, PublicUser,
    ForumPost, ForumComment,
    GalleryImage,
    Product, Order,
    News, NewsComment,
    LikeAction, CommentAction,
    CreatedResponse,
)

app = FastAPI(title="Manga.de API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Utilities

def oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id")


def with_id(doc):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def root():
    return {"name": "Manga.de API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Connected & Working"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response

# ------------- Auth (simple, demo only) -------------
class RegisterPayload(BaseModel):
    username: str
    email: str
    password: str

class LoginPayload(BaseModel):
    email: str
    password: str

@app.post("/auth/register")
def register(payload: RegisterPayload):
    # naive: store hash as plain for demo; in real app, hash properly
    existing = db["user"].find_one({"email": payload.email})
    if existing:
        raise HTTPException(400, "Email already registered")
    user = User(username=payload.username, email=payload.email, password_hash=payload.password)
    new_id = create_document("user", user)
    return {"id": new_id}

@app.post("/auth/login")
def login(payload: LoginPayload):
    user = db["user"].find_one({"email": payload.email, "password_hash": payload.password})
    if not user:
        raise HTTPException(401, "Invalid credentials")
    return {"id": str(user["_id"]), "username": user["username"], "email": user["email"]}

# ------------- Profiles -------------
@app.get("/users/{user_id}")
def get_profile(user_id: str):
    user = db["user"].find_one({"_id": oid(user_id)})
    if not user:
        raise HTTPException(404, "User not found")
    return {"id": str(user["_id"]), "username": user.get("username"), "bio": user.get("bio", ""), "avatar": user.get("avatar", ""), "theme": user.get("theme", "system")}

@app.put("/users/{user_id}")
def update_profile(user_id: str, data: dict):
    db["user"].update_one({"_id": oid(user_id)}, {"$set": data, "$currentDate": {"updated_at": True}})
    user = db["user"].find_one({"_id": oid(user_id)})
    return with_id(user)

# ------------- Forum -------------
@app.post("/forum")
def create_forum_post(post: ForumPost):
    new_id = create_document("forumpost", post)
    return {"id": new_id}

@app.get("/forum")
def list_forum_posts(limit: int = 20):
    posts = get_documents("forumpost", {}, limit)
    return [with_id(p) for p in posts]

@app.post("/forum/{post_id}/comment")
def comment_forum_post(post_id: str, comment: CommentAction):
    data = ForumComment(user_id=comment.user_id, post_id=post_id, content=comment.content)
    new_id = create_document("forumcomment", data)
    return {"id": new_id}

@app.post("/forum/{post_id}/like")
def like_forum_post(post_id: str, like: LikeAction):
    db["forumpost"].update_one({"_id": oid(post_id)}, {"$inc": {"likes": 1}, "$currentDate": {"updated_at": True}})
    post = db["forumpost"].find_one({"_id": oid(post_id)})
    return with_id(post)

# ------------- News -------------
@app.post("/news")
def create_news(news: News):
    new_id = create_document("news", news)
    return {"id": new_id}

@app.get("/news")
def list_news(limit: int = 20):
    items = get_documents("news", {}, limit)
    return [with_id(n) for n in items]

@app.post("/news/{news_id}/comment")
def comment_news(news_id: str, comment: CommentAction):
    data = NewsComment(user_id=comment.user_id, news_id=news_id, content=comment.content)
    new_id = create_document("newscomment", data)
    return {"id": new_id}

@app.post("/news/{news_id}/like")
def like_news(news_id: str, like: LikeAction):
    db["news"].update_one({"_id": oid(news_id)}, {"$inc": {"likes": 1}, "$currentDate": {"updated_at": True}})
    item = db["news"].find_one({"_id": oid(news_id)})
    return with_id(item)

# ------------- Gallery -------------
@app.post("/gallery")
def upload_image(img: GalleryImage):
    new_id = create_document("galleryimage", img)
    return {"id": new_id}

@app.get("/gallery")
def list_images(limit: int = 30):
    items = get_documents("galleryimage", {}, limit)
    return [with_id(i) for i in items]

@app.post("/gallery/{image_id}/like")
def like_image(image_id: str, like: LikeAction):
    db["galleryimage"].update_one({"_id": oid(image_id)}, {"$inc": {"likes": 1}, "$currentDate": {"updated_at": True}})
    item = db["galleryimage"].find_one({"_id": oid(image_id)})
    return with_id(item)

# ------------- Shop -------------
@app.post("/products")
def create_product(product: Product):
    new_id = create_document("product", product)
    return {"id": new_id}

@app.get("/products")
def list_products(limit: int = 20):
    items = get_documents("product", {}, limit)
    return [with_id(p) for p in items]

@app.post("/orders")
def create_order(order: Order):
    # simple stock check
    total = 0.0
    for item in order.items:
        product = db["product"].find_one({"_id": oid(item["product_id"])})
        if not product:
            raise HTTPException(404, f"Product {item['product_id']} not found")
        if product.get("stock", 0) < item.get("quantity", 1):
            raise HTTPException(400, f"Insufficient stock for {product['title']}")
        total += product.get("price", 0) * item.get("quantity", 1)
    order.total = total
    new_id = create_document("order", order)
    return {"id": new_id, "total": total}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
