import os
import pytest
from ncclient import manager
from ncclient.operations import RPCError
from lxml import etree
import apteryx

# TEST CONFIGURATION

host = 'localhost'
port = 830
username = 'manager'
password = 'friend'

# TEST HELPERS


db_default = [
    # Default namespace
    ('/test/settings/debug', '1'),
    ('/test/settings/enable', 'true'),
    ('/test/settings/priority', '1'),
    ('/test/settings/hidden', 'friend'),
    ('/test/state/counter', '42'),
    ('/test/state/uptime/days', '5'),
    ('/test/state/uptime/hours', '50'),
    ('/test/state/uptime/minutes', '30'),
    ('/test/state/uptime/seconds', '20'),
    ('/test/animals/animal/cat/name', 'cat'),
    ('/test/animals/animal/cat/type', '1'),
    ('/test/animals/animal/dog/name', 'dog'),
    ('/test/animals/animal/dog/colour', 'brown'),
    ('/test/animals/animal/mouse/name', 'mouse'),
    ('/test/animals/animal/mouse/type', '2'),
    ('/test/animals/animal/mouse/colour', 'grey'),
    ('/test/animals/animal/hamster/name', 'hamster'),
    ('/test/animals/animal/hamster/type', '2'),
    ('/test/animals/animal/hamster/food/banana/name', 'banana'),
    ('/test/animals/animal/hamster/food/banana/type', 'fruit'),
    ('/test/animals/animal/hamster/food/nuts/name', 'nuts'),
    ('/test/animals/animal/hamster/food/nuts/type', 'kibble'),
    ('/test/animals/animal/parrot/name', 'parrot'),
    ('/test/animals/animal/parrot/type', '1'),
    ('/test/animals/animal/parrot/colour', 'blue'),
    ('/test/animals/animal/parrot/toys/toy/rings', 'rings'),
    ('/test/animals/animal/parrot/toys/toy/puzzles', 'puzzles'),
    # Default namespace augmented path
    ('/test/settings/volume', '1'),
    # Non-default namespace same path as default
    ('/t2:test/settings/priority', '2'),
    # Non-default namespace augmented path
    ('/t2:test/settings/speed', '2'),
    # Data for with-defaults testing
    ('/interfaces/interface/eth0/name', 'eth0'),
    ('/interfaces/interface/eth0/mtu', '8192'),
    ('/interfaces/interface/eth0/status', 'up'),
    ('/interfaces/interface/eth1/name', 'eth1'),
    ('/interfaces/interface/eth1/status', 'up'),
    ('/interfaces/interface/eth2/name', 'eth2'),
    ('/interfaces/interface/eth2/mtu', '9000'),
    ('/interfaces/interface/eth2/status', 'not feeling so good'),
    ('/interfaces/interface/eth3/name', 'eth3'),
    ('/interfaces/interface/eth3/mtu', '1500'),
    ('/interfaces/interface/eth3/status', 'waking up'),
    # Data to test xpath
    ('/alphabet/A/id', 'n1'),
    ('/alphabet/A/pre', '1'),
    ('/alphabet/A/post', '26'),
    ('/alphabet/A/B/id', 'n2'),
    ('/alphabet/A/B/pre', '2'),
    ('/alphabet/A/B/post', '3'),
    ('/alphabet/A/B/C/id', 'n3'),
    ('/alphabet/A/B/C/pre', '3'),
    ('/alphabet/A/B/C/post', '1'),
    ('/alphabet/A/B/C/word', 'clergywoman'),
    ('/alphabet/A/B/D/id', 'n4'),
    ('/alphabet/A/B/D/pre', '4'),
    ('/alphabet/A/B/D/post', '2'),
    ('/alphabet/A/B/D/word', 'decadent'),
    ('/alphabet/A/E/id', 'n5'),
    ('/alphabet/A/E/pre', '5'),
    ('/alphabet/A/E/post', '22'),
    ('/alphabet/A/E/F/id', 'n6'),
    ('/alphabet/A/E/F/pre', '6'),
    ('/alphabet/A/E/F/post', '6'),
    ('/alphabet/A/E/F/G/id', 'n7'),
    ('/alphabet/A/E/F/G/pre', '7'),
    ('/alphabet/A/E/F/G/post', '4'),
    ('/alphabet/A/E/F/G/word', 'gentility'),
    ('/alphabet/A/E/F/H/id', 'n8'),
    ('/alphabet/A/E/F/H/pre', '8'),
    ('/alphabet/A/E/F/H/post', '5'),
    ('/alphabet/A/E/F/H/idrefs', 'n17 n26'),
    ('/alphabet/A/E/F/H/word', 'happy-go-lucky man'),
    ('/alphabet/A/E/I/id', 'n9'),
    ('/alphabet/A/E/I/pre', '9'),
    ('/alphabet/A/E/I/post', '9'),
    ('/alphabet/A/E/I/J/id', 'n10'),
    ('/alphabet/A/E/I/J/pre', '10'),
    ('/alphabet/A/E/I/J/post', '7'),
    ('/alphabet/A/E/I/J/word', 'jigsaw'),
    ('/alphabet/A/E/I/K/id', 'n11'),
    ('/alphabet/A/E/I/K/pre', '11'),
    ('/alphabet/A/E/I/K/post', '8'),
    ('/alphabet/A/E/I/K/word', 'kerchief'),
    ('/alphabet/A/E/L/id', 'n12'),
    ('/alphabet/A/E/L/pre', '12'),
    ('/alphabet/A/E/L/post', '15'),
    ('/alphabet/A/E/L/M/id', 'n13'),
    ('/alphabet/A/E/L/M/pre', '13'),
    ('/alphabet/A/E/L/M/post', '10'),
    ('/alphabet/A/E/L/N/id', 'n14'),
    ('/alphabet/A/E/L/N/pre', '14'),
    ('/alphabet/A/E/L/N/post', '13'),
    ('/alphabet/A/E/L/N/O/id', 'n15'),
    ('/alphabet/A/E/L/N/O/pre', '15'),
    ('/alphabet/A/E/L/N/O/post', '11'),
    ('/alphabet/A/E/L/N/O/word', 'ovenware'),
    ('/alphabet/A/E/L/N/P/id', 'n16'),
    ('/alphabet/A/E/L/N/P/pre', '16'),
    ('/alphabet/A/E/L/N/P/post', '12'),
    ('/alphabet/A/E/L/N/P/word', 'plentiful'),
    ('/alphabet/A/E/L/Q/id', 'n17'),
    ('/alphabet/A/E/L/Q/pre', '17'),
    ('/alphabet/A/E/L/Q/post', '14'),
    ('/alphabet/A/E/L/Q/idrefs', 'n8 n26'),
    ('/alphabet/A/E/L/Q/word', 'quarrelsome'),
    ('/alphabet/A/E/R/id', 'n18'),
    ('/alphabet/A/E/R/pre', '18'),
    ('/alphabet/A/E/R/post', '18'),
    ('/alphabet/A/E/R/S/id', 'n19'),
    ('/alphabet/A/E/R/S/pre', '19'),
    ('/alphabet/A/E/R/S/post', '16'),
    ('/alphabet/A/E/R/S/word', 'sage'),
    ('/alphabet/A/E/R/T/id', 'n20'),
    ('/alphabet/A/E/R/T/pre', '20'),
    ('/alphabet/A/E/R/T/post', '17'),
    ('/alphabet/A/E/R/T/word', 'tattered'),
    ('/alphabet/A/E/U/id', 'n21'),
    ('/alphabet/A/E/U/pre', '21'),
    ('/alphabet/A/E/U/post', '21'),
    ('/alphabet/A/E/U/V/id', 'n22'),
    ('/alphabet/A/E/U/V/pre', '22'),
    ('/alphabet/A/E/U/V/post', '19'),
    ('/alphabet/A/E/U/V/word', 'volume'),
    ('/alphabet/A/E/U/W/id', 'n23'),
    ('/alphabet/A/E/U/W/pre', '23'),
    ('/alphabet/A/E/U/W/post', '20'),
    ('/alphabet/A/E/U/W/word', 'wriggle'),
    ('/alphabet/A/X/id', 'n24'),
    ('/alphabet/A/X/pre', '24'),
    ('/alphabet/A/X/post', '25'),
    ('/alphabet/A/X/Y/id', 'n25'),
    ('/alphabet/A/X/Y/pre', '25'),
    ('/alphabet/A/X/Y/post', '23'),
    ('/alphabet/A/X/Y/word', 'yawn'),
    ('/alphabet/A/X/Z/id', 'n26'),
    ('/alphabet/A/X/Z/pre', '26'),
    ('/alphabet/A/X/Z/post', '24'),
    ('/alphabet/A/X/Z/idrefs', 'n8 n17'),
    ('/alphabet/A/X/Z/word', 'zuzzurellone'),
    # Some users, various list and leaf-list tests
    ('/test/settings/users/bob/name', 'bob'),
    ('/test/settings/users/bob/age', '34'),
    ('/test/settings/users/bob/active', 'true'),
    ('/test/settings/users/bob/groups/2', '2'),
    ('/test/settings/users/bob/groups/23', '23'),
]


