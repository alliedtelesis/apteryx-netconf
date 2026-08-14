import socket
import os
import select
import re

# Must match MAX_REQUEST_MESSAGE_SIZE in netconf.c
MAX_REQUEST_MESSAGE_SIZE = 32768


def _recv_until(sock, terminator, timeout=2):
    """
    Read from sock until terminator has been seen. A single recv() call
    isn't guaranteed to return a whole message - the server's hello can
    exceed 4096 bytes once enough schema/models are loaded.
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


def test_aggregate_message_too_big():
    """
    receive_message() must reject a request whose size, summed across all
    chunks, exceeds MAX_REQUEST_MESSAGE_SIZE - even when no single chunk
    exceeds it on its own. Send two chunks that are each individually under
    the limit but together are over it, and confirm the second chunk's
    header is rejected with a "too-big" rpc-error rather than being
    accepted (which would let a client grow a request without bound by
    never sending the "\n##\n" end-of-message marker).
    """
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = _connect_and_hello(unix_path)

    # Two chunks, each comfortably under MAX_REQUEST_MESSAGE_SIZE on its
    # own, but summing to more than it. The first is accepted and its
    # payload consumed; the second chunk's header alone should be enough
    # to trigger rejection, so we never need to send its payload.
    chunk1_len = MAX_REQUEST_MESSAGE_SIZE - 4000
    chunk2_len = MAX_REQUEST_MESSAGE_SIZE - 4000
    assert chunk1_len < MAX_REQUEST_MESSAGE_SIZE
    assert chunk2_len < MAX_REQUEST_MESSAGE_SIZE
    assert chunk1_len + chunk2_len > MAX_REQUEST_MESSAGE_SIZE

    sock.send('\n#{0}\n'.format(chunk1_len).encode() + b'A' * chunk1_len)
    sock.send('\n#{0}\n'.format(chunk2_len).encode())

    result = _recv_until(sock, b'\n##\n').decode('utf-8')
    sock.close()
    assert 'too-big' in result


def test_multi_chunk_message_within_limit():
    """
    A legal request split across multiple chunks whose total is
    comfortably under MAX_REQUEST_MESSAGE_SIZE must still be accepted and
    processed normally.
    """
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = _connect_and_hello(unix_path)

    # Same <nc:get/> request as test_hello.py's single-chunk case, but
    # split across three small chunks - well under the limit individually
    # and in total - to prove legal multi-chunk requests still work.
    rpc_xml = '<?xml version="1.0" encoding="UTF-8"?><nc:rpc ' \
              'xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" ' \
              'message-id="urn:uuid:6f6b6f6b-0000-0000-0000-000000000000">' \
              '<nc:get/></nc:rpc>'
    third = len(rpc_xml) // 3
    parts = [rpc_xml[:third], rpc_xml[third:2 * third], rpc_xml[2 * third:]]
    assert sum(len(p) for p in parts) < MAX_REQUEST_MESSAGE_SIZE

    for part in parts:
        chunk = part.encode()
        sock.send('\n#{0}\n'.format(len(chunk)).encode() + chunk)
    sock.send(b'\n##\n')

    result = _recv_until(sock, b'\n##\n').decode('utf-8')
    sock.close()
    assert 'rpc-reply' in result
    assert 'urn:uuid:6f6b6f6b-0000-0000-0000-000000000000' in result


def test_get_config_empty_source():
    """
    An empty <source/> element must not crash the daemon (CR-91412).

    get_process_action() crashed by calling xmlFirstElementChild(node)->name
    a second time without checking if the first call returned NULL.

    This test confirms the fix: an empty <source/> now produces a normal
    rpc-error, and the session stays alive and responsive afterwards.
    """
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = _connect_and_hello(unix_path)

    rpc_xml = '<?xml version="1.0" encoding="UTF-8"?><nc:rpc ' \
              'xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" ' \
              'message-id="urn:uuid:aaaaaaaa-0000-0000-0000-000000000000">' \
              '<nc:get-config><nc:source/></nc:get-config></nc:rpc>'
    chunk = rpc_xml.encode()
    sock.send('\n#{0}\n'.format(len(chunk)).encode() + chunk)
    sock.send(b'\n##\n')

    result = _recv_until(sock, b'\n##\n').decode('utf-8')
    assert 'rpc-error' in result
    assert 'urn:uuid:aaaaaaaa-0000-0000-0000-000000000000' in result

    # Confirm the daemon is still alive: a second, well-formed request on
    # the same session must still get a normal reply.
    rpc_xml2 = '<?xml version="1.0" encoding="UTF-8"?><nc:rpc ' \
               'xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" ' \
               'message-id="urn:uuid:bbbbbbbb-0000-0000-0000-000000000000">' \
               '<nc:get/></nc:rpc>'
    chunk2 = rpc_xml2.encode()
    sock.send('\n#{0}\n'.format(len(chunk2)).encode() + chunk2)
    sock.send(b'\n##\n')

    result2 = _recv_until(sock, b'\n##\n').decode('utf-8')
    sock.close()
    assert 'rpc-reply' in result2
    assert 'urn:uuid:bbbbbbbb-0000-0000-0000-000000000000' in result2
