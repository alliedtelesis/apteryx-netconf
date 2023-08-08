# from ncclient.operations import RPCError
from lxml import etree
from conftest import connect
import re
from pytest import mark
from ncclient.operations import RPCError
from lxml import etree as ET

OK_REGEX_PATTERN = "<nc:ok/>"


def _edit_config_test(conn, payload, expect_err=None, post_xpath=None, inc_str=[], exc_str=[]):
    """
    Run an edit-config for a given connection with the given payload, optionally checking for error, and
    strings that should be included or excluded in the response,
    returning the response from a get carried out with the optional given xpath.
    """
    xml = None
    try:
        response = conn.edit_config(target='running', config=payload)
        print(response)
    except RPCError as err:
        print(err)
        assert expect_err is not None
        assert err.tag == expect_err
    else:
        assert expect_err is None
        if post_xpath is not None:
            xml = conn.get(filter=('xpath', post_xpath)).data
            print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
            if len(inc_str) + len(exc_str) != 0:
                for s in inc_str:
                    assert s in etree.XPath("//text()")(xml)
                for s in exc_str:
                    assert s not in etree.XPath("//text()")(xml)
    return xml


def test_lock_default_ds_fail():
    m = connect()

    # Lock target datastore
    try:
        m.lock()
    except Exception as e:
        assert e.tag == "operation-not-supported"
        assert e.type == "protocol"

    m.close_session()


def test_lock_ok():
    m = connect()
    response = None

    # Lock target datastore
    response = m.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    m.close_session()


@mark.skip(reason="requires candidate datastore")
def test_lock_candidate():
    pass


def test_lock_unlock_ok():
    m = connect()
    response = None

    # Lock target datastore
    response = m.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Unlock target datastore
    response = None
    match = None
    response = m.unlock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    m.close_session()


def test_unlock_fail():
    m = connect()

    # Unlock target datastore
    response = None
    try:
        response = m.unlock(target="running")
    except Exception as e:
        assert e.severity == "error"
        assert e.tag == "operation-failed"
        assert e.type == "protocol"
        assert e.message is not None

    assert response is None

    m.close_session()


@mark.skip(reason="requires candidate datastore")
def test_lock_candidate_unlock_running():
    pass


@mark.skip(reason="requires candidate datastore")
def test_lock_running_unlock_candidate():
    pass


def test_lock_unlock_twice_ok():

    test_lock_unlock_ok()
    test_lock_unlock_ok()


def test_lock_lock_fail():
    m = connect()

    # Lock target datastore
    response = None
    response = m.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Attempt to lock the same datastore
    response = None
    match = None
    try:
        response = m.lock(target="running")
    except Exception as e:
        assert e.tag == "lock-denied"
        assert e.type == "protocol"
        assert e.severity == "error"
        assert e.message is not None
        assert e.info is not None
        xml_error_info = ET.fromstring(e.info.encode('utf-8'))
        assert m.session_id == xml_error_info.find('.//{*}session-id').text

    assert response is None

    m.close_session()


def test_lock_unlock_unlock_fail():
    m = connect()

    # Lock target datastore
    response = None
    response = m.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Unlock target datastore
    response = None
    match = None
    response = m.unlock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Attempt unlock, again
    response = None
    match = None
    try:
        response = m.unlock(target="running")
    except Exception as e:
        assert e.tag == "operation-failed"
        assert e.type == "protocol"
        assert e.severity == "error"
        assert e.message is not None

    assert response is None

    m.close_session()


def test_lock_get_unlock_ok():
    m = connect()

    # Lock target datastore
    response = None
    response = m.lock(target="running")
    assert response is not None
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Perform get operation
    xml = m.get().data
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter').text == '42'

    # Unlock target datastore
    response = None
    match = None
    response = m.unlock(target="running")
    assert response is not None
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    m.close_session()


@mark.skip(reason="delete-config not implemented")
def test_lock_delete_unlock():
    pass


def test_lock_edit_unlock_ok():
    m = connect()

    # Lock target datastore
    response = None
    response = m.lock(target="running")
    assert response is not None
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Perform edit operation
    payload1 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
    """

    _edit_config_test(m, payload1, post_xpath="/test/animals", inc_str=["cat"])

    payload2 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>big</type>
        </animal>
    </animals>
  </test>
</config>
    """

    _edit_config_test(m, payload2, post_xpath="/test/animals", inc_str=["cat"])

    # Unlock target datastore
    response = None
    match = None
    response = m.unlock(target="running")
    assert response.ok is True
    assert response is not None
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    m.close_session()


@mark.skip(reason="copy-config not implemented")
def test_lock_copy_unlock():
    pass


def test_lock_none_fail():
    m = connect()
    response = None

    try:
        response = m.lock(target=None)
    except Exception as e:
        assert e.severity == "error"
        assert e.tag == "operation-not-supported"
        assert e.type == "protocol"

    assert response is None

    m.close_session()


def test_lock_unlock_none_fail():
    m = connect()

    # Lock target
    response = None
    response = m.lock(target="running")
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Attempt to unlock target=None
    response = None
    match = None
    try:
        response = m.unlock(target=None)
    except Exception as e:
        assert e.severity == "error"
        assert e.tag == "operation-not-supported"
        assert e.type == "protocol"

    assert response is None

    # Unlock target
    response = m.unlock(target="running")
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN
    assert response.ok is True

    m.close_session()


