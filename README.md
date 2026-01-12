# Robin AI - GroupMe Bot

Robin AI is a Python Flask bot that responds to group messages on GroupMe using OpenAI GPT-4. It acts as a virtual Residential Assistant (RA) for Robinson Dorm at Stanford University.

## Important Note About GroupMe Bots

**GroupMe bots can only work in group chats, not direct messages (DMs).** To simulate private one-on-one conversations, create a dedicated group chat with just your bot and one user. This effectively creates a private conversation channel.

## Features

- ✅ Responds to group messages (works best in one-on-one groups for private conversations)
- ✅ Uses OpenAI GPT-4 for intelligent responses
- ✅ Token usage tracking with daily limits
- ✅ Prevents message loops by ignoring bot's own messages
- ✅ Friendly, helpful, and professional RA personality
- ✅ Health check and statistics endpoints

## Prerequisites

- Python 3.8 or higher
- OpenAI API key
- GroupMe Bot ID and Access Token
- ngrok (for local testing)
- A public server (for deployment)

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and fill in your credentials:

```bash
cp env.example .env
```

Edit `.env` and add your configuration:

```env
# OpenAI API Configuration
OPENAI_API_KEY=your_openai_api_key_here

# GroupMe Bot Configuration
GROUPME_BOT_ID=your_groupme_bot_id_here
GROUPME_ACCESS_TOKEN=your_groupme_access_token_here

# Application Configuration
PORT=5000
FLASK_ENV=development

# Token Usage Limits
MAX_TOKENS_PER_DAY=50000
```

### 3. Getting GroupMe Credentials

To get your GroupMe Bot ID and Access Token:

