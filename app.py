"""
Robin AI - GroupMe Bot
A Python Flask bot that responds to group messages using OpenAI GPT-4.
Acts as a virtual RA for Robinson Dorm at Stanford.

Note: GroupMe bots can only work in group chats, not direct messages.
To simulate private conversations, create one-on-one groups (bot + 1 user).
"""

import os
import json
import logging
import time
import requests
from flask import Flask, request, jsonify
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAI_API_KEY')
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set")

openai_client = OpenAI(api_key=openai_api_key)

# Configuration
GROUPME_BOT_ID = os.getenv('GROUPME_BOT_ID', '')
GROUPME_BOT_NAME = os.getenv('GROUPME_BOT_NAME', 'Robin AI')  # Bot name for mention detection
MAX_TOKENS_PER_DAY = int(os.getenv('MAX_TOKENS_PER_DAY', '50000'))  # Default: 50k tokens per day
GROUPME_API_BASE_URL = 'https://api.groupme.com/v3'

# Token usage tracking (in production, use a database instead)
# Format: {date: total_tokens_used}
daily_token_usage = {}

# System prompt for Robin AI
SYSTEM_PROMPT = """You are Robin AI, the virtual Residential Assistant (RA) for Robinson Dorm at Stanford University.

Your role:
- Provide clear, concise, and kind answers to students' questions
- Be friendly, helpful, and professional like a supportive residential assistant
- Help students navigate dorm life, answer questions about policies, facilities, and campus resources
- Maintain a warm and approachable tone while being informative

Remember to:
- Keep responses concise but complete
- Be empathetic and understanding
- Provide actionable advice when possible
- Maintain professionalism appropriate for a Stanford residential environment"""


def get_today_date():
    """Get today's date as a string (YYYY-MM-DD)."""
    from datetime import datetime
    return datetime.now().strftime('%Y-%m-%d')


def check_token_limit():
    """
    Check if we've exceeded the daily token limit.
    Returns: (bool) True if within limit, False if exceeded
    """
    today = get_today_date()
    tokens_used_today = daily_token_usage.get(today, 0)
    
    if tokens_used_today >= MAX_TOKENS_PER_DAY:
        logger.warning(f"Daily token limit reached: {tokens_used_today}/{MAX_TOKENS_PER_DAY}")
        return False
    return True


def update_token_usage(tokens_used):
    """
    Update the daily token usage counter.
    Args:
        tokens_used (int): Number of tokens used in the request
    """
    today = get_today_date()
    daily_token_usage[today] = daily_token_usage.get(today, 0) + tokens_used
    logger.info(f"Token usage updated: {daily_token_usage[today]}/{MAX_TOKENS_PER_DAY} tokens used today")


def send_group_message(text):
    """
    Send a message to the group chat via GroupMe Bot API.
    Note: GroupMe bots can only send messages to group chats, not direct messages.
    Args:
        text (str): The message text to send
    Returns:
        bool: True if message sent successfully, False otherwise
    """
    if not GROUPME_BOT_ID:
        logger.error("GROUPME_BOT_ID not configured")
        return False
    
    url = f"{GROUPME_API_BASE_URL}/bots/post"
    payload = {
        'bot_id': GROUPME_BOT_ID,
        'text': text
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Group message sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send group message: {e}")
        logger.error(f"Response: {response.text if 'response' in locals() else 'N/A'}")
        return False


def get_openai_response(user_message):
    """
    Get a response from OpenAI GPT-4 for the user's message.
    Args:
        user_message (str): The user's message text
    Returns:
        tuple: (response_text, tokens_used) or (None, 0) on error
    """
    try:
        # Try gpt-4o first (latest GPT-4 model), fall back to gpt-4-turbo or gpt-3.5-turbo
        model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        response = openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            max_tokens=500,  # Limit response length
            temperature=0.7  # Balanced creativity/consistency
        )
        
        response_text = response.choices[0].message.content
        tokens_used = response.usage.total_tokens
        
        logger.info(f"OpenAI response generated. Tokens used: {tokens_used}")
        return response_text, tokens_used
        
    except Exception as e:
        logger.error(f"Error getting OpenAI response: {e}")
        return None, 0


