# Telegram Channel Monitor - WatcherGuru Scraper

This Python application monitors the WatcherGuru Telegram channel and automatically forwards new posts to your specified channel.

## Features

- 🔍 Real-time monitoring of WatcherGuru channel
- 📤 Automatic forwarding of new posts to your channel
- 🎨 Custom message formatting option
- 📝 Comprehensive logging
- 🔐 Secure authentication handling
- ⚡ Rate limiting protection

## Prerequisites

1. **Telegram API Credentials**: You need to obtain API credentials from Telegram:
   - Go to https://my.telegram.org/apps
   - Log in with your phone number
   - Create a new application
   - Note down your `API_ID` and `API_HASH`

2. **Python 3.7+**: Make sure you have Python 3.7 or higher installed

3. **Telegram Account**: You need a Telegram account with access to both source and destination channels

## Installation

1. **Clone or download this repository**

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   ```bash
   cp .env.example .env
   ```
   
   Edit the `.env` file with your credentials:
   ```env
   API_ID=your_api_id_here
   API_HASH=your_api_hash_here
   PHONE_NUMBER=your_phone_number_here
   SOURCE_CHANNEL=WatcherGuru
   DESTINATION_CHANNEL=your_channel_username_here
   SESSION_NAME=watcher_guru_monitor
   ```

## Configuration

### Environment Variables

- `API_ID`: Your Telegram API ID
- `API_HASH`: Your Telegram API Hash
- `PHONE_NUMBER`: Your phone number (with country code, e.g., +1234567890)
- `SOURCE_CHANNEL`: Source channel to monitor (default: WatcherGuru)
- `DESTINATION_CHANNEL`: Your destination channel username or ID
- `SESSION_NAME`: Session file name (default: watcher_guru_monitor)

### Channel Setup

**For the destination channel:**
- If using forwarding mode: You need admin rights in your destination channel
- If using custom message mode: You need permission to send messages

**Channel format options:**
- Username: `mychannel` or `@mychannel`
- Channel ID: `-1001234567890` (for private channels)

## Usage

### Basic Usage

Run the monitor:
```bash
python telegram_monitor.py
```

### First Run Authentication

On the first run, you'll be prompted to:
1. Enter the verification code sent to your Telegram app
2. If you have 2FA enabled, enter your password

The session will be saved for future runs.

### Monitoring Modes

The script supports two modes:

1. **Forwarding Mode** (`use_forwarding=True`):
   - Forwards original messages as-is
   - Requires admin rights in destination channel
   - Preserves original formatting and media

2. **Custom Message Mode** (`use_forwarding=False`):
   - Sends custom formatted messages
   - Adds timestamp and source information
   - Works with basic send message permissions

You can change the mode in the `main()` function:
```python
await monitor.start_monitoring(use_forwarding=False)  # Custom messages
await monitor.start_monitoring(use_forwarding=True)   # Forwarding
```

## Logging

The application creates detailed logs in:
- Console output (real-time)
- `telegram_monitor.log` file

Log levels include:
- INFO: Normal operations
- WARNING: Rate limits and recoverable errors
- ERROR: Critical errors

## Troubleshooting

### Common Issues

1. **"Could not find channel"**:
   - Verify channel username/ID is correct
   - Ensure you have access to both channels
   - For private channels, use the channel ID format

2. **"Authentication failed"**:
   - Check API_ID and API_HASH are correct
   - Verify phone number format includes country code
   - Delete session file and try again

3. **"Permission denied"**:
   - For forwarding: Ensure you're admin in destination channel
   - For custom messages: Ensure you can send messages to destination

4. **Rate limiting**:
   - The script automatically handles rate limits
   - If persistent, consider reducing message frequency

### Session Issues

If you encounter authentication problems:
```bash
# Remove session file and re-authenticate
rm watcher_guru_monitor.session
python telegram_monitor.py
```

## Security Notes

- Keep your `.env` file secure and never commit it to version control
- The session file contains authentication data - keep it secure
- Consider using environment variables in production instead of `.env` files

## Legal and Ethical Considerations

- Ensure you have permission to monitor and forward content
- Respect the original channel's terms of service
- Be mindful of copyright and content ownership
- Consider rate limiting to avoid being flagged as spam

## Contributing

Feel free to submit issues and enhancement requests!

## License

This project is provided as-is for educational purposes. Use responsibly and in accordance with Telegram's Terms of Service. 