1. **Create a Bot**:

   - Go to [GroupMe Developer Portal](https://dev.groupme.com/)
   - Create a new bot
   - Note down your Bot ID

2. **Get Access Token**:
   - Log in to GroupMe
   - Go to your [Access Token page](https://dev.groupme.com/applications)
   - Create a new application if needed
   - Copy your Access Token

## Testing Locally with ngrok

### 1. Start the Flask Application

```bash
python app.py
```

The app will start on `http://localhost:5000` by default.

### 2. Start ngrok

In a new terminal window:

```bash
ngrok http 5000
```

ngrok will provide you with a public URL like:

```
Forwarding    https://abc123.ngrok.io -> http://localhost:5000
```

### 3. Configure GroupMe Callback URL

1. Go to your GroupMe bot settings in the [Developer Portal](https://dev.groupme.com/bots)
2. Set the callback URL to your ngrok URL + `/webhook`:
   ```
   https://abc123.ngrok.io/webhook
   ```
3. Save the configuration

### 4. Add Bot to a Group and Test

**For Private One-on-One Conversations:**

1. Create a new group in GroupMe
2. Add only yourself and the bot to the group (2 members total)
3. Send a message in this group
4. The bot should respond with GPT-4 generated replies

**For Group Conversations:**

1. Add the bot to any existing GroupMe group
2. Send messages in the group
3. The bot will respond to all messages in that group

### 5. Check Health and Statistics

- **Health Check**: `http://localhost:5000/health`
- **Token Statistics**: `http://localhost:5000/stats`

## Deployment to a Public Server

### Option 1: Deploying to Vercel (Recommended for Free Tier)

**Note:** Your code is already pushed to GitHub: https://github.com/marianaisaw/Robin-AI

1. **Go to Vercel Dashboard**:

   - Visit [vercel.com](https://vercel.com) and sign up/login (use GitHub to connect)

2. **Import Your GitHub Repository**:

   - Click "New Project"
   - Select "Import Git Repository"
   - Choose `marianaisaw/Robin-AI`
   - Click "Import"

3. **Configure Environment Variables**:

   - In the "Environment Variables" section, add all your variables:
     - `OPENAI_API_KEY` = your OpenAI API key
     - `GROUPME_BOT_ID` = your bot ID (84c1834e8bec8ca2dd819b8b20)
     - `GROUPME_BOT_NAME` = Robin AI
     - `GROUPME_ACCESS_TOKEN` = your access token
     - `MAX_TOKENS_PER_DAY` = 50000
     - `PORT` = 5000 (optional)
     - `FLASK_ENV` = production (optional)
   - Click "Deploy"

4. **Update GroupMe Callback URL**:
   - After deployment, Vercel will give you a URL like: `https://your-app.vercel.app`
   - Update your GroupMe bot's callback URL to: `https://your-app.vercel.app/webhook`
   - Go to [GroupMe Developer Portal](https://dev.groupme.com/bots) → Edit your bot → Update callback URL

**Important Vercel Notes:**

- Free tier has a 10-second function timeout (should be fine for most requests)
- Your code is already configured with `vercel.json`
- Environment variables are secure (never commit `.env` file)

### Option 2: Using Other Cloud Providers (Railway, Render, etc.)

1. **Prepare for Deployment**:

   - Make sure your `.env` file is not committed (it should be in `.gitignore`)
   - Set environment variables on your hosting platform

2. **Deploy**:

   ```bash
   git push origin main  # Already done if using GitHub
   ```

3. **Configure Environment Variables**:

   - Set all environment variables from `.env` in your hosting platform's dashboard
   - Use the same variable names (OPENAI_API_KEY, GROUPME_BOT_ID, etc.)

4. **Update GroupMe Callback URL**:
   - Update your bot's callback URL to: `https://your-domain.com/webhook`

### Option 2: Using a VPS (DigitalOcean, AWS EC2, etc.)

1. **SSH into your server**:

   ```bash
   ssh user@your-server-ip
   ```

2. **Install Python and dependencies**:

   ```bash
   sudo apt update
   sudo apt install python3 python3-pip nginx
   pip3 install -r requirements.txt
   ```

3. **Set up environment variables**:

   ```bash
   nano .env
   # Add your configuration
   ```

4. **Run with gunicorn** (recommended for production):

   ```bash
   pip install gunicorn
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

5. **Set up Nginx as reverse proxy**:

   ```nginx
   server {
       listen 80;
       server_name your-domain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

6. **Set up SSL with Let's Encrypt**:

   ```bash
   sudo apt install certbot python3-certbot-nginx
   sudo certbot --nginx -d your-domain.com
   ```

7. **Update GroupMe Callback URL**:
   - Update your bot's callback URL to: `https://your-domain.com/webhook`

### Using systemd for Service Management (Optional)

Create a service file for automatic startup:

```bash
sudo nano /etc/systemd/system/robin-ai.service
```

Add:

```ini
[Unit]
Description=Robin AI GroupMe Bot
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/RobinAI
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/local/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable robin-ai
sudo systemctl start robin-ai
sudo systemctl status robin-ai
```

## Project Structure

```
RobinAI/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── env.example         # Example environment variables
├── .env               # Your actual environment variables (not in git)
└── README.md          # This file
```

## API Endpoints

- `POST /webhook` - GroupMe callback endpoint (receives messages)
- `GET /health` - Health check endpoint
- `GET /stats` - Token usage statistics

## Configuration Options

- `OPENAI_API_KEY` - Your OpenAI API key (required)
- `GROUPME_BOT_ID` - Your GroupMe Bot ID (required)
- `GROUPME_ACCESS_TOKEN` - Your GroupMe Access Token (required)
- `PORT` - Port to run the Flask app on (default: 5000)
- `FLASK_ENV` - Flask environment (development/production)
- `MAX_TOKENS_PER_DAY` - Daily token limit (default: 50000)

## Troubleshooting

### Bot not responding

- Check that your callback URL is correctly configured in GroupMe
- Verify your ngrok tunnel is running (for local testing)
- Check Flask logs for errors
- Ensure all environment variables are set correctly

### Token limit reached

- Check `/stats` endpoint to see current usage
- Increase `MAX_TOKENS_PER_DAY` if needed
- Wait until the next day (reset happens daily at midnight)

### Messages not being received

- Verify the webhook endpoint is accessible publicly
- Check that GroupMe can reach your callback URL
- Review logs for incoming webhook requests

## Security Notes

- Never commit your `.env` file to version control
- Keep your OpenAI API key secure
- Use HTTPS in production
- Regularly rotate access tokens
- Monitor token usage to avoid unexpected costs

## License

This project is for use at Stanford University's Robinson Dorm.
