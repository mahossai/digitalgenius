import requests
import json
import base64
import re
import os
from typing import Optional, Dict, Any

def validate_email(email: str) -> bool:
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def send_gorgias_email_reply(
    ticket_id: int,
    agent_email: str,
    customer_email: str,
    email_text: str,
    api_token: str,
    subdomain: str = None,
    subject: str = None,
    timeout: int = 30
) -> Optional[Dict[Any, Any]]:
    """
    Sends an email reply to a specific Gorgias support ticket.

    Parameters:
        ticket_id (int): The ticket ID to reply to.
        agent_email (str): Email of the agent sending the response.
        customer_email (str): Email of the customer receiving the reply.
        email_text (str): The text content of the email reply.
        api_token (str): API token for Basic Auth.
        subdomain (str, optional): Gorgias subdomain. If None, uses GORGIAS_SUBDOMAIN env var.
        subject (str, optional): Email subject. If None, uses default.
        timeout (int): Request timeout in seconds. Default is 30.

    Returns:
        dict: Response data if successful, None if failed.
        
    Raises:
        ValueError: If required parameters are missing or invalid.
    """
    
    # Input validation
    if not all([ticket_id, agent_email, customer_email, email_text, api_token]):
        raise ValueError("All required parameters must be provided and non-empty")
    
    if not isinstance(ticket_id, int) or ticket_id <= 0:
        raise ValueError("ticket_id must be a positive integer")
    
    if not validate_email(agent_email):
        raise ValueError(f"Invalid agent email format: {agent_email}")
    
    if not validate_email(customer_email):
        raise ValueError(f"Invalid customer email format: {customer_email}")
    
    # Get subdomain from parameter or environment variable
    if subdomain is None:
        subdomain = os.getenv('GORGIAS_SUBDOMAIN')
        if not subdomain:
            raise ValueError("Subdomain must be provided or set in GORGIAS_SUBDOMAIN environment variable")
    
    # Default subject if not provided
    if subject is None:
        subject = f"Re: Support Ticket #{ticket_id}"
    
    # Construct API URL
    url = f"https://{subdomain}.gorgias.com/api/tickets/{ticket_id}/messages"
    
    # Encode Basic Auth header
    basic_auth_string = f"{agent_email}:{api_token}"
    encoded_auth = base64.b64encode(basic_auth_string.encode('utf-8')).decode('utf-8')
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_auth}',
        'User-Agent': 'Gorgias-API-Client/1.0'
    }
    
    # Construct payload - FIXED: Now sends TO customer, FROM agent
    payload = {
        "receiver": {
            "email": customer_email  # Customer receives the reply
        },
        "sender": {
            "email": agent_email  # Agent sends the reply
        },
        "source": {
            "to": [
                {
                    "address": customer_email
                }
            ],
            "from": {
                "address": agent_email
            }
        },
        "body_html": email_text,
        "body_text": email_text,
        "channel": "email",
        "from_agent": True,
        "via": "api",
        "subject": subject
    }
    
    try:
        # Send the POST request
        response = requests.post(
            url, 
            headers=headers, 
            data=json.dumps(payload),
            timeout=timeout
        )
        
        # Handle different response status codes
        if response.status_code == 201:
            print("✅ Email reply sent successfully.")
            return response.json()
        elif response.status_code == 400:
            print(f"❌ Bad request: {response.text}")
            return None
        elif response.status_code == 401:
            print("❌ Unauthorized: Check your email and API token")
            return None
        elif response.status_code == 404:
            print(f"❌ Ticket {ticket_id} not found")
            return None
        elif response.status_code == 422:
            print(f"❌ Validation error: {response.text}")
            return None
        else:
            print(f"❌ Failed to send email. Status: {response.status_code}, Response: {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"❌ Request timed out after {timeout} seconds")
        return None
    except requests.exceptions.ConnectionError:
        print("❌ Connection error: Unable to connect to Gorgias API")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return None
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return None


def get_ticket_info(ticket_id: int, agent_email: str, api_token: str, subdomain: str = None) -> Optional[Dict[Any, Any]]:
    """
    Retrieve ticket information to get customer email and other details.
    
    Parameters:
        ticket_id (int): The ticket ID to query.
        agent_email (str): Agent's email for authentication.
        api_token (str): API token for Basic Auth.
        subdomain (str, optional): Gorgias subdomain.
        
    Returns:
        dict: Ticket data if successful, None if failed.
    """
    if subdomain is None:
        subdomain = os.getenv('GORGIAS_SUBDOMAIN')
        if not subdomain:
            raise ValueError("Subdomain must be provided or set in GORGIAS_SUBDOMAIN environment variable")
    
    url = f"https://{subdomain}.gorgias.com/api/tickets/{ticket_id}"
    
    basic_auth_string = f"{agent_email}:{api_token}"
    encoded_auth = base64.b64encode(basic_auth_string.encode('utf-8')).decode('utf-8')
    
    headers = {
        'Authorization': f'Basic {encoded_auth}',
        'User-Agent': 'Gorgias-API-Client/1.0'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"❌ Failed to get ticket info. Status: {response.status_code}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting ticket info: {e}")
        return None


# Example usage and testing
if __name__ == "__main__":
    import os
    
    # Example configuration (replace with actual values)
    TEST_CONFIG = {
        'ticket_id': 12345,
        'agent_email': 'agent@yourcompany.com',
        'customer_email': 'customer@example.com',
        'email_text': 'Hello! Thank you for contacting us. We have received your request and will get back to you shortly.',
        'api_token': 'your_api_token_here',
        'subdomain': 'yourcompany'  # or set GORGIAS_SUBDOMAIN env var
    }
    
    print("🧪 Testing Gorgias email reply function...")
    print("=" * 50)
    
    # Test input validation
    try:
        print("📝 Testing input validation...")
        
        # Test with invalid email
        try:
            send_gorgias_email_reply(123, "invalid-email", "test@example.com", "test", "token")
            print("❌ Validation should have failed for invalid email")
        except ValueError as e:
            print(f"✅ Correctly caught invalid email: {e}")
        
        # Test with missing parameters
        try:
            send_gorgias_email_reply(123, "", "test@example.com", "test", "token")
            print("❌ Validation should have failed for empty parameters")
        except ValueError as e:
            print(f"✅ Correctly caught empty parameter: {e}")
            
        print("\n📡 Testing API call (will fail without real credentials)...")
        
        # This will fail without real credentials, but shows the structure
        result = send_gorgias_email_reply(
            ticket_id=TEST_CONFIG['ticket_id'],
            agent_email=TEST_CONFIG['agent_email'],
            customer_email=TEST_CONFIG['customer_email'],
            email_text=TEST_CONFIG['email_text'],
            api_token=TEST_CONFIG['api_token'],
            subdomain=TEST_CONFIG['subdomain']
        )
        
        if result:
            print("✅ Test completed successfully")
            print(f"Response: {json.dumps(result, indent=2)}")
        else:
            print("ℹ️  Test failed (expected with dummy credentials)")
            
    except Exception as e:
        print(f"❌ Test error: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 To use this code:")
    print("1. Replace TEST_CONFIG values with real data")
    print("2. Set environment variable: export GORGIAS_SUBDOMAIN='yoursubdomain'")
    print("3. Ensure your API token has proper permissions")
    print("4. Test with a real ticket ID and customer email")