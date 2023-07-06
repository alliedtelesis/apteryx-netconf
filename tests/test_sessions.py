from conftest import connect
from random import randint
import re
import time
import socket
import os
import select

OK_REGEX_PATTERN = "<nc:ok/>"


def test_multi_close_ok():

    m1 = connect()
    assert (m1.connected is True)

    m2 = connect()
    assert (m2.connected is True)

    m3 = connect()
    assert (m3.connected is True)

    m1.close_session()
    assert (m1.connected is False)

    m2.close_session()
    assert (m2.connected is False)

    m3.close_session()
    assert (m3.connected is False)


def test_close_ok():
    m1 = connect()
    response = None

    response = m1.close_session()
    assert (response.ok is True)
    assert (m1.connected is False)


def test_close_get_fail():

    m1 = connect()
    m1.close_session()
    assert (m1.connected is False)

    try:
        m1.get().data
    except Exception as e:
        assert (e is not None)


def test_kill_valid_ok():

    response = None

    # Create session 1
    m1 = connect()

    # Create session 2
    m2 = connect()

    # From session 1 kill-session 2
    response = m1.kill_session(m2.session_id)
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    # Attempt to make a get request using session 2
    try:
        m2.get().data
    except Exception as e:
        assert (e is not None)

    time.sleep(1)
    assert (m1.connected is True)
    assert (m2.connected is False)

    # Close session 1
    response = None
    response = m1.close_session()
    assert (response.ok is True)
    assert (m1.connected is False)


def test_kill_self_fail():

    # Create session 1
    m1 = connect()

    # From session 1 kill-session 1
    try:
        m1.kill_session(m1.session_id)
    except Exception as e:
        err_msg = "Attempt to kill own session is forbidden"
        assert (err_msg in e.message)
        assert ("invalid-value" in e.tag)

    # Close session 1
    response = None
    response = m1.close_session()
    assert (response.ok is True)


def test_kill_invalid_fail():

    # Create session 1
    m1 = connect()

    # Create session 2
    m2 = connect()

    test_id = 0
    while True:
        test_id = randint(1000, 32768)
        if test_id not in (m1.session_id, m2.session_id):
            break

    test_id_str = "%d" % test_id
    try:
        m1.kill_session(test_id_str)
    except Exception as e:
        assert ("invalid-value" in e.tag)

    # Close session 1
    response = None
    response = m1.close_session()
    assert (response.ok is True)

    # Close session 2
    response = None
    response = m2.close_session()
    assert (response.ok is True)


def test_lock_kill():

    # Create session 1
    m1 = connect()

    # Create session 2
    m2 = connect()

    # Lock session 1
    response = None
    response = m1.lock(target="running")
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    # From session 2, kill session 1
    response = None
    response = m2.kill_session(m1.session_id)
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    time.sleep(1)
    assert (m1.connected is False)

    # Lock session 2
    response = None
    response = m2.lock(target="running")
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    # Unlock session 2
    response = None
    response = m2.unlock(target="running")
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    # Close session 2
    response = None
    response = m2.close_session()
    assert (response.ok is True)


def test_multi_kill():

    # Create session 1
    m1 = connect()
    assert (m1.connected is True)

    # Create session 2
    m2 = connect()
    assert (m2.connected is True)

    # Create session 3
    m3 = connect()
    assert (m3.connected is True)

    # From session 3 kill-session 2
    response = None
    response = m3.kill_session(m2.session_id)
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    # Ensure that session 2 is not connected
    time.sleep(1)
    assert (m1.connected is True)
    assert (m2.connected is False)
    assert (m3.connected is True)

    # From session 1 kill-session 3
    response = None
    response = m1.kill_session(m3.session_id)
    assert (response.ok is True)
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert (match.group() == OK_REGEX_PATTERN)

    # Ensure that session 3 is not connected
    time.sleep(1)
    assert (m1.connected is True)
    assert (m2.connected is False)
    assert (m3.connected is False)

    # Perform get operation using session 1
    xml = m1.get().data
    assert (xml is not None)

    # Close session 1
    response = None
    response = m1.close_session()
    assert (response.ok is True)


def test_connect_hello():
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(unix_path)
    sock.setblocking(0)
    ready = select.select([sock], [], [], 2)
    if ready[0]:
        data = sock.recv(4096)
        sock.close()
        result = data.decode('utf-8')
        assert (result.find('<nc:hello xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">') > 0)
    else:
        sock.close()
        assert (False)
