import os
import pytest
from ncclient import manager
from lxml import etree

# TEST CONFIGURATION

host = '127.0.0.1'
port = 830
username = 'manager'
password = 'friend'

APTERYX = 'LD_LIBRARY_PATH=.build/usr/lib .build/usr/bin/apteryx'

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
]


@pytest.fixture(autouse=True)
def run_around_tests():
    # Before test
    os.system("echo Before test")
    os.system("%s -r /test" % (APTERYX))
    for path, value in db_default:
        os.system("%s -s %s %s" % (APTERYX, path, value))
    yield
    # After test
    os.system("echo After test")
    os.system("%s -r /test" % (APTERYX))
    os.system("%s -r /t2:test" % (APTERYX))


def allowUnknownHosts(host,fingerprint):
    return True

def connect():
    return manager.connect(host=host,
                           port=port,
                           username=username,
                           password=password,
                           hostkey_verify=False,
                           allow_agent=False,
                           look_for_keys=False,
                           unknown_host_cb=allowUnknownHosts)


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


def _get_test_with_filter(f_value, expected=None, f_type='subtree'):
    """
    Perform a get with the given filter, which can be of type 'subtree' or 'xpath'. If expectede
    respose is given, assert that it was the same as the response from the get. Return the response
    so the caller can perform its own tests.
    """
    m = connect()
    xml = m.get(filter=(f_type, f_value)).data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    if expected:
        expected = toXML(expected)
        assert diffXML(xml, expected) is None
    m.close_session()
    return xml
