#!/usr/bin/env python3
"""
eBay OAuth2 Authentication Helper

This script helps with the OAuth2 authorization flow for the eBay API.
It can be used to generate an authorization URL or exchange an authorization code for an access token.
"""

import os
import sys
import webbrowser
from urllib.parse import urlparse, parse_qs

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packages.connectors.channels.ebay import EBayAdapter
from config.ebay_config import get_ebay_config

# Load environment variables from .env file
load_dotenv()


def get_authorization_url():
    """Generate and display the eBay authorization URL."""
    config = get_ebay_config()

    if not config.get("ru_name"):
        print("Error: EBAY_RU_NAME environment variable is not set.")
        print("Please set this to your eBay Redirect URL Name (RuName).")
        return

    adapter = EBayAdapter(
        {
            "app_id": config["app_id"],
            "cert_id": config["cert_id"],
            "dev_id": config["dev_id"],
            "sandbox": config["sandbox"],
        }
    )

    # Generate a random state for CSRF protection
    import secrets

    state = secrets.token_urlsafe(16)

    auth_url = adapter.get_authorization_url(ru_name=config["ru_name"], state=state)

    print(f"eBay {'Sandbox' if config['sandbox'] else 'Production'} Authorization")
    print("=" * 50)
    print(f"1. Open this URL in your browser to authorize the application:")
    print(f"   {auth_url}")
    print("\n2. After authorizing, you will be redirected to your RuName URL.")
    print("3. Copy the full redirect URL from your browser's address bar.")
    print("4. Run this script with the redirect URL as an argument to get your tokens.")
    print("\nExample command:")
    print(f"   python {os.path.basename(__file__)} 'https://your-ru-name.com/?code=v1%5C...'")

    # Try to open the URL in the default web browser
    try:
        webbrowser.open(auth_url)
        print("\nOpened the authorization URL in your default web browser.")
    except Exception as e:
        print(f"\nCould not open browser: {e}")
        print("Please copy and paste the URL above into your browser.")


def exchange_code_for_token(redirect_url: str):
    """Exchange an authorization code for an access token.

    Args:
        redirect_url: The full redirect URL after authorization
    """
    # Parse the redirect URL
    parsed = urlparse(redirect_url)
    params = parse_qs(parsed.query)

    # Get the authorization code
    if "code" not in params:
        print("Error: No authorization code found in the redirect URL.")
        print("Make sure you're using the full redirect URL after authorizing the application.")
        return

    code = params["code"][0]

    # Get the RuName from the redirect URL
    ru_name = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    print("Exchanging authorization code for access token...")
    print(f"- Using RuName: {ru_name}")

    try:
        # Initialize the adapter
        config = get_ebay_config()
        adapter = EBayAdapter(
            {
                "app_id": config["app_id"],
                "cert_id": config["cert_id"],
                "dev_id": config["dev_id"],
                "sandbox": config["sandbox"],
            }
        )

        # Exchange the code for a token
        token_data = adapter.exchange_code_for_token(code=code, ru_name=ru_name)

        print("\nSuccess! Here are your tokens:")
        print("=" * 50)
        print(f"Access Token:  {token_data['access_token']}")
        print(f"Refresh Token: {token_data.get('refresh_token', 'Not provided')}")
        print(f"Expires In:    {token_data.get('expires_in', 'N/A')} seconds")
        print(f"Token Type:    {token_data.get('token_type', 'N/A')}")

        print("\nAdd these to your environment variables:")
        print("=" * 50)
        print(f"EBAY_AUTH_TOKEN={token_data['access_token']}")
        if "refresh_token" in token_data:
            print(f"EBAY_REFRESH_TOKEN={token_data['refresh_token']}")

        print("\nOr add them to your .env file:")
        print("=" * 50)
        print(f"EBAY_AUTH_TOKEN={token_data['access_token']}")
        if "refresh_token" in token_data:
            print(f"EBAY_REFRESH_TOKEN={token_data['refresh_token']}")

    except Exception as e:
        print(f"Error: {e}")
        print(
            "\nMake sure you have the correct credentials and that the authorization code hasn't expired."
        )


def refresh_token(refresh_token: str):
    """Refresh an access token using a refresh token.

    Args:
        refresh_token: The refresh token to use
    """
    print("Refreshing access token...")

    try:
        # Initialize the adapter with the refresh token
        config = get_ebay_config()
        adapter = EBayAdapter(
            {
                "app_id": config["app_id"],
                "cert_id": config["cert_id"],
                "dev_id": config["dev_id"],
                "sandbox": config["sandbox"],
                "refresh_token": refresh_token,
            }
        )

        # Refresh the token
        if adapter.authenticate(force_refresh=True):
            print("\nToken refreshed successfully!")
            print("=" * 50)
            print(f"New Access Token:  {adapter.config.auth_token}")
            print(f"New Refresh Token: {adapter.config.refresh_token}")
            print(f"Expires At:        {adapter.config.token_expiry}")

            print("\nUpdate your environment variables:")
            print("=" * 50)
            print(f"EBAY_AUTH_TOKEN={adapter.config.auth_token}")
            print(f"EBAY_REFRESH_TOKEN={adapter.config.refresh_token}")
        else:
            print("Failed to refresh token.")

    except Exception as e:
        print(f"Error: {e}")
        print(
            "\nMake sure you have the correct credentials and that the refresh token is still valid."
        )


def main():
    """Main function to handle command-line arguments."""
    import argparse

    parser = argparse.ArgumentParser(description="eBay OAuth2 Authentication Helper")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Subcommand: get-auth-url
    auth_parser = subparsers.add_parser("get-auth-url", help="Get the authorization URL")

    # Subcommand: exchange-code
    exchange_parser = subparsers.add_parser(
        "exchange-code", help="Exchange an authorization code for a token"
    )
    exchange_parser.add_argument("redirect_url", help="The full redirect URL after authorization")

    # Subcommand: refresh-token
    refresh_parser = subparsers.add_parser("refresh-token", help="Refresh an access token")
    refresh_parser.add_argument("refresh_token", help="The refresh token to use")

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        return

    args = parser.parse_args()

    if args.command == "get-auth-url":
        get_authorization_url()
    elif args.command == "exchange-code":
        exchange_code_for_token(args.redirect_url)
    elif args.command == "refresh-token":
        refresh_token(args.refresh_token)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
