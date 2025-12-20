"""Raw protobuf encoder for Antigravity Connect-RPC without .proto files.

This module provides raw protobuf binary encoding for Connect-RPC calls
to Antigravity's jetski agent service.
"""

import struct
from typing import Dict, Any, List, Optional
from io import BytesIO


def encode_varint(value: int) -> bytes:
    """Encode a varint (variable-length integer)."""
    result = []
    while value > 127:
        result.append((value & 0x7F) | 0x80)
        value >>= 7
    result.append(value)
    return bytes(result)


def encode_field(field_number: int, wire_type: int, data: bytes) -> bytes:
    """Encode a protobuf field with its tag."""
    tag = (field_number << 3) | wire_type
    return encode_varint(tag) + data


def encode_string(field_number: int, value: str) -> bytes:
    """Encode a string field (wire type 2)."""
    encoded = value.encode('utf-8')
    return encode_field(field_number, 2, encode_varint(len(encoded)) + encoded)


def encode_bytes_field(field_number: int, value: bytes) -> bytes:
    """Encode a bytes field (wire type 2)."""
    return encode_field(field_number, 2, encode_varint(len(value)) + value)


def encode_int32(field_number: int, value: int) -> bytes:
    """Encode an int32 field (wire type 0)."""
    return encode_field(field_number, 0, encode_varint(value))


def encode_bool(field_number: int, value: bool) -> bytes:
    """Encode a bool field (wire type 0)."""
    return encode_field(field_number, 0, encode_varint(1 if value else 0))


def encode_embedded_message(field_number: int, message_bytes: bytes) -> bytes:
    """Encode an embedded message field (wire type 2)."""
    return encode_field(field_number, 2, encode_varint(len(message_bytes)) + message_bytes)


class ClientMetadata:
    """Encodes ClientMetadata protobuf message.
    
    Based on: google.internal.cloud.code.v1internal.ClientMetadata
    Fields from JS analysis:
    - ide_version (string) = field 1
    - ide_name (string) = field 9
    - ide_type (enum) = field 10 (guess based on pattern)
    """
    
    @staticmethod
    def encode(
        ide_name: str = "antigravity",
        ide_version: str = "1.0.0",
        ide_type: int = 2  # ANTIGRAVITY enum value (guess)
    ) -> bytes:
        result = BytesIO()
        result.write(encode_string(1, ide_version))
        result.write(encode_string(9, ide_name))
        result.write(encode_int32(10, ide_type))
        return result.getvalue()


class ChatMessage:
    """Encodes a chat message for the jetski agent.
    
    This is a best-guess structure based on JS analysis.
    Fields likely include: content, role, etc.
    """
    
    @staticmethod
    def encode(
        content: str,
        role: str = "user"  # or "model" for assistant
    ) -> bytes:
        result = BytesIO()
        result.write(encode_string(1, content))
        result.write(encode_string(2, role))
        return result.getvalue()


class CascadeRequest:
    """Encodes a CascadeRequest protobuf message.
    
    Based on analysis of exa.jetski_cortex_pb namespace.
    This is the request sent to start/continue a cascade (agent) conversation.
    """
    
    @staticmethod
    def encode(
        message: str,
        model_id: str = "gemini-3-pro-high",
        metadata: Optional[bytes] = None,
        project: str = ""
    ) -> bytes:
        result = BytesIO()
        
        # Field 1: User message
        result.write(encode_string(1, message))
        
        # Field 2: Model ID
        result.write(encode_string(2, model_id))
        
        # Field 3: Client metadata (embedded message)
        if metadata:
            result.write(encode_embedded_message(3, metadata))
        else:
            result.write(encode_embedded_message(3, ClientMetadata.encode()))
        
        # Field 4: Project (cloudaicompanion project)
        if project:
            result.write(encode_string(4, project))
        
        return result.getvalue()


def encode_connect_rpc_message(message_bytes: bytes) -> bytes:
    """Encode a message for Connect-RPC binary format.
    
    Connect-RPC uses a 5-byte envelope:
    - 1 byte: flags (0 = uncompressed)
    - 4 bytes: message length (big-endian)
    """
    flags = 0  # Uncompressed
    length = len(message_bytes)
    envelope = struct.pack('>BI', flags, length)
    return envelope + message_bytes


def decode_connect_rpc_envelope(data: bytes) -> tuple:
    """Decode a Connect-RPC envelope.
    
    Returns: (flags, message_bytes)
    """
    if len(data) < 5:
        return None, None
    flags = data[0]
    length = struct.unpack('>I', data[1:5])[0]
    message = data[5:5 + length]
    return flags, message


# Model ID mapping
ANTIGRAVITY_MODEL_IDS = {
    'gemini-3-pro': 'gemini-3-pro-high',
    'gemini-3-flash': 'gemini-3-flash',
    'claude-sonnet-4.5': 'claude-sonnet-4-5',
    'claude-sonnet-4.5-thinking': 'claude-sonnet-4-5-thinking',
    'claude-opus-4.5': 'claude-opus-4-5-thinking',
    'gpt-oss-120b': 'gpt-oss-120b-medium',
}


def get_model_id(friendly_name: str) -> str:
    """Convert friendly model name to Antigravity API model ID."""
    name_lower = friendly_name.lower().replace('antigravity/', '')
    return ANTIGRAVITY_MODEL_IDS.get(name_lower, name_lower)


if __name__ == '__main__':
    # Test encoding
    metadata = ClientMetadata.encode()
    print(f"Metadata bytes: {metadata.hex()}")
    
    request = CascadeRequest.encode(
        message="Hello, can you help me?",
        model_id="gemini-3-pro-high"
    )
    print(f"Request bytes: {request.hex()}")
    
    envelope = encode_connect_rpc_message(request)
    print(f"Envelope bytes: {envelope.hex()}")
