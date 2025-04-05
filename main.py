from fastapi import FastAPI, HTTPException, Header, Query, Path, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import httpx
import base64
import json

app = FastAPI(
    title="Smithery Registry API Server",
    version="1.0.0",
    description="OpenAPI server for Smithery Registry, providing access to search and obtain launch configurations for MCP servers.",
)

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Base URL for Smithery Registry API
BASE_URL = "https://registry.smithery.ai"

# Models for API responses
class Connection(BaseModel):
    type: str = Field(..., description="Connection type ('ws' or 'stdio')")
    url: Optional[str] = Field(None, description="Connection URL if available")
    configSchema: Dict[str, Any] = Field(..., description="JSONSchema for configuration")

class Server(BaseModel):
    qualifiedName: str = Field(..., description="Unique server identifier")
    displayName: str = Field(..., description="Human-readable server name")
    description: str = Field(..., description="Server description")
    homepage: str = Field(..., description="Server homepage URL")
    useCount: str = Field(..., description="Usage count")
    isDeployed: bool = Field(..., description="Deployment status")
    createdAt: str = Field(..., description="Creation timestamp")

class Pagination(BaseModel):
    currentPage: int = Field(..., description="Current page number")
    pageSize: int = Field(..., description="Items per page")
    totalPages: int = Field(..., description="Total number of pages")
    totalCount: int = Field(..., description="Total item count")

class ServerListResponse(BaseModel):
    servers: List[Server] = Field(..., description="List of servers")
    pagination: Pagination = Field(..., description="Pagination information")

class ServerDetailResponse(BaseModel):
    qualifiedName: str = Field(..., description="Server identifier")
    displayName: str = Field(..., description="Human-readable server name")
    deploymentUrl: str = Field(..., description="Deployment URL")
    connections: List[Connection] = Field(..., description="Available connections")

# WebSocket URL Creation Utility
class WebSocketUrlRequest(BaseModel):
    qualifiedName: str = Field(..., description="Server identifier")
    config: Dict[str, Any] = Field(..., description="Configuration object matching the server's configSchema")

class WebSocketUrlResponse(BaseModel):
    wsUrl: str = Field(..., description="Complete WebSocket URL with encoded config")

# Authentication dependency
async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.replace("Bearer ", "")
    if not token:
        raise HTTPException(status_code=401, detail="No token provided")
    
    return token

# Endpoints
@app.get(
    "/servers",
    response_model=ServerListResponse,
    summary="List MCP Servers",
    description="Search and list available MCP servers with optional filtering"
)
async def list_servers(
    q: Optional[str] = Query(None, description="Search query (semantic search)"),
    page: int = Query(1, description="Page number"),
    page_size: int = Query(10, description="Items per page", alias="pageSize"),
    authorization: str = Depends(verify_token)
):
    params = {}
    if q:
        params["q"] = q
    if page:
        params["page"] = page
    if page_size:
        params["pageSize"] = page_size

    async with httpx.AsyncClient() as client:
        headers = {"Authorization": authorization}
        response = await client.get(f"{BASE_URL}/servers", params=params, headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Smithery Registry API error: {response.text}"
            )
            
        return response.json()

@app.get(
    "/servers/{qualified_name}",
    response_model=ServerDetailResponse,
    summary="Get Server Details",
    description="Get detailed information about a specific MCP server including connection configuration"
)
async def get_server(
    qualified_name: str = Path(..., description="Qualified name of the server"),
    authorization: str = Depends(verify_token)
):
    async with httpx.AsyncClient() as client:
        headers = {"Authorization": authorization}
        response = await client.get(f"{BASE_URL}/servers/{qualified_name}", headers=headers)
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=f"Smithery Registry API error: {response.text}"
            )
            
        return response.json()

@app.post(
    "/create-websocket-url",
    response_model=WebSocketUrlResponse,
    summary="Create WebSocket URL",
    description="Create a complete WebSocket URL with base64-encoded config for connecting to an MCP server"
)
async def create_websocket_url(request: WebSocketUrlRequest):
    # Base64 encode the config
    config_json = json.dumps(request.config)
    config_base64 = base64.b64encode(config_json.encode()).decode()
    
    # Create the WebSocket URL
    ws_url = f"https://server.smithery.ai/{request.qualifiedName}/ws?config={config_base64}"
    
    return WebSocketUrlResponse(wsUrl=ws_url)