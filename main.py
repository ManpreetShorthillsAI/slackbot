import os
from datetime import datetime, timedelta
import slack_sdk
from slack_sdk.errors import SlackApiError
import google.generativeai as genai
from dotenv import load_dotenv
 
# Load environment variables
load_dotenv()
 
# Configuration variables
SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN")
SLACK_APP_TOKEN = os.getenv("SLACK_APP_TOKEN")
SLACK_CHANNEL_ID = os.getenv("SLACK_CHANNEL_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
 
# Validate environment variables
if not all([SLACK_BOT_TOKEN, SLACK_APP_TOKEN, SLACK_CHANNEL_ID, GEMINI_API_KEY]):
    raise ValueError("Missing required environment variables. Please check your .env file.")
 
# Configure Gemini AI
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')
 
class SlackDailySummaryBot:
    def __init__(self):
        # Initialize Slack WebClient for sending messages
        self.slack_client = slack_sdk.WebClient(token=SLACK_BOT_TOKEN)
        
    def get_todays_messages(self, channel_id):
        """
        Retrieve all messages from the current day.
        
        Args:
            channel_id (str): Slack channel ID
        
        Returns:
            list: List of message texts from today
        """
        # Calculate the timestamp for the start of today
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_ts = today_start.timestamp()
        
        try:
            # Fetch conversation history
            result = self.slack_client.conversations_history(
                channel=channel_id,
                oldest=str(today_start_ts)
            )
            
            # Extract message texts, filtering out bot messages and system messages
            messages = [
                msg['text'] for msg in result.get('messages', [])
                if 'text' in msg and not msg.get('bot_id')
            ]
            
            return messages
        
        except SlackApiError as e:
            print(f"Error retrieving messages: {e}")
            return []
    
    def generate_summary(self, messages):
        """
        Generate a summary of the day's messages using Gemini.
        
        Args:
            messages (list): List of message texts
        
        Returns:
            str: Generated summary
        """
        if not messages:
            return "No messages found today."
        
        # Combine messages into a single text block
        messages_text = "\n".join(messages)
        
        prompt = f"""
        You are a professional summarizer. Provide a concise, clear, and objective summary
        of the following conversation and messages from today:
 
        ```
        {messages_text}
        ```
 
        Key requirements for the summary:
        1. Capture the main topics and key points discussed
        2. Identify any important decisions or action items
        3. Be objective and neutral in tone
        4. Limit the summary to 300-500 words
        5. Use clear, professional language
        """
        
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            return f"Error generating summary: {str(e)}"
    
    def post_summary(self, channel_id, summary):
        """
        Post the summary to the Slack channel.
        
        Args:
            channel_id (str): Slack channel ID
            summary (str): Summary text to post
        """
        try:
            self.slack_client.chat_postMessage(
                channel=channel_id,
                text=f"*Daily Channel Summary* 📝\n\n{summary}"
            )
        except SlackApiError as e:
            print(f"Error posting summary: {e}")
 
def main():
    bot = SlackDailySummaryBot()
    
    messages = bot.get_todays_messages(SLACK_CHANNEL_ID)
    summary = bot.generate_summary(messages)
    bot.post_summary(SLACK_CHANNEL_ID, summary)
 
if __name__ == "__main__":
    main()