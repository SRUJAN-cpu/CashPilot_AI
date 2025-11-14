"""
Chat Routes
Handles conversations and messages with AI agents
"""

from fastapi import APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from supabase import Client
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
import uuid

from config.supabase_config import get_supabase_client, get_supabase_admin_client
from api.middleware.auth import get_current_user
from api.services.chat_service import get_chat_service
from fastapi import Request

logger = logging.getLogger(__name__)
router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ConversationCreate(BaseModel):
    """Create new conversation"""
    title: Optional[str] = "New Conversation"


class ConversationUpdate(BaseModel):
    """Update conversation"""
    title: str


class MessageCreate(BaseModel):
    """Create new message"""
    content: str = Field(..., min_length=1)
    role: str = Field(default="user", pattern="^(user|assistant|system)$")


class MessageResponse(BaseModel):
    """Message response"""
    id: str
    conversation_id: str
    role: str
    content: str
    timestamp: str
    agent_type: Optional[str]
    metadata: Optional[Dict[str, Any]]


class ConversationResponse(BaseModel):
    """Conversation response"""
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: Optional[int] = 0


# ============================================================================
# Conversation Endpoints
# ============================================================================

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    request: ConversationCreate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    admin_supabase: Client = Depends(get_supabase_admin_client)
):
    """
    Create a new conversation

    - **title**: Optional conversation title (defaults to "New Conversation")
    """
    try:
        # Ensure user exists in public.users table (fix for missing profiles)
        logger.info(f"Checking user profile for: {user['email']}")
        try:
            # Use admin client to check and create user (bypasses RLS)
            user_check = admin_supabase.table("users").select("id").eq("id", user["id"]).execute()
            logger.info(f"User check result: {len(user_check.data) if user_check.data else 0} rows found")

            if not user_check.data:
                # Create missing user profile using admin client
                # Extract name from user_metadata
                user_metadata = user.get("user_metadata", {})
                name = user_metadata.get("name") if user_metadata else None

                user_profile = {
                    "id": user["id"],
                    "email": user["email"],
                    "name": name,
                }
                logger.info(f"Creating user profile with admin client: {user_profile}")
                insert_result = admin_supabase.table("users").insert(user_profile).execute()
                logger.info(f"✓ Created missing user profile: {user['email']} - Result: {insert_result.data}")
            else:
                logger.info(f"User profile already exists for: {user['email']}")
        except Exception as profile_error:
            logger.error(f"❌ Failed to verify/create user profile: {profile_error}")
            logger.error(f"User data structure: {user}")
            # Re-raise the error so we can see it
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Profile creation failed: {str(profile_error)}"
            )

        conversation_data = {
            "user_id": user["id"],
            "title": request.title or "New Conversation",
        }

        response = supabase.table("conversations").insert(conversation_data).execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create conversation"
            )

        logger.info(f"Conversation created: {response.data[0]['id']} by {user['email']}")

        result = response.data[0]
        result["message_count"] = 0
        return result

    except Exception as e:
        logger.error(f"Create conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create conversation: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    limit: int = 50,
    offset: int = 0
):
    """
    List all conversations for current user

    - **limit**: Maximum number of conversations to return (default: 50)
    - **offset**: Number of conversations to skip (default: 0)
    """
    try:
        response = supabase.table("conversations")\
            .select("*, messages(count)")\
            .eq("user_id", user["id"])\
            .order("updated_at", desc=True)\
            .limit(limit)\
            .offset(offset)\
            .execute()

        conversations = []
        for conv in response.data:
            conv_data = {**conv}
            # Count messages
            conv_data["message_count"] = len(conv.get("messages", []))
            conversations.append(conv_data)

        return conversations

    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversations"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Get a specific conversation by ID
    """
    try:
        response = supabase.table("conversations")\
            .select("*, messages(count)")\
            .eq("id", conversation_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        conv_data = {**response.data}
        conv_data["message_count"] = len(response.data.get("messages", []))
        return conv_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch conversation"
        )


@router.put("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    updates: ConversationUpdate,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Update conversation title
    """
    try:
        response = supabase.table("conversations")\
            .update({"title": updates.title})\
            .eq("id", conversation_id)\
            .eq("user_id", user["id"])\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        logger.info(f"Conversation updated: {conversation_id}")
        result = response.data[0]
        result["message_count"] = 0
        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Delete a conversation (also deletes all messages)
    """
    try:
        response = supabase.table("conversations")\
            .delete()\
            .eq("id", conversation_id)\
            .eq("user_id", user["id"])\
            .execute()

        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        logger.info(f"Conversation deleted: {conversation_id}")
        return {"message": "Conversation deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )


# ============================================================================
# Message Endpoints
# ============================================================================

@router.get("/conversations/{conversation_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client),
    limit: int = 100,
    offset: int = 0
):
    """
    Get all messages in a conversation

    - **limit**: Maximum number of messages to return (default: 100)
    - **offset**: Number of messages to skip (default: 0)
    """
    try:
        # Verify user owns the conversation
        conv_response = supabase.table("conversations")\
            .select("id")\
            .eq("id", conversation_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()

        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Fetch messages
        messages_response = supabase.table("messages")\
            .select("*")\
            .eq("conversation_id", conversation_id)\
            .order("timestamp", desc=False)\
            .limit(limit)\
            .offset(offset)\
            .execute()

        return messages_response.data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch messages"
        )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: str,
    message: MessageCreate,
    request: Request,
    user: dict = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_client)
):
    """
    Send a message in a conversation

    This will:
    1. Save the user's message
    2. Process it with NLP layer
    3. Route to appropriate AI agent
    4. Return agent's response
    """
    try:
        # Verify user owns the conversation
        conv_response = supabase.table("conversations")\
            .select("id")\
            .eq("id", conversation_id)\
            .eq("user_id", user["id"])\
            .single()\
            .execute()

        if not conv_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Save user message
        user_message_data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": message.content,
        }

        user_msg_response = supabase.table("messages").insert(user_message_data).execute()

        if not user_msg_response.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save message"
            )

        # Process with NLP and agents
        chat_service = get_chat_service()
        assistant_response = await chat_service.process_user_message(
            user_message=message.content,
            conversation_id=conversation_id,
            supabase=supabase,
            app_state=request.app.state
        )

        # Save assistant's response
        assistant_message_data = {
            "conversation_id": conversation_id,
            "role": "assistant",
            "content": assistant_response,
        }

        assistant_msg_response = supabase.table("messages").insert(assistant_message_data).execute()

        # Update conversation updated_at
        supabase.table("conversations")\
            .update({"updated_at": datetime.utcnow().isoformat()})\
            .eq("id", conversation_id)\
            .execute()

        logger.info(f"Message processed in conversation {conversation_id}")

        # Return assistant's message
        return assistant_msg_response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Send message error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send message: {str(e)}"
        )


# ============================================================================
# WebSocket for Real-time Chat
# ============================================================================

class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, conversation_id: str):
        await websocket.accept()
        if conversation_id not in self.active_connections:
            self.active_connections[conversation_id] = []
        self.active_connections[conversation_id].append(websocket)
        logger.info(f"WebSocket connected to conversation: {conversation_id}")

    def disconnect(self, websocket: WebSocket, conversation_id: str):
        if conversation_id in self.active_connections:
            self.active_connections[conversation_id].remove(websocket)
            if not self.active_connections[conversation_id]:
                del self.active_connections[conversation_id]
        logger.info(f"WebSocket disconnected from conversation: {conversation_id}")

    async def broadcast(self, message: dict, conversation_id: str):
        if conversation_id in self.active_connections:
            for connection in self.active_connections[conversation_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}")


manager = ConnectionManager()


@router.websocket("/ws/conversations/{conversation_id}")
async def websocket_endpoint(
    websocket: WebSocket,
    conversation_id: str,
    token: str  # Pass token as query parameter: ?token=xxx
):
    """
    WebSocket endpoint for real-time chat updates

    Usage:
        ws = new WebSocket("ws://localhost:8000/chat/ws/conversations/{id}?token={jwt}")
    """
    try:
        # Verify token (simplified - in production, decode JWT properly)
        # For now, just connect
        await manager.connect(websocket, conversation_id)

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                message_data = json.loads(data)

                # Broadcast to all connected clients in this conversation
                await manager.broadcast({
                    "type": "new_message",
                    "data": message_data
                }, conversation_id)

        except WebSocketDisconnect:
            manager.disconnect(websocket, conversation_id)

    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.close()
        except:
            pass