@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    apteryx.prune("/test")
    apteryx.prune("/test-list")
    apteryx.prune("/test-leaflist")
    apteryx.prune("/t2:test")
    for path, value in db_default:
        apteryx.set(path, value)
    yield
    # After test
    os.system("echo After test")
    apteryx.prune("/test")
    apteryx.prune("/test-list")
    apteryx.prune("/test-leaflist")
    apteryx.prune("/t2:test")


def connect():
    return manager.connect(host=host,
                           port=port,
                           username=username,
                           password=password,
                           hostkey_verify=False,
                           allow_agent=False,
                           look_for_keys=False)


def toXML(xml_str):
    parser = etree.XMLParser(remove_blank_text=True)
    return etree.XML(xml_str, parser=parser)


def diffXML(a, b):
    if len(a) != len(b):
        return "len(%s) != len(%s)" % (a.tag, b.tag)
    if a.tag != b.tag:
        return "%s != %s" % (a.tag, b.tag)
    if a is not None and len(a):
        for ae, be in zip(a, b):
            cmp = diffXML(ae, be)
            if cmp is not None:
                return cmp
    if a.text is None and b.text is not None:
        return "a.text is None and b.text is not None"
    elif a.text is not None and b.text is None:
        return "a.text is not None and b.text is None"
    elif a.text and a.text.strip() != b.text.strip():
        return "%s == %s" % (a.text.strip(), b.text.strip())
    return None


