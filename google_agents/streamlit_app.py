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


def create_new_room(room_name: str = None) -> str:
    """Create a new chat room"""
    room_id = str(uuid.uuid4())
    if room_name is None:
        room_name = f"Chat {len(st.session_state.chat_rooms) + 1}"

    st.session_state.chat_rooms[room_id] = []
    st.session_state.room_names[room_id] = room_name
    st.session_state.current_room_id = room_id
    return room_id


def delete_room(room_id: str):
    """Delete a chat room"""
    if room_id in st.session_state.chat_rooms:
        del st.session_state.chat_rooms[room_id]
        del st.session_state.room_names[room_id]

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


def stream_chat_response(question: str, room_id: str) -> Generator[tuple[str, str], None, None]:
    """Stream chat response from the API

    Yields:
        tuple[event_type, content]: Event type ('working', 'streaming', 'error') and content
    """
    payload = {
        "question": question,
        "roomId": room_id
    }

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
                            if "contents" in data and data["contents"]:
                                if current_event == "working":
                                    yield ("working", data["contents"])
                                elif current_event == "streaming":
                                    yield ("streaming", data["contents"])
                        except json.JSONDecodeError:
                            continue

                        if current_event == "Done":
                            break

    except Exception as e:
        yield ("error", f"❌ Error: {str(e)}")


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
            # Placeholder for working status (temporary, will be cleared)
            working_placeholder = st.empty()
            # Placeholder for final response (permanent)
            response_placeholder = st.empty()

            full_response = ""
            current_working_msg = ""

            try:
                for event_type, content in stream_chat_response(prompt, current_room_id):
                    if event_type == "working":
                        # Display working message in gray (temporary)
                        current_working_msg = content
                        working_placeholder.markdown(
                            f'<span style="color: gray;">{current_working_msg}</span>',
                            unsafe_allow_html=True
                        )

                    elif event_type == "streaming":
                        # Clear working message when streaming starts
                        working_placeholder.empty()

                        # Display streaming response in black (permanent)
                        full_response = content
                        response_placeholder.markdown(full_response + "▌")

                    elif event_type == "error":
                        working_placeholder.empty()
                        response_placeholder.error(content)
                        full_response = content

                # Remove cursor after completion
                if full_response:
                    response_placeholder.markdown(full_response)

                # Add assistant message to history
                if full_response:
                    st.session_state.chat_rooms[current_room_id].append({
                        "role": "assistant",
                        "content": full_response
                    })

            except Exception as e:
                error_msg = f"❌ Error: {str(e)}"
                working_placeholder.empty()
                response_placeholder.error(error_msg)
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
