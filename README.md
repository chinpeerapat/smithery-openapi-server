# Smithery Registry OpenAPI Server

This server provides an OpenAPI interface to the Smithery Registry API, allowing you to search and obtain launch configurations for Model Context Protocol (MCP) servers.

## Features

- List available MCP servers with advanced filtering
- Get detailed server information including connection configurations
- Generate WebSocket URLs with base64-encoded configurations
- Authentication via bearer token
- Compatible with OpenAPI tools and clients

## Authentication

All requests to the Smithery Registry API require authentication:

- You need a bearer token in the `Authorization` header
- Format: `Authorization: Bearer your-api-token`
- Obtain a token from your Smithery user profile under API keys

## Usage

### Installation

```bash
pip install -r requirements.txt
```

### Running the server

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### API Endpoints

1. `GET /servers` - List available MCP servers
   - Query parameters:
     - `q`: Search query (semantic search)
     - `page`: Page number (default: 1)
     - `pageSize`: Items per page (default: 10)
   - Advanced filtering syntax in the `q` parameter:
     - Text search: "machine learning"
     - Owner filter: owner:username
     - Repository filter: repo:repository-name 
     - Deployment status: is:deployed
     - Example: "owner:smithery-ai repo:fetch is:deployed machine learning"

2. `GET /servers/{qualified_name}` - Get detailed information about a specific server

3. `POST /create-websocket-url` - Create a WebSocket URL with encoded config
   - Request body:
     ```json
     {
       "qualifiedName": "username/repository",
       "config": {
         // Configuration object matching the server's schema
       }
     }
     ```

## WebSocket Connection

For direct WebSocket connections to MCP servers:
- URL Format: `https://server.smithery.ai/${qualifiedName}/ws?config=${base64encode(config)}`
- Config must comply with the server's configSchema
- Config is base64-encoded JSON

## Integration with OpenAPI Tools

This server is designed to be compatible with any OpenAPI-compliant tools and frameworks. The API follows RESTful conventions and provides detailed OpenAPI documentation at the `/docs` endpoint when running.

## TypeScript SDK Usage

For use with the Smithery TypeScript SDK:

```typescript
import { WebSocketClientTransport } from "@modelcontextprotocol/sdk/client/websocket.js"
import { createSmitheryUrl } from "@smithery/sdk/config.js"

const url = createSmitheryUrl(
  "https://your-smithery-mcp-server/ws",
  {
    // config object matching schema
  },
)
const transport = new WebSocketClientTransport(url)
```

## License

MIT