def test_concurrent_lock_fail():

    # Session 1: connect
    m1 = connect()

    # Session1: Lock target
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 2: connect
    m2 = connect()

    # Session 2: Attempt to lock the same target datastore
    try:
        m2.lock(target="running")
    except Exception as e:
        print(f"Exception: {e.__dict__}")
        assert e.tag == "lock-denied"
        assert e.type == "protocol"
        assert e.severity == "error"
        assert e.message is not None
        assert e.info is not None
        xml_error_info = ET.fromstring(e.info.encode('utf-8'))
        assert m1.session_id == xml_error_info.find('.//{*}session-id').text

    # Session 1: close
    m1.close_session()

    # Session 2: close
    m2.close_session()


def test_concurrent_lock_unlock_fail():

    # Session 1: connect
    m1 = connect()

    # Session1: Lock target
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 2: connect
    m2 = connect()

    # Session 2: Attempt to unlock the same target datastore
    try:
        m2.unlock(target="running")
    except Exception as e:
        print(f"Exception: {e.__dict__}")
        assert e.tag == "lock-denied"
        assert e.type == "protocol"
        assert e.severity == "error"
        assert e.message is not None
        assert e.info is not None
        xml_error_info = ET.fromstring(e.info.encode('utf-8'))
        assert m1.session_id == xml_error_info.find('.//{*}session-id').text

    # Session 1: close
    m1.close_session()

    # Session 2: close
    m2.close_session()


def test_concurrent_lock_get():

    # Session 1: connect
    m1 = connect()

    # Session 2: connect
    m2 = connect()

    # Session 1: Lock target
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 2: Attempt to perform get operation
    try:
        m2.get().data
    except Exception as e:
        assert e.tag == "in-use"
        assert e.type == "application"
        assert e.severity == "error"
        assert e.message is not None
        assert e.info is not None
        xml_error_info = ET.fromstring(e.info.encode('utf-8'))
        assert m1.session_id == xml_error_info.find('.//{*}session-id').text

    # Session 1: Unlock target
    response = m1.unlock(target="running")
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN
    assert response.ok is True

    # Session 2: Attempt to perform get operation should succeed now
    xml = m2.get().data
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter').text == '42'

    # Session 1: close
    m1.close_session()

    # Session 2: close
    m2.close_session()


def test_concurrent_lock_edit():

    # Session 1: connect
    m1 = connect()

    # Session 2: connect
    m2 = connect()

    # Session 1: Lock target
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 2: Attempt to perform edit operation
    payload1 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
    """
    _edit_config_test(m2, payload1, expect_err="in-use", post_xpath="/test/animals", inc_str=["cat"])

    # Session 1: Unlock target
    response = m1.unlock(target="running")
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN
    assert response.ok is True

    # Session 2: Attempt to perform edit operation should succeed now
    _edit_config_test(m2, payload1, post_xpath="/test/animals", inc_str=["cat"])
    payload2 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>big</type>
        </animal>
    </animals>
  </test>
</config>
    """
    _edit_config_test(m2, payload2, post_xpath="/test/animals", inc_str=["cat"])

    # Session 1: close
    m1.close_session()

    # Session 2: close
    m2.close_session()


def test_concurrent_lock_get_edit():

    # Session 1: connect
    m1 = connect()

    # Session 2: connect
    m2 = connect()

    # Session 1: Lock target
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 1: Perform get operation
    xml = m1.get().data
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter').text == '42'

    # Session 2: Attempt to perform edit operation should fail
    payload1 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
    """
    _edit_config_test(m2, payload1, expect_err="in-use", post_xpath="/test/animals", inc_str=["cat"])

    # Session 1: Unlock target
    response = m1.unlock(target="running")
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN
    assert response.ok is True

    # Session 2: Attempt to perform edit operation should succeed now
    _edit_config_test(m2, payload1, post_xpath="/test/animals", inc_str=["cat"])
    payload2 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>big</type>
        </animal>
    </animals>
  </test>
</config>
    """
    _edit_config_test(m2, payload2, post_xpath="/test/animals", inc_str=["cat"])

    # Session 1: close
    m1.close_session()

    # Session 2: close
    m2.close_session()


def test_concurrent_lock_edit_get():

    # Session 1: connect
    m1 = connect()

    # Session 2: connect
    m2 = connect()

    # Session 1: Lock target
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 1: Perform edit operation
    payload1 = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
    """
    _edit_config_test(m1, payload1, post_xpath="/test/animals", inc_str=["cat"])

    # Session 2: Attempt to perform get operation should fail
    try:
        m2.get().data
    except Exception as e:
        assert e.tag == "in-use"
        assert e.type == "application"
        assert e.severity == "error"
        assert e.message is not None
        assert e.info is not None
        xml_error_info = ET.fromstring(e.info.encode('utf-8'))
        assert xml_error_info.find('.//{*}session-id').text is not None
        assert m1.session_id == xml_error_info.find('.//{*}session-id').text

    # Session 1: Unlock target
    response = m1.unlock(target="running")
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN
    assert response.ok is True

    # Session 2: Attempt to peform get operation should succeed now
    xml = m2.get().data
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter').text == '42'

    # Session 1: close
    m1.close_session()

    # Session 2: close
    m2.close_session()


@mark.skip(reason="delete-config not implemented")
def test_concurrent_lock_unlock_del():
    pass


@mark.skip(reason="copy-config not implemented")
def test_concurrent_lock_unlock_copy():
    pass


def test_concurrent_lock_kill_ok():
    # Session 1: connect
    m1 = connect()

    # Session 2: connect
    m2 = connect()

    # Session 1: lock datastore
    response = None
    response = m1.lock(target="running")
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 2: kill session-1
    response = m2.kill_session(m1.session_id)
    assert response.ok is True
    match = re.search(OK_REGEX_PATTERN, response.xml)
    assert match.group() == OK_REGEX_PATTERN

    # Session 2: close
    m2.close_session()
