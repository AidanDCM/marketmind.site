"""API documentation configuration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi


def setup_docs(app: FastAPI):
    """Configure API documentation."""
    # Access settings via get_settings() if needed for environment-specific docs behavior

    # Configure CORS for Swagger UI
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title="MarketMind API",
            version="1.0.0",
            description="""
            # MarketMind API Documentation
            
            This is the API documentation for the MarketMind e-commerce automation platform.
            
            ## Authentication
            
            Most endpoints require authentication. Use the `/auth/token` endpoint to get an access token.
            
            ## Rate Limiting
            
            - 1000 requests per minute per IP address
            - 10,000 requests per day per user
            
            ## Error Handling
            
            - 400: Bad Request - Invalid request data
            - 401: Unauthorized - Invalid or missing authentication
            - 403: Forbidden - Insufficient permissions
            - 404: Not Found - Resource not found
            - 429: Too Many Requests - Rate limit exceeded
            - 500: Internal Server Error - Something went wrong
            """,
            routes=app.routes,
        )

        # Add security schemes
        openapi_schema["components"]["securitySchemes"] = {
            "OAuth2PasswordBearer": {
                "type": "oauth2",
                "flows": {
                    "password": {
                        "tokenUrl": "/auth/token",
                        "scopes": {
                            "read": "Read access to resources",
                            "write": "Write access to resources",
                            "admin": "Admin access",
                        },
                    }
                },
            }
        }

        # Add security to all endpoints by default
        for path in openapi_schema["paths"].values():
            for method in path.values():
                if "security" not in method:
                    method["security"] = [{"OAuth2PasswordBearer": []}]

        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi

    # Custom Swagger UI
    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui_html():
        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=app.title + " - Swagger UI",
            oauth2_redirect_url=app.swagger_ui_oauth2_redirect_url,
            swagger_js_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui-bundle.js",
            swagger_css_url="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5/swagger-ui.css",
            swagger_favicon_url="https://fastapi.tiangolo.com/img/favicon.png",
        )

    return app