def _get_test_with_filter(f_value, expected=None, f_ns=None, f_type='subtree'):
    """
    Perform a get with the given filter, which can be of type 'subtree' or 'xpath'. If expectede
    respose is given, assert that it was the same as the response from the get. Return the response
    so the caller can perform its own tests.
    """
    m = connect()
    if f_ns is not None:
        filter_str = '<nc:filter type="xpath" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" %s select="%s" />' % (f_ns, f_value)
        print("Filter_str = ", filter_str)
        xml = m.get(filter=filter_str).data
    else:
        xml = m.get(filter=(f_type, f_value)).data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    if expected:
        expected = toXML(expected)
        assert diffXML(xml, expected) is None
    m.close_session()
    return xml


def _get_test_with_defaults_and_filter(f_value, w_d_value, expected=None, f_type='subtree'):
    """
    Perform a get with the given filter, which can be of type 'subtree' or 'xpath'. If expectede
    respose is given, assert that it was the same as the response from the get. Return the response
    so the caller can perform its own tests.
    """
    m = connect()
    xml = m.get(filter=(f_type, f_value), with_defaults=(w_d_value)).data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    if expected:
        expected = toXML(expected)
        assert diffXML(xml, expected) is None
    m.close_session()
    return xml


def response_error_check(err, expect_err):
    assert err is not None
    if "message" in expect_err:
        assert err.message == expect_err["message"]


def _get_test_with_filter_expect_error(f_value, expected=None, f_ns=None, f_type='subtree'):
    """
    Perform a get with the given filter, which can be of type 'subtree' or 'xpath'. If expectede
    respose is given, assert that it was the same as the response from the get. Return the response
    so the caller can perform its own tests.
    """
    xml = None
    m = connect()
    try:
        if f_ns is not None:
            filter_str = '<nc:filter type="xpath" xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0" %s select="%s" />' % (f_ns, f_value)
            print("Filter_str = ", filter_str)
            xml = m.get(filter=filter_str).data
        else:
            xml = m.get(filter=(f_type, f_value)).data
            print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    except RPCError as err:
        print(err)
        assert expected is not None
        response_error_check(err, expected)
    else:
        print(xml)
        if expected:
            expected = toXML(expected)
            assert diffXML(xml, expected) is None
    m.close_session()
    return xml
