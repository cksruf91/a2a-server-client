import json
import uuid
from typing import Generator

import httpx
import streamlit as st

# Page configuration
st.set_page_config(
    page_title="Travel Assistant Chat",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
API_BASE_URL = "http://localhost:8080"
STREAM_ENDPOINT = f"{API_BASE_URL}/chat/stream"


def initialize_session_state():
    """Initialize Streamlit session state"""
    if "chat_rooms" not in st.session_state:
        st.session_state.chat_rooms = {}
    if "current_room_id" not in st.session_state:
        st.session_state.current_room_id = None
    if "room_names" not in st.session_state:
        st.session_state.room_names = {}
    if "room_task_ids" not in st.session_state:
        st.session_state.room_task_ids = {}
    if "room_user_ids" not in st.session_state:
        st.session_state.room_user_ids = {}


def create_new_room(room_name: str = None) -> str:
    """Create a new chat room"""
    room_id = str(uuid.uuid4())
    user_id = str(uuid.uuid4())
    if room_name is None:
        room_name = f"Chat {len(st.session_state.chat_rooms) + 1}"

    st.session_state.chat_rooms[room_id] = []
    st.session_state.room_names[room_id] = room_name
    st.session_state.room_user_ids[room_id] = user_id
    st.session_state.current_room_id = room_id
    return room_id


def delete_room(room_id: str):
    """Delete a chat room"""
    if room_id in st.session_state.chat_rooms:
        del st.session_state.chat_rooms[room_id]
        del st.session_state.room_names[room_id]
        if room_id in st.session_state.room_task_ids:
            del st.session_state.room_task_ids[room_id]
        if room_id in st.session_state.room_user_ids:
            del st.session_state.room_user_ids[room_id]

        # Set current room to another room or None
        if st.session_state.chat_rooms:
            st.session_state.current_room_id = list(st.session_state.chat_rooms.keys())[0]
        else:
            st.session_state.current_room_id = None


def delete_message(room_id: str, message_index: int):
    """Delete a specific message from a chat room"""
    if room_id in st.session_state.chat_rooms:
        if 0 <= message_index < len(st.session_state.chat_rooms[room_id]):
            st.session_state.chat_rooms[room_id].pop(message_index)


def parse_sse_event(line: str) -> tuple[str, str]:
    """Parse SSE event line"""
    if line.startswith("event:"):
        return "event", line[6:].strip()
    elif line.startswith("data:"):
        return "data", line[5:].strip()
    return None, None


def stream_chat_response(question: str, room_id: str, user_id: str, task_id: str = None) -> Generator[
    tuple[str, str, str, bool], None, None]:
    """Stream chat response from the API

    Yields:
        tuple[event_type, content, task_id, require_user_input]:
            Event type ('working', 'streaming', 'error'), content, task_id, and require_user_input flag
    """
    payload = {
        "question": question,
        "roomId": room_id,
        "userId": user_id
    }

    # Add taskId to payload if it exists
    if task_id:
        payload["taskId"] = task_id

    print(f"payload: {payload}")

    received_task_id = None
    require_user_input = False

    try:
        with httpx.Client(timeout=60.0) as client:
            with client.stream("POST", STREAM_ENDPOINT, json=payload) as response:
                response.raise_for_status()

                current_event = None
                for line in response.iter_lines():
                    line = line.strip()
                    if not line:
                        continue

                    field, value = parse_sse_event(line)

                    if field == "event":
                        current_event = value
                    elif field == "data":
                        try:
                            data = json.loads(value)
                        except json.JSONDecodeError:
                            continue

                        # Extract task_id from top level
                        if "task_id" in data:
                            received_task_id = data["task_id"]

                        # Extract contents object
                        contents = data.get("contents", {})

                        # Extract require_user_input from contents (default to False if not present)
                        if isinstance(contents, dict) and "require_user_input" in contents:
                            require_user_input = contents["require_user_input"]

                        # Extract response from contents
                        display_content = None
                        if isinstance(contents, dict) and "response" in contents:
                            display_content = contents["response"]
                        elif isinstance(contents, str):
                            # Fallback: if contents is a string, use it directly
                            display_content = contents

                        if display_content:
                            if current_event == "working":
                                yield "working", display_content, received_task_id, require_user_input
                            elif current_event == "streaming":
                                yield "streaming", display_content, received_task_id, require_user_input

                        if current_event == "Done":
                            break

    except Exception as e:
        yield "error", f"❌ Error: {str(e)}", received_task_id, False


def render_sidebar():
    """Render the sidebar with chat room management"""
    with st.sidebar:
        st.title("🌍 Travel Assistant")
        st.divider()

        # New chat button
        col1, col2 = st.columns([3, 1])
        with col1:
            new_room_name = st.text_input(
                "New chat name",
                placeholder="Enter chat name...",
                label_visibility="collapsed",
                key="new_room_name_input"
            )
        with col2:
            if st.button("➕", help="Create new chat", use_container_width=True):
                create_new_room(new_room_name if new_room_name else None)
                st.rerun()

        st.divider()

        # Chat room list
        if st.session_state.chat_rooms:
            st.subheader("Chat Rooms")

            for room_id in list(st.session_state.chat_rooms.keys()):
                room_name = st.session_state.room_names.get(room_id, "Unnamed Chat")
                message_count = len(st.session_state.chat_rooms[room_id])

                col1, col2 = st.columns([4, 1])

                with col1:
                    # Room selection button
                    is_current = room_id == st.session_state.current_room_id
                    button_type = "primary" if is_current else "secondary"

                    if st.button(
                            f"💬 {room_name} ({message_count})",
                            key=f"room_{room_id}",
                            type=button_type,
                            use_container_width=True
                    ):
                        st.session_state.current_room_id = room_id
                        st.rerun()

                with col2:
                    # Delete room button
                    if st.button("🗑️", key=f"delete_room_{room_id}", help="Delete chat room"):
                        delete_room(room_id)
                        st.rerun()
        else:
            st.info("No chat rooms yet. Create one to start!")

        st.divider()

        # API status
        with st.expander("🔧 Settings"):
            st.caption(f"API Endpoint: {API_BASE_URL}")
            st.caption(f"Port: 9001")


def render_chat_interface():
    """Render the main chat interface"""
    current_room_id = st.session_state.current_room_id

    if current_room_id is None:
        st.info("👈 Create or select a chat room from the sidebar to start chatting!")
        return

    # Chat room header
    room_name = st.session_state.room_names.get(current_room_id, "Unnamed Chat")
    col1, col2 = st.columns([5, 1])

    with col1:
        st.title(f"💬 {room_name}")

    with col2:
        if st.button("🗑️ Clear All", help="Clear all messages in this chat"):
            st.session_state.chat_rooms[current_room_id] = []
            # Clear task_id for this room when clearing all messages
            if current_room_id in st.session_state.room_task_ids:
                del st.session_state.room_task_ids[current_room_id]
            st.rerun()

    st.divider()

    # Display chat messages
    messages = st.session_state.chat_rooms.get(current_room_id, [])

    for idx, message in enumerate(messages):
        role = message["role"]
        content = message["content"]

        with st.chat_message(role):
            col1, col2 = st.columns([20, 1])
            with col1:
                st.markdown(content)
            with col2:
                if st.button("🗑️", key=f"delete_msg_{current_room_id}_{idx}", help="Delete this message"):
                    delete_message(current_room_id, idx)
                    st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about travel destinations..."):
        # Add user message
        st.session_state.chat_rooms[current_room_id].append({
            "role": "user",
            "content": prompt
        })

        # Display user message
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get assistant response
        with st.chat_message("assistant"):
            # Use a single container for the entire response
            response_container = st.container()

            full_response = ""
            is_streaming = False
            received_task_id = None
            require_user_input = False

            # Get existing task_id for this room (if any)
            existing_task_id = st.session_state.room_task_ids.get(current_room_id)
            # Get user_id for this room
            user_id = st.session_state.room_user_ids.get(current_room_id)

            try:
                with response_container:
                    message_placeholder = st.empty()

                    for event_type, content, task_id, req_input in stream_chat_response(prompt, current_room_id,
                                                                                        user_id, existing_task_id):
                        # Store the task_id and require_user_input if received
                        if task_id and not received_task_id:
                            received_task_id = task_id
                        # Update require_user_input flag
                        require_user_input = req_input

                        if event_type == "working":
                            # Display working message in gray with task_id
                            if not is_streaming:
                                working_msg = f"task({task_id}) - working" if task_id else "working"
                                message_placeholder.markdown(
                                    f'<span style="color: gray;">{working_msg}</span>',
                                    unsafe_allow_html=True
                                )

                        elif event_type == "streaming":
                            # Mark that streaming has started
                            is_streaming = True

                            # Display streaming response in black (permanent)
                            full_response = content
                            message_placeholder.markdown(full_response + "▌")

                        elif event_type == "error":
                            is_streaming = True
                            message_placeholder.error(content)
                            full_response = content

                    # Remove cursor after completion
                    if full_response:
                        message_placeholder.markdown(full_response)

                # Handle task_id based on require_user_input
                if require_user_input and received_task_id:
                    # Save the task_id for this room if require_user_input is true
                    st.session_state.room_task_ids[current_room_id] = received_task_id
                else:
                    # Clear the task_id for this room if require_user_input is false or missing
                    if current_room_id in st.session_state.room_task_ids:
                        del st.session_state.room_task_ids[current_room_id]

                # Add assistant message to history
                if full_response:
                    st.session_state.chat_rooms[current_room_id].append({
                        "role": "assistant",
                        "content": full_response
                    })

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                with response_container:
                    st.error(error_msg)
                st.session_state.chat_rooms[current_room_id].append({
                    "role": "assistant",
                    "content": error_msg
                })


def main():
    """Main application entry point"""
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main chat interface
    render_chat_interface()


if __name__ == "__main__":
    main()
