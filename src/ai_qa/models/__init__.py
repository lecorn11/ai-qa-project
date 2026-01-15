# src/ai_qa/models/__init__.py
from .common import SuccessResponse, ErrorResponse
from .auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from .chat import SendMessageRequest, MessageResponse, ConversationResponse, ConversationListResponse
from .knowledge import (
    CreateKnowledgeBaseRequest,
    UpdateKnowledgeBaseRequest,
    AddDocumentRequest,
    KnowledgeBaseResponse,
    KnowledgeBaseListResponse,
    KnowledgeBaseStatus,
)
from .mcp import (
    McpServerInfo,
    McpServersResponse,
    McpSettingsResponse,
    UpdateMcpSettingsRequest,
)

__all__ = [
    # Common
    "SuccessResponse",
    "ErrorResponse",
    # Auth
    "RegisterRequest",
    "LoginRequest",
    "TokenResponse",
    "UserResponse",
    # Chat
    "SendMessageRequest",
    "MessageResponse",
    "ConversationResponse",
    "ConversationListResponse",
    # Knowledge
    "CreateKnowledgeBaseRequest",
    "UpdateKnowledgeBaseRequest",
    "AddDocumentRequest",
    "KnowledgeBaseResponse",
    "KnowledgeBaseListResponse",
    "KnowledgeBaseStatus",
    # MCP
    "McpServerInfo",
    "McpServersResponse",
    "McpSettingsResponse",
    "UpdateMcpSettingsRequest",
]