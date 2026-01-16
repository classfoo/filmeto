"""
Simple test to verify logging functionality
"""
import logging
import sys

# Set up logging to see if our changes work
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Test the utility functions
from agent.utils import create_text_message, create_error_message, create_system_message

print("Testing logging for utility functions...")

# This should trigger logging
text_msg = create_text_message("Test text message content", "test_sender", "Test Sender")
error_msg = create_error_message("Test error message", "error_sender", "Error Sender")
system_msg = create_system_message("Test system message")

print(f"Messages created: {text_msg.message_id}, {error_msg.message_id}, {system_msg.message_id}")