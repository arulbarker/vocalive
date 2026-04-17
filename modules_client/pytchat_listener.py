import json
import logging
import threading
import time

import pytchat
from pytchat import exceptions as pytchat_exceptions

# Setup logging
logger = logging.getLogger(__name__)

# THREAD SYNCHRONIZATION FIX: Add thread locks for shared variables
_message_lock = threading.Lock()
_listener_lock = threading.Lock()

# Variabel global untuk menyimpan pesan terbaru (untuk Delay mode)
# THREAD SYNCHRONIZATION FIX: Protected by _message_lock
latest_message = {"username": None, "message": None}

# Global flag untuk menghentikan listener
_stop_listener = False

def start_pytchat_listener(video_id, callback):
    global _stop_listener
    _stop_listener = False

    try:
        # Enhanced pytchat creation with error handling
        chat = pytchat.create(
            video_id=video_id,
            interruptable=True,
            hold_exception=True
        )

        # Muat konfigurasi reply mode dari file config dengan error handling
        try:
            with open("config/live_state.json", "r", encoding='utf-8') as f:
                config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Config file error: {e}, using defaults")
            config = {}

        reply_mode = config.get("reply_mode", "Trigger")
        delay_seconds = config.get("delay_seconds", 5)
        custom_trigger = config.get("custom_cohost_name", "").strip().lower()

        logger.info(f"Starting pytchat listener for video {video_id} in {reply_mode} mode")

    except Exception as e:
        logger.error(f"Failed to initialize pytchat listener: {e}")
        return None

    def process_delay_mode():
        # Loop terpisah untuk mode Delay
        while not _stop_listener:
            time.sleep(delay_seconds)

            # THREAD SYNCHRONIZATION FIX: Use lock for accessing shared variable
            with _message_lock:
                if latest_message["message"] and not _stop_listener:
                    # Copy message data to avoid race conditions
                    username = latest_message["username"]
                    message = latest_message["message"]
                    # Reset pesan setelah diproses
                    latest_message["username"] = None
                    latest_message["message"] = None
                else:
                    username = None
                    message = None

            # Process message outside the lock to prevent deadlock
            if username and message and not _stop_listener:
                try:
                    callback(username, message)
                except Exception as cb_error:
                    logger.error(f"Callback error in delay mode: {cb_error}")

    if reply_mode == "Delay":
        # Mulai thread untuk memproses Delay mode
        threading.Thread(target=process_delay_mode, daemon=True).start()

    def run():
        retry_count = 0
        max_retries = 5

        while not _stop_listener:
            try:
                # Check if chat is still alive
                if not chat.is_alive():
                    logger.warning("Chat connection lost, attempting to reconnect...")
                    break

                # Check for exceptions in pytchat
                try:
                    chat.raise_for_status()
                except Exception as chat_error:
                    logger.error(f"Pytchat error: {chat_error}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error("Max retries exceeded, stopping listener")
                        break
                    time.sleep(2 ** retry_count)  # Exponential backoff
                    continue

                # Process chat messages with error handling
                try:
                    chat_items = chat.get().sync_items()
                    for c in chat_items:
                        if _stop_listener:
                            break

                        try:
                            username = c.author.name if c.author else "Unknown"
                            message = c.message if c.message else ""

                            if not username or not message:
                                continue

                            # Process based on reply mode
                            if reply_mode == "Trigger":
                                if custom_trigger and custom_trigger in message.lower():
                                    callback(username, message)
                            elif reply_mode == "Delay":
                                # THREAD SYNCHRONIZATION FIX: Use lock for updating shared variable
                                with _message_lock:
                                    latest_message["username"] = username
                                    latest_message["message"] = message
                            elif reply_mode == "Sequential":
                                callback(username, message)
                            else:
                                # Default: Trigger mode
                                if custom_trigger and custom_trigger in message.lower():
                                    callback(username, message)

                        except Exception as msg_error:
                            logger.error(f"Error processing message: {msg_error}")
                            continue

                except pytchat_exceptions.ChatParseException as parse_error:
                    logger.warning(f"Chat parse error: {parse_error}")
                    time.sleep(1)
                    continue
                except pytchat_exceptions.RetryExceedMaxCount as retry_error:
                    logger.error(f"Network retry exceeded: {retry_error}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        break
                    time.sleep(5)
                    continue
                except Exception as general_error:
                    logger.error(f"Unexpected error in chat processing: {general_error}")
                    retry_count += 1
                    if retry_count >= max_retries:
                        break
                    time.sleep(2)
                    continue

                # Reset retry count on successful iteration
                retry_count = 0
                time.sleep(0.5)  # Prevent CPU overload

            except Exception as outer_error:
                logger.error(f"Critical error in pytchat listener: {outer_error}")
                break

        # Cleanup
        try:
            if chat and chat.is_alive():
                chat.terminate()
                logger.info("Pytchat listener terminated gracefully")
        except Exception as cleanup_error:
            logger.error(f"Error during pytchat cleanup: {cleanup_error}")

    thread = threading.Thread(target=run, daemon=True)
    thread.start()
    return thread

def stop_pytchat_listener():
    """Stop the pytchat listener gracefully with thread synchronization"""
    global _stop_listener

    # THREAD SYNCHRONIZATION FIX: Use lock to prevent race conditions
    with _listener_lock:
        if not _stop_listener:  # Avoid multiple stop requests
            _stop_listener = True
            logger.info("Pytchat listener stop requested")

            # SYNCHRONIZATION FIX: Clear latest_message to prevent stale data
            with _message_lock:
                latest_message["username"] = None
                latest_message["message"] = None
                logger.debug("Latest message cleared during shutdown")
        else:
            logger.debug("Pytchat listener stop already requested")

