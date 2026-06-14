import asyncio
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, Form, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from src.auth import create_token, decode_token
from src.client_store import (
    authenticate, create_client, get_client,
    get_all_clients, delete_client
)
from src.bot_store import (
    create_bot, get_bot, get_bots_for_client, get_all_bots,
    add_pdf, update_bot, delete_bot, get_bot_by_api_key_and_id
)
from src.generator import generate_answer, clear_memory
from src.ingest import ingest_pdf
from src.vectorstores import (
    init_qdrant, clear_qdrant,
    init_bot_collection, delete_collection
)


# ── Startup ───────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    asyncio.create_task(_init_db())
    yield

async def _init_db():
    try:
        print("Initializing Qdrant database...")
        init_qdrant()
        print("Database initialization complete.")
    except Exception as e:
        print(f"Qdrant init error: {e}")

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ──────────────────────────────────────────
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def root():
    return FileResponse("static/index.html")

@app.get("/admin")
def admin_page():
    return FileResponse("static/admin.html")


# ── JWT dependency ────────────────────────────────────────
bearer = HTTPBearer()

def get_current_client(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    payload = decode_token(creds.credentials)
    if not payload:
        raise JSONResponse({"error": "Invalid or expired token"}, status_code=401)
    client = get_client(payload["sub"])
    if not client:
        raise JSONResponse({"error": "Client not found"}, status_code=401)
    return client

def require_super_admin(client: dict = Depends(get_current_client)) -> dict:
    if not client.get("is_super_admin"):
        raise JSONResponse({"error": "Super admin only"}, status_code=403)
    return client


# ════════════════════════════════════════════════════════
# AUTH ROUTES
# ════════════════════════════════════════════════════════

class LoginRequest(BaseModel):
    email:    str
    password: str

@app.post("/auth/login")
async def login(req: LoginRequest):
    """Login — returns JWT token."""
    client = authenticate(req.email, req.password)
    if not client:
        return JSONResponse({"error": "Invalid email or password"}, status_code=401)

    token = create_token(
        client_id=client["client_id"],
        email=client["email"],
        is_super_admin=client.get("is_super_admin", False)
    )
    return {
        "token":          token,
        "client_id":      client["client_id"],
        "name":           client["name"],
        "email":          client["email"],
        "api_key":        client["api_key"],
        "is_super_admin": client.get("is_super_admin", False),
    }


@app.get("/auth/me")
async def me(client: dict = Depends(get_current_client)):
    """Return current logged-in client info."""
    return {"client": client}


# ════════════════════════════════════════════════════════
# SUPER ADMIN ROUTES — manage clients
# ════════════════════════════════════════════════════════

class CreateClientRequest(BaseModel):
    name:     str
    email:    str
    password: str

@app.post("/superadmin/create-client")
async def superadmin_create_client(
    req:    CreateClientRequest,
    admin:  dict = Depends(require_super_admin)
):
    """Super admin creates a new client account."""
    try:
        client = create_client(req.name, req.email, req.password)
        return {"success": True, "client": client}
    except ValueError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.get("/superadmin/clients")
async def superadmin_list_clients(admin: dict = Depends(require_super_admin)):
    """List all clients."""
    return {"clients": get_all_clients()}


@app.delete("/superadmin/client/{client_id}")
async def superadmin_delete_client(
    client_id: str,
    admin:     dict = Depends(require_super_admin)
):
    """Delete a client account."""
    delete_client(client_id)
    return {"success": True}


@app.get("/superadmin/bots")
async def superadmin_all_bots(admin: dict = Depends(require_super_admin)):
    """Super admin sees ALL bots across all clients."""
    return {"bots": get_all_bots()}


# ════════════════════════════════════════════════════════
# ADMIN ROUTES — bot management (per client)
# ════════════════════════════════════════════════════════

@app.post("/admin/create-bot")
async def admin_create_bot(
    name:            str  = Form(...),
    welcome_message: str  = Form(...),
    primary_color:   str  = Form(default="#0a6e9f"),
    client: dict = Depends(get_current_client)
):
    """Create a new bot for this client."""
    bot = create_bot(
        client_id=client["client_id"],
        client_api_key=client["api_key"],
        name=name,
        welcome_message=welcome_message,
        primary_color=primary_color
    )
    init_bot_collection(bot["bot_id"])
    return {"success": True, "bot": bot}


@app.get("/admin/bots")
async def admin_list_bots(client: dict = Depends(get_current_client)):
    """List only this client's bots."""
    if client.get("is_super_admin"):
        bots = get_all_bots()
    else:
        bots = get_bots_for_client(client["client_id"])
    return {"bots": bots}


@app.get("/admin/bot/{bot_id}")
async def admin_get_bot(bot_id: str, client: dict = Depends(get_current_client)):
    bot = get_bot(bot_id)
    if not bot:
        return JSONResponse({"error": "Bot not found"}, status_code=404)
    if not client.get("is_super_admin") and bot["client_id"] != client["client_id"]:
        return JSONResponse({"error": "Access denied"}, status_code=403)
    return {"bot": bot}


@app.post("/admin/bot/{bot_id}/update")
async def admin_update_bot(
    bot_id:          str,
    name:            str = Form(...),
    welcome_message: str = Form(...),
    primary_color:   str = Form(default="#0a6e9f"),
    client: dict = Depends(get_current_client)
):
    try:
        bot = update_bot(
            bot_id=bot_id,
            client_id=client["client_id"] if not client.get("is_super_admin") else get_bot(bot_id)["client_id"],
            name=name,
            welcome_message=welcome_message,
            primary_color=primary_color
        )
        return {"success": True, "bot": bot}
    except (ValueError, PermissionError) as e:
        return JSONResponse({"error": str(e)}, status_code=403)


@app.post("/admin/bot/{bot_id}/upload-pdf")
async def admin_upload_pdf(
    bot_id: str,
    file:   UploadFile = None,
    client: dict = Depends(get_current_client)
):
    if not file:
        return JSONResponse({"error": "No file uploaded"}, status_code=400)
    if not file.filename.endswith(".pdf"):
        return JSONResponse({"error": "Only PDF files accepted"}, status_code=400)

    bot = get_bot(bot_id)
    if not bot:
        return JSONResponse({"error": "Bot not found"}, status_code=404)
    if not client.get("is_super_admin") and bot["client_id"] != client["client_id"]:
        return JSONResponse({"error": "Access denied"}, status_code=403)

    try:
        await ingest_pdf(file, collection_name=bot["collection_name"])
        add_pdf(bot_id, file.filename)
        return {"success": True, "message": f"{file.filename} processed successfully"}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.delete("/admin/bot/{bot_id}")
async def admin_delete_bot(bot_id: str, client: dict = Depends(get_current_client)):
    bot = get_bot(bot_id)
    if not bot:
        return JSONResponse({"error": "Bot not found"}, status_code=404)
    try:
        delete_collection(bot["collection_name"])
        delete_bot(bot_id, client["client_id"], client.get("is_super_admin", False))
        return {"success": True}
    except PermissionError as e:
        return JSONResponse({"error": str(e)}, status_code=403)


# ════════════════════════════════════════════════════════
# ORIGINAL ROUTES — your existing chat app (unchanged)
# ════════════════════════════════════════════════════════

class QueryRequest(BaseModel):
    query:       str
    session_id:  str  = "default"
    use_general: bool = False
    language:    str  = "English"

@app.post("/ask")
async def ask_question(req: QueryRequest):
    result = generate_answer(
        req.query,
        session_id=req.session_id,
        use_general=req.use_general,
        language=req.language
    )
    return {
        "response":        result["answer"],
        "rewritten_query": result["rewritten_query"],
        "has_pdf_context": result["has_pdf_context"]
    }

@app.post("/upload")
async def upload_file(file: UploadFile = None):
    if not file:
        return {"message": "No file uploaded"}
    if not file.filename.endswith(".pdf"):
        return {"message": "Please upload a PDF file"}
    try:
        await ingest_pdf(file)
        return {"message": "File processed successfully"}
    except Exception as e:
        return {"message": f"Error processing file: {str(e)}"}

@app.post("/clear")
async def clear_chat(session_id: str = "default"):
    clear_memory(session_id)
    return {"message": f"Memory cleared for session {session_id}"}

@app.post("/clear-db")
async def clear_database():
    clear_qdrant()
    return {"message": "Database cleared."}


# ════════════════════════════════════════════════════════
# WIDGET ROUTES — used by embedded widget.js
# ════════════════════════════════════════════════════════

@app.get("/widget/config/{bot_id}")
async def widget_get_config(bot_id: str, api_key: str):
    """
    Widget fetches bot config on load.
    Requires api_key to verify ownership.
    """
    bot = get_bot_by_api_key_and_id(bot_id, api_key)
    if not bot:
        return JSONResponse(
            {"error": "Invalid API key or bot not found"},
            status_code=401
        )
    return {
        "bot_id":          bot["bot_id"],
        "name":            bot["name"],
        "welcome_message": bot["welcome_message"],
        "primary_color":   bot["primary_color"],
    }


class WidgetQueryRequest(BaseModel):
    bot_id:      str
    api_key:     str
    query:       str
    session_id:  str  = "default"
    use_general: bool = False
    language:    str  = "English"

@app.post("/widget/ask")
async def widget_ask(req: WidgetQueryRequest):
    """
    Chat endpoint for embedded widgets.
    Verifies api_key before processing.
    """
    bot = get_bot_by_api_key_and_id(req.bot_id, req.api_key)
    if not bot:
        return JSONResponse(
            {"error": "Invalid API key — please check your embed code"},
            status_code=401
        )

    session_id = f"{req.bot_id}_{req.session_id}"
    result     = generate_answer(
        req.query,
        session_id=session_id,
        use_general=req.use_general,
        language=req.language,
        collection_name=bot["collection_name"]
    )
    return {
        "response":        result["answer"],
        "rewritten_query": result["rewritten_query"],
        "has_pdf_context": result["has_pdf_context"]
    }


@app.post("/widget/clear")
async def widget_clear(bot_id: str, api_key: str, session_id: str = "default"):
    bot = get_bot_by_api_key_and_id(bot_id, api_key)
    if not bot:
        return JSONResponse({"error": "Invalid API key"}, status_code=401)
    clear_memory(f"{bot_id}_{session_id}")
    return {"message": "Session cleared"}