import socket
import os
import select
import re
import time


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


def test_connect_hello_large_msg():
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(unix_path)
    sock.setblocking(0)
    ready = select.select([sock], [], [], 2)
    if ready[0]:
        send_data = '<?xml version="1.0" encoding="UTF-8"?>\n<nc:hello xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><nc:capabilities>' \
                    '<nc:capability>urn:ietf:params:netconf:base:1.1</nc:capability>' \
                    '<nc:capability>urn:ietf:params:netconf:capability:xpath:1.0</nc:capability>' \
                    '<nc:capability>urn:ietf:params:netconf:capability:writable-running:1.0</nc:capability>' \
                    '<nc:capability>urn:ietf:params:netconf:capability:with-defaults:1.0?basic-mode=explicit&amp;also-supported=report-all,trim</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1ab-types?module=ieee802-dot1ab-types&amp;revision=2022-03-15</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1q-types?module=ieee802-dot1q-types&amp;revision=2020-06-04</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-types?module=ieee802-types&amp;revision=2022-10-29</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-inet-types?module=ietf-inet-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-interfaces?module=ietf-interfaces&amp;revision=2018-02-20</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l2-topology?module=ietf-l2-topology&amp;revision=2020-11-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l3-unicast-topology?module=ietf-l3-unicast-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network-topology?module=ietf-network-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network?module=ietf-network&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-routing-types?module=ietf-routing-types&amp;revision=2017-12-04</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-yang-types?module=ietf-yang-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-ext?module=openconfig-extensions&amp;revision=2022-10-05</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/system?module=openconfig-system&amp;revision=2022-12-20</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-types?module=openconfig-types&amp;revision=2019-04-16</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/types/yang?module=openconfig-yang-types&amp;revision=2021-07-14</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:iana-if-type?module=iana-if-type&amp;revision=2017-01-19</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1ab-types?module=ieee802-dot1ab-types&amp;revision=2022-03-15</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1q-types?module=ieee802-dot1q-types&amp;revision=2020-06-04</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-types?module=ieee802-types&amp;revision=2022-10-29</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-inet-types?module=ietf-inet-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-interfaces?module=ietf-interfaces&amp;revision=2018-02-20</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l2-topology?module=ietf-l2-topology&amp;revision=2020-11-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l3-unicast-topology?module=ietf-l3-unicast-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network-topology?module=ietf-network-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network?module=ietf-network&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-routing-types?module=ietf-routing-types&amp;revision=2017-12-04</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-yang-types?module=ietf-yang-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-ext?module=openconfig-extensions&amp;revision=2022-10-05</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/system?module=openconfig-system&amp;revision=2022-12-20</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-types?module=openconfig-types&amp;revision=2019-04-16</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/types/yang?module=openconfig-yang-types&amp;revision=2021-07-14</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1ab-types?module=ieee802-dot1ab-types&amp;revision=2022-03-15</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1q-types?module=ieee802-dot1q-types&amp;revision=2020-06-04</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-types?module=ieee802-types&amp;revision=2022-10-29</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-inet-types?module=ietf-inet-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-interfaces?module=ietf-interfaces&amp;revision=2018-02-20</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l2-topology?module=ietf-l2-topology&amp;revision=2020-11-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l3-unicast-topology?module=ietf-l3-unicast-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network-topology?module=ietf-network-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network?module=ietf-network&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-routing-types?module=ietf-routing-types&amp;revision=2017-12-04</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-yang-types?module=ietf-yang-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-ext?module=openconfig-extensions&amp;revision=2022-10-05</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/system?module=openconfig-system&amp;revision=2022-12-20</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-types?module=openconfig-types&amp;revision=2019-04-16</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/types/yang?module=openconfig-yang-types&amp;revision=2021-07-14</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:iana-if-type?module=iana-if-type&amp;revision=2017-01-19</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1ab-types?module=ieee802-dot1ab-types&amp;revision=2022-03-15</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1q-types?module=ieee802-dot1q-types&amp;revision=2020-06-04</nc:capability>' \
                    '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-types?module=ieee802-types&amp;revision=2022-10-29</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-inet-types?module=ietf-inet-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-interfaces?module=ietf-interfaces&amp;revision=2018-02-20</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l2-topology?module=ietf-l2-topology&amp;revision=2020-11-15</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l3-unicast-topology?module=ietf-l3-unicast-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network-topology?module=ietf-network-topology&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network?module=ietf-network&amp;revision=2018-02-26</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-routing-types?module=ietf-routing-types&amp;revision=2017-12-04</nc:capability>' \
                    '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-yang-types?module=ietf-yang-types&amp;revision=2013-07-15</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-ext?module=openconfig-extensions&amp;revision=2022-10-05</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/system?module=openconfig-system&amp;revision=2022-12-20</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/openconfig-types?module=openconfig-types&amp;revision=2019-04-16</nc:capability>' \
                    '<nc:capability>http://openconfig.net/yang/types/yang?module=openconfig-yang-types&amp;revision=2021-07-14</nc:capability>' \
                    '</nc:capabilities><nc:session-id>21497</nc:session-id></nc:hello>]]>]]>'
        sock.send(send_data.encode())
        data = sock.recv(4096)
        sock.close()
        result = data.decode('utf-8')
        print(data)
        assert (result.find('<nc:hello xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">') > 0)
    else:
        sock.close()
        assert (False)


