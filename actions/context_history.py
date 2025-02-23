def get_openai_context(tracker, max_interactions: int = 4) -> list:
    """
    Extracts the most recent user-bot message pairs in chronological order
    and formats them for OpenAI's API, including the latest user input.

    Args:
        tracker: Rasa tracker object
        max_interactions: Number of message pairs to include (default: 3)

    Returns:
        List of messages in OpenAI format with proper user-assistant pairing
    """
    events = list(tracker.events)
    messages = []
    pending_user_message = None

    # Track pairs in chronological order
    interaction_pairs = []

    # Process events as they occurred (oldest to newest)
    for event in events:
        if event.get("event") == "user":
            # Store user message until we find matching bot response
            pending_user_message = event.get("text", "")
        elif event.get("event") == "bot" and pending_user_message:
            # Found a complete interaction pair
            interaction_pairs.append(
                (pending_user_message, event.get("text", ""))
            )
            pending_user_message = None

    # Add the latest unpaired user message if present
    if pending_user_message:
        interaction_pairs.append((pending_user_message, None))

    # Get the most recent interactions (last N pairs)
    recent_interactions = interaction_pairs[-max_interactions:]

    # Format for OpenAI API (maintain chronological order)
    for user_msg, bot_msg in recent_interactions:
        if bot_msg is not None:
            messages.append({"role": "user", "content": user_msg})
            messages.append({"role": "assistant", "content": bot_msg})

    return messages