@app.route('/webhook', methods=['POST'])
def webhook():
    """
    Main webhook endpoint that receives GroupMe callbacks.
    Handles group messages and generates responses using OpenAI.
    
    Note: GroupMe bots can only receive messages in group chats, not direct messages.
    To simulate private conversations, create a one-on-one group (bot + 1 user).
    """
    try:
        # Parse the incoming JSON payload
        data = request.get_json()
        
        if not data:
            logger.warning("Received empty request")
            return jsonify({'status': 'error', 'message': 'Empty request'}), 400
        
        logger.info(f"Received webhook: {json.dumps(data, indent=2)}")
        
        # GroupMe sends group messages directly (not wrapped in 'direct_message' key)
        # Extract message details
        sender_id = data.get('sender_id', '')
        sender_type = data.get('sender_type', '')
        message_text = data.get('text', '').strip()
        sender_name = data.get('name', 'Unknown')
        group_id = data.get('group_id', '')
        user_id = data.get('user_id', '')
        
        # Ignore messages from the bot itself to prevent loops
        # GroupMe identifies bot messages with sender_type == 'bot'
        if sender_type == 'bot':
            logger.info("Ignoring message from bot itself")
            return jsonify({'status': 'ignored', 'reason': 'bot_message'}), 200
        
        # Also check if sender_id matches bot_id (backup check)
        if sender_id == GROUPME_BOT_ID or user_id == GROUPME_BOT_ID:
            logger.info("Ignoring message from bot itself (ID match)")
            return jsonify({'status': 'ignored', 'reason': 'bot_message'}), 200
        
        # Ignore empty messages
        if not message_text:
            logger.info("Ignoring empty message")
            return jsonify({'status': 'ignored', 'reason': 'empty_message'}), 200
        
        # Check if bot is mentioned/tagged in the message
        # GroupMe uses @botname format for mentions
        bot_mentioned = False
        message_lower = message_text.lower()
        bot_name_lower = GROUPME_BOT_NAME.lower()
        
        # Check for @mention format
        if f"@{bot_name_lower}" in message_lower:
            bot_mentioned = True
        # Also check if bot name appears in message (more lenient)
        elif bot_name_lower in message_lower:
            bot_mentioned = True
        
        # Check for mentions in attachments (GroupMe includes mention data here)
        attachments = data.get('attachments', [])
        for attachment in attachments:
            if attachment.get('type') == 'mentions':
                # If mentions exist, the bot might be mentioned
                # For now, if there are any mentions, we'll assume the bot is mentioned
                # You can refine this by checking the user_ids in mentions
                bot_mentioned = True
                break
        
        # Only respond if the bot is mentioned/tagged
        if not bot_mentioned:
            logger.info(f"Ignoring message - bot not mentioned: {message_text[:100]}")
            return jsonify({'status': 'ignored', 'reason': 'bot_not_mentioned'}), 200
        
        logger.info(f"Processing message from {sender_name} (ID: {sender_id}) in group {group_id}: {message_text[:100]}")
        
        # Check token limit before processing
        if not check_token_limit():
            error_message = "I've reached my daily response limit. Please try again tomorrow!"
            send_group_message(error_message)
            return jsonify({'status': 'error', 'message': 'Token limit reached'}), 429
        
        # Get response from OpenAI
        response_text, tokens_used = get_openai_response(message_text)
        
        if not response_text:
            error_message = "I'm having trouble processing your message right now. Please try again in a moment!"
            send_group_message(error_message)
            return jsonify({'status': 'error', 'message': 'OpenAI error'}), 500
        
        # Update token usage
        update_token_usage(tokens_used)
        
        # Send the response to the group chat
        send_group_message(response_text)
        
        return jsonify({'status': 'success'}), 200
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}", exc_info=True)
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Robin AI GroupMe Bot'
    }), 200


@app.route('/stats', methods=['GET'])
def stats():
    """
    Endpoint to check token usage statistics.
    Useful for monitoring and debugging.
    """
    today = get_today_date()
    tokens_used_today = daily_token_usage.get(today, 0)
    
    return jsonify({
        'date': today,
        'tokens_used_today': tokens_used_today,
        'max_tokens_per_day': MAX_TOKENS_PER_DAY,
        'tokens_remaining': max(0, MAX_TOKENS_PER_DAY - tokens_used_today),
        'percentage_used': round((tokens_used_today / MAX_TOKENS_PER_DAY) * 100, 2) if MAX_TOKENS_PER_DAY > 0 else 0
    }), 200


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_ENV') == 'development'
    
    logger.info("Starting Robin AI GroupMe Bot...")
    logger.info(f"Max tokens per day: {MAX_TOKENS_PER_DAY}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

