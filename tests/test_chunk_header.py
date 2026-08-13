import socket
import os
import select
import re

# Must match MAX_CHUNK_HEADER_SIZE in netconf.c
MAX_CHUNK_HEADER_SIZE = 13


def _recv_until(sock, terminator, timeout=2):
    """
    Read from sock until terminator has been seen. A single recv() call
    isn't guaranteed to return a whole message.
    """
    data = b''
    while terminator not in data:
        ready = select.select([sock], [], [], timeout)
        assert ready[0], 'timed out waiting for data'
        chunk = sock.recv(4096)
        assert chunk, 'connection closed unexpectedly'
        data += chunk
    return data


def _connect_and_hello(unix_path):
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(unix_path)
    sock.setblocking(0)
    result = _recv_until(sock, b']]>]]>').decode('utf-8')
    m = re.search('<nc:session-id>(.+?)</nc:session-id>', result)
    assert m
    id = int(m.group(1))

    send_data = '<?xml version="1.0" encoding="UTF-8"?>\n' \
                '<nc:hello xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">' \
                '<nc:capabilities>' \
                '<nc:capability>urn:ietf:params:netconf:base:1.1</nc:capability>' \
                '</nc:capabilities>' \
                '<nc:session-id>{id}</nc:session-id></nc:hello>]]>]]>'.format(id=id)
    sock.send(send_data.encode())
    return sock


def test_malformed_chunk_header_closes_promptly():
    """
    Regression test: read_chunk_size()'s loop bounds check used to stop
    one iteration too late, reading (and NUL-terminating past) a 14th
    header byte - a one-byte stack buffer overflow.

    Send exactly 13 header bytes that never form a legal "\\n#<digits>\\n"
    pattern. Correct behaviour: the server gives up once its 13-byte
    budget is used up and closes the connection promptly. If the off-by-
    one regresses, it instead blocks waiting for a 14th byte that's never
    sent, so the connection stays open past this test's short timeout.
    """
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = _connect_and_hello(unix_path)

    # "\n#" followed by 11 digits, no closing '\n' - a well-formed
    # *prefix* of a chunk header that never completes.
    malformed_header = b'\n#99999999999'
    assert len(malformed_header) == MAX_CHUNK_HEADER_SIZE
    sock.send(malformed_header)

    ready = select.select([sock], [], [], 5)
    assert ready[0], (
        'server did not close the connection promptly after a malformed, '
        'unterminated chunk header - looks like read_chunk_size() is '
        'waiting to read a 14th header byte that should never be read '
        '(regression of the read_chunk_size off-by-one fix)'
    )
    data = sock.recv(4096)
    sock.close()
    assert data == b'', 'expected the server to close the connection (EOF)'


def test_well_formed_chunk_header_at_max_length_still_works():
    """
    A legitimate chunk header that uses the full MAX_CHUNK_HEADER_SIZE (13)
    bytes budget - "\\n#<digits>\\n" with the maximum number of
    chunk-size digits (10, for up to the max uint32 4294967295) - must
    be accepted normally.
    """
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = _connect_and_hello(unix_path)

    rpc_xml = '<?xml version="1.0" encoding="UTF-8"?><nc:rpc ' \
              'xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" ' \
              'message-id="urn:uuid:9f9f9f9f-0000-0000-0000-000000000000">' \
              '<nc:get/></nc:rpc>'
    chunk = rpc_xml.encode()

    # "\n#" + zero-padded 10-digit length + "\n" = 13 bytes, the longest
    # legal chunk header (matches the comment above MAX_CHUNK_HEADER_SIZE
    # in netconf.c: "max chunk-size = 4294967295").
    header = '\n#{0:010d}\n'.format(len(chunk)).encode()
    assert len(header) == MAX_CHUNK_HEADER_SIZE

    sock.send(header + chunk)
    sock.send(b'\n##\n')

    result = _recv_until(sock, b'\n##\n').decode('utf-8')
    sock.close()
    assert 'rpc-reply' in result
    assert 'urn:uuid:9f9f9f9f-0000-0000-0000-000000000000' in result
