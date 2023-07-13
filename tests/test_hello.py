import socket
import os
import select


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


def test_connect_hello_feature():
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
        assert (result.find('module=example&amp;revision=2023-04-04&amp;features=ether,fast') > 0)
    else:
        sock.close()
        assert (False)


def test_connect_hello_deviation():
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
        assert (result.find('amp;deviations=user-example-deviation') > 0)
    else:
        sock.close()
        assert (False)
