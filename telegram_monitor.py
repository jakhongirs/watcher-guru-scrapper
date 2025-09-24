import asyncio
import logging
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from telethon.tl.types import MessageMediaPhoto, MessageMediaDocument
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('telegram_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TelegramChannelMonitor:
    def __init__(self):
        self.api_id = os.getenv('API_ID')
        self.api_hash = os.getenv('API_HASH')
        self.phone_number = os.getenv('PHONE_NUMBER')
        self.source_channel = os.getenv('SOURCE_CHANNEL', 'WatcherGuru')
        self.destination_channel = os.getenv('DESTINATION_CHANNEL')
        self.session_name = os.getenv('SESSION_NAME', 'watcher_guru_monitor')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not all([self.api_id, self.api_hash, self.phone_number, self.destination_channel, self.openai_api_key]):
            raise ValueError("Missing required environment variables. Check your .env file.")
        
        self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
        self.openai_client = OpenAI(api_key=self.openai_api_key)
        
    async def authenticate(self):
        """Authenticate with Telegram"""
        try:
            await self.client.connect()
            
            if not await self.client.is_user_authorized():
                logger.info("User not authorized. Starting authentication process...")
                await self.client.send_code_request(self.phone_number)
                
                code = input("Enter the code you received: ")
                try:
                    await self.client.sign_in(self.phone_number, code)
                except SessionPasswordNeededError:
                    password = input("Two-factor authentication enabled. Enter your password: ")
                    await self.client.sign_in(password=password)
                    
            logger.info("Successfully authenticated!")
            
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise
    
    async def get_channel_entity(self, channel_name):
        """Get channel entity by username or ID"""
        try:
            if channel_name.startswith('@'):
                channel_name = channel_name[1:]
            elif channel_name.startswith('-100'):
                # It's a channel ID
                return int(channel_name)
            
            entity = await self.client.get_entity(channel_name)
            return entity
        except Exception as e:
            logger.error(f"Failed to get channel entity for {channel_name}: {e}")
            return None
    
    async def forward_message(self, message):
        """Forward a message to the destination channel"""
        try:
            destination = await self.get_channel_entity(self.destination_channel)
            if not destination:
                logger.error(f"Could not find destination channel: {self.destination_channel}")
                return False
            
            # Forward the message
            await self.client.forward_messages(destination, message)
            logger.info(f"Successfully forwarded message from {self.source_channel} to {self.destination_channel}")
            return True
            
        except FloodWaitError as e:
            logger.warning(f"Rate limit hit. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            logger.error(f"Failed to forward message: {e}")
            return False
    
    def clean_text(self, text):
        """Remove links and mentions from text and return cleaned version (without custom mention)"""
        if not text:
            return None
        
        import re
        # Remove URLs (http/https links)
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        # Remove Telegram links (t.me links)
        text = re.sub(r't\.me/[^\s]+', '', text)
        # Remove www links
        text = re.sub(r'www\.[^\s]+', '', text)
        # Remove mentions (@username)
        text = re.sub(r'@[a-zA-Z0-9_]+', '', text)
        # Clean up extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text if text else None

    async def translate_text(self, text):
        """Translate text to Uzbek and Russian using OpenAI"""
        if not text:
            return "@pullab_news"
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a professional translator. Translate ONLY the content provided into Uzbek and Russian. "
                        "CRITICAL RULES:\n"
                        "- NO introductory words like 'Xabar', 'YANGILIK', 'НОВОСТИ', 'Сообщение' etc.\n"
                        "- NO explanatory text or commentary\n"
                        "- Translate EXACTLY what is given, nothing more\n"
                        "- Format response EXACTLY as:\n\n"
                        "🇺🇿 [direct translation only]\n\n"
                        "🇷🇺 [direct translation only]"
                    },
                    {
                        "role": "user", 
                        "content": text
                    }
                ],
                max_tokens=500,
                temperature=0.1,
            )
            
            translated_text = response.choices[0].message.content.strip()
            # Add the mention statically after translation
            final_text = f"{translated_text}\n\n@pullab_news"
            logger.info("Successfully translated text using OpenAI")
            return final_text
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Fallback: return original text with custom mention
            return f"{text}\n\n@pullab_news"

    async def handle_grouped_media(self, messages, destination):
        """Handle grouped media (albums) from the source channel"""
        try:
            # Get the first message for text
            first_msg = messages[0]
            
            # Clean the text by removing links
            cleaned_text = self.clean_text(first_msg.text)
            
            # Translate the cleaned text
            translated_caption = await self.translate_text(cleaned_text)
            
            # Collect all media files
            media_files = []
            for msg in messages:
                if msg.media:
                    media_files.append(msg.media)
            
            if media_files:
                # Send as album with translated caption
                await self.client.send_file(
                    destination,
                    media_files,
                    caption=translated_caption
                )
                logger.info(f"Successfully sent album ({len(media_files)} items) from {self.source_channel} to {self.destination_channel}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to send grouped media: {e}")
            return False

    async def send_custom_message(self, original_message):
        """Send message with translated content"""
        try:
            destination = await self.get_channel_entity(self.destination_channel)
            if not destination:
                logger.error(f"Could not find destination channel: {self.destination_channel}")
                return False
            
            # Clean the text by removing links
            cleaned_text = self.clean_text(original_message.text)
            
            # Translate the cleaned text
            translated_text = await self.translate_text(cleaned_text)
            
            # Handle messages with media
            if original_message.media:
                # Send media with translated text as caption
                await self.client.send_file(
                    destination, 
                    original_message.media,
                    caption=translated_text,
                    force_document=False,  # Let Telegram decide the best format
                    supports_streaming=True  # For videos
                )
                logger.info(f"Successfully sent media from {self.source_channel} to {self.destination_channel}")
            else:
                # Text-only message
                if translated_text:
                    await self.client.send_message(destination, translated_text)
                    logger.info(f"Successfully sent text message from {self.source_channel} to {self.destination_channel}")
                else:
                    logger.info("Message contained only links - skipping")
                    return True  # Consider this successful since we intentionally skip link-only messages
            
            return True
            
        except FloodWaitError as e:
            logger.warning(f"Rate limit hit. Waiting {e.seconds} seconds...")
            await asyncio.sleep(e.seconds)
            return False
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return False
    
    async def start_monitoring(self, use_forwarding=True):
        """Start monitoring the source channel for new messages"""
        try:
            await self.authenticate()
            
            source = await self.get_channel_entity(self.source_channel)
            if not source:
                logger.error(f"Could not find source channel: {self.source_channel}")
                return
            
            logger.info(f"Starting to monitor {self.source_channel} for new posts...")
            logger.info(f"Messages will be {'forwarded' if use_forwarding else 'sent as custom messages'} to {self.destination_channel}")
            
            # Track grouped messages (albums)
            grouped_messages = {}
            
            @self.client.on(events.NewMessage(chats=source))
            async def handle_new_message(event):
                message = event.message
                
                # Handle grouped media (albums)
                if message.grouped_id:
                    if message.grouped_id not in grouped_messages:
                        grouped_messages[message.grouped_id] = []
                        # Set a timer to process the group after a short delay
                        async def process_group():
                            await asyncio.sleep(1)  # Wait for all messages in group
                            if message.grouped_id in grouped_messages:
                                group = grouped_messages.pop(message.grouped_id)
                                if group:
                                    logger.info(f"New album detected in {self.source_channel} with {len(group)} items")
                                    if use_forwarding:
                                        # Forward each message in the group
                                        for msg in group:
                                            await self.forward_message(msg)
                                    else:
                                        # Send as custom album
                                        destination = await self.get_channel_entity(self.destination_channel)
                                        if destination:
                                            await self.handle_grouped_media(group, destination)
                        
                        asyncio.create_task(process_group())
                    
                    grouped_messages[message.grouped_id].append(message)
                else:
                    # Single message (not part of an album)
                    logger.info(f"New message detected in {self.source_channel}: {message.text[:100] if message.text else 'Media message'}...")
                    
                    if use_forwarding:
                        success = await self.forward_message(message)
                    else:
                        success = await self.send_custom_message(message)
                    
                    if success:
                        logger.info("Message processed successfully!")
                    else:
                        logger.warning("Failed to process message")
            
            # Keep the client running
            logger.info("Monitor is running. Press Ctrl+C to stop.")
            await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error during monitoring: {e}")
        finally:
            await self.client.disconnect()

async def main():
    """Main function to run the monitor"""
    try:
        monitor = TelegramChannelMonitor()
        
        # You can choose between forwarding or custom messages
        # use_forwarding=True: Forward original messages (requires admin rights in destination)
        # use_forwarding=False: Send custom formatted messages
        await monitor.start_monitoring(use_forwarding=False)
        
    except Exception as e:
        logger.error(f"Application error: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 
