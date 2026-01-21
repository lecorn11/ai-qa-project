from .common import SuccessResponse, ErrorResponse
from .auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from .conversation import (
    SendMessageRequest,
    MessageResponse,
    ConversationResponse,
    ConversationListResponse,
    AgentChatRequest,
    AgentChatResponse,
)
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
    "AgentChatRequest",
    "AgentChatResponse",
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