def test_connect_hello_with_request():
    cwd = os.getcwd()
    unix_path = cwd + '/.build/apteryx-netconf.sock'
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.connect(unix_path)
    sock.setblocking(0)
    ready = select.select([sock], [], [], 2)
    if ready[0]:
        data = sock.recv(4096)
        result = data.decode('utf-8')
        m = re.search('<nc:session-id>(.+?)</nc:session-id>', result)
        id = 0
        if m:
            id = int(m.group(1))
        if id > 0:
            send_data = '<?xml version="1.0" encoding="UTF-8"?>\n<nc:hello xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"><nc:capabilities>' \
                        '<nc:capability>urn:ietf:params:netconf:base:1.1</nc:capability>' \
                        '<nc:capability>urn:ietf:params:netconf:capability:xpath:1.0</nc:capability>' \
                        '<nc:capability>urn:ietf:params:netconf:capability:writable-running:1.0</nc:capability>' \
                        '<nc:capability>urn:ietf:params:netconf:capability:with-defaults:1.0?basic-mode=explicit&amp;also-supported=report-all,trim</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:iana-if-type?module=iana-if-type&amp;revision=2017-01-19</nc:capability>' \
                        '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1ab-types?module=ieee802-dot1ab-types&amp;revision=2022-03-15</nc:capability>' \
                        '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-dot1q-types?module=ieee802-dot1q-types&amp;revision=2020-06-04</nc:capability>' \
                        '<nc:capability>urn:ieee:std:802.1Q:yang:ieee802-types?module=ieee802-types&amp;revision=2022-10-29</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-inet-types?module=ietf-inet-types&amp;revision=2013-07-15</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-interfaces?module=ietf-interfaces&amp;revision=2018-02-20</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l2-topology?module=ietf-l2-topology&amp;revision=2020-11-15</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-l3-unicast-topology?module=ietf-l3-unicast-topology&amp;revision=2018-02-26</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network-topology?module=ietf-network-topology&amp;revision=2018-02-26</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-network?module=ietf-network&amp;revision=2018-02-26</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-routing-types?module=ietf-routing-types&amp;revision=2017-12-04</nc:capability>' \
                        '<nc:capability>urn:ietf:params:xml:ns:yang:ietf-yang-types?module=ietf-yang-types&amp;revision=2013-07-15</nc:capability>' \
                        '<nc:capability>http://openconfig.net/yang/openconfig-ext?module=openconfig-extensions&amp;revision=2022-10-05</nc:capability>' \
                        '<nc:capability>http://openconfig.net/yang/system?module=openconfig-system&amp;revision=2022-12-20</nc:capability>' \
                        '<nc:capability>http://openconfig.net/yang/openconfig-types?module=openconfig-types&amp;revision=2019-04-16</nc:capability>' \
                        '<nc:capability>http://openconfig.net/yang/types/yang?module=openconfig-yang-types&amp;revision=2021-07-14</nc:capability>' \
                        '</nc:capabilities><nc:session-id>{id}</nc:session-id></nc:hello>]]>]]>'
            sock.send(send_data.encode())
            send_data = '\n#174\n<?xml version="1.0" encoding="UTF-8"?><nc:rpc xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" ' \
                        'message-id="urn:uuid:459ee3e5-db20-462e-bf4e-1de2c5cc1de8"><nc:get/></nc:rpc>\n##\n'
            sock.send(send_data.encode())
            time.sleep(1)
            data = sock.recv(4096)
        sock.close()
        result = data.decode('utf-8')
        print(data)
        assert (result.find('<nc:rpc-reply xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" message-id="urn:uuid:459ee3e5-db20-462e-bf4e-1de2c5cc1de8">') > 0)
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
