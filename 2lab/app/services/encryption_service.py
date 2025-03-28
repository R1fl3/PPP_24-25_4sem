
import heapq
import base64
from collections import Counter
from typing import Dict, Tuple

class Node:
    def __init__(self, char=None, freq=0):
        self.char = char
        self.freq = freq
        self.left = None
        self.right = None

    def __lt__(self, other):
        return self.freq < other.freq

def build_huffman_tree(text: str) -> Node:
    frequency = Counter(text)
    heap = [Node(char, freq) for char, freq in frequency.items()]
    heapq.heapify(heap)
    while len(heap) > 1:
        node1 = heapq.heappop(heap)
        node2 = heapq.heappop(heap)
        merged = Node(freq=node1.freq + node2.freq)
        merged.left = node1
        merged.right = node2
        heapq.heappush(heap, merged)
    return heap[0]

def generate_codes(node: Node, prefix="", code_map=None) -> Dict[str, str]:
    if code_map is None:
        code_map = {}
    if node.char is not None:
        code_map[node.char] = prefix
    else:
        generate_codes(node.left, prefix + "0", code_map)
        generate_codes(node.right, prefix + "1", code_map)
    return code_map

def huffman_encode(text: str) -> Tuple[str, Dict[str, str], int]:
    tree = build_huffman_tree(text)
    code_map = generate_codes(tree)
    encoded_bits = ''.join(code_map[char] for char in text)
    padding = 8 - len(encoded_bits) % 8 if len(encoded_bits) % 8 != 0 else 0
    encoded_bits += '0' * padding
    b = bytearray()
    for i in range(0, len(encoded_bits), 8):
        byte = encoded_bits[i:i+8]
        b.append(int(byte, 2))
    return base64.b64encode(bytes(b)).decode(), code_map, padding

def huffman_decode(encoded_data: str, code_map: Dict[str, str], padding: int) -> str:
    reverse_map = {v: k for k, v in code_map.items()}
    binary_data = ''.join(f"{byte:08b}" for byte in base64.b64decode(encoded_data))
    binary_data = binary_data[:-padding] if padding else binary_data
    current_code = ""
    decoded_text = ""
    for bit in binary_data:
        current_code += bit
        if current_code in reverse_map:
            decoded_text += reverse_map[current_code]
            current_code = ""
    return decoded_text

def xor_encrypt(data: bytes, key: str) -> bytes:
    key_bytes = key.encode()
    return bytes([b ^ key_bytes[i % len(key_bytes)] for i, b in enumerate(data)])

def encode_text(text: str, key: str):
    huff_encoded, code_map, padding = huffman_encode(text)
    raw_bytes = base64.b64decode(huff_encoded)
    xor_encrypted = xor_encrypt(raw_bytes, key)
    encoded_final = base64.b64encode(xor_encrypted).decode()
    return {
        "encoded_data": encoded_final,
        "key": key,
        "huffman_codes": code_map,
        "padding": padding
    }

def decode_text(encoded_data: str, key: str, huffman_codes: Dict[str, str], padding: int):
    encrypted_bytes = base64.b64decode(encoded_data)
    decrypted_bytes = xor_encrypt(encrypted_bytes, key)
    huff_encoded = base64.b64encode(decrypted_bytes).decode()
    decoded_text = huffman_decode(huff_encoded, huffman_codes, padding)
    return {"decoded_text": decoded_text}
