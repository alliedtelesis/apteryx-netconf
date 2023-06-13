from ncclient.operations import RPCError
from lxml import etree
from conftest import connect

# CAPABILITIES


def test_server_capabilities():
    m = connect()
    for capability in m.server_capabilities:
        print("Capability: %s" % capability)
    assert ":base" in m.server_capabilities
    assert ":writable-running" in m.server_capabilities
    # assert ":startup" in m.server_capabilities
    assert ":xpath" in m.server_capabilities
    assert ":with-defaults" in m.server_capabilities

    assert ":candidate" not in m.server_capabilities
    assert ":rollback-on-error" not in m.server_capabilities
    assert ":url" not in m.server_capabilities
    assert ":confirmed-commit" not in m.server_capabilities
    assert ":validate" not in m.server_capabilities
    assert ":power-control" not in m.server_capabilities
    assert ":notification" not in m.server_capabilities
    assert ":interleave" not in m.server_capabilities
    assert ":session-id" not in m.server_capabilities
    # Supported models - first is default namespace
    assert "http://test.com/ns/yang/testing?module=testing&revision=2023-01-01" in m.server_capabilities
    assert "http://test.com/ns/yang/testing-2?module=testing-2&revision=2023-02-01" in m.server_capabilities
    assert "http://test.com/ns/yang/testing2-augmented?module=testing2-augmented&revision=2023-02-02" in m.server_capabilities
    m.close_session()

# TODO :with-defaults
# TODO explicit namespace queries

# Packet formats


def test_rpc_data():
    m = connect()
    reply = m.get_config(source='running', filter=('xpath', "/test/settings/debug"))
    print(reply.xml)
    xml = reply._root
    assert xml.nsmap == {'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0'}
    assert xml.tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply'
    assert xml.getchildren()[0].tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}data'
    assert xml.prefix == 'nc'
    m.close_session()


def test_rpc_ok():
    config = """
<config>
  <test>
    <settings>
        <priority>5</priority>
    </settings>
  </test>
</config>
"""
    m = connect()
    reply = m.edit_config(target='running', config=config)
    print(reply.xml)
    xml = reply._root
    assert xml.nsmap == {'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0'}
    assert xml.tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply'
    assert xml.getchildren()[0].tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}ok'
    assert xml.prefix == 'nc'
    m.close_session()


def test_rpc_error():
    m = connect()
    try:
        m.get_config(source='candidate', filter=('xpath', "/test/settings/debug"))
    except RPCError as e:
        reply = e
    xml = reply.xml.getparent()
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert xml.nsmap == {'nc': 'urn:ietf:params:xml:ns:netconf:base:1.0'}
    assert xml.tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}rpc-reply'
    assert xml.getchildren()[0].tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}rpc-error'
    assert xml.prefix == 'nc'
    m.close_session()


# GET-CONFIG


def test_get_config_simple_node():
    m = connect()
    xml = m.get_config(source='running', filter=('xpath', "/test/settings/debug")).data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    m.close_session()


def test_get_config_unsupported_datastore():
    m = connect()
    response = None
    try:
        response = m.get_config(source='candidate', filter=('xpath', "/test/settings/debug"))
    except RPCError as err:
        print(err)
        assert err.tag == 'operation-not-supported'
    assert response is None, 'Should have received an RPCError'
    m.close_session()


def test_get_config_no_state():
    m = connect()
    xml = m.get_config(source='running').data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    # Full tree should be returned with config only
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter') is None
    assert xml.find('./{*}test/{*}state/{*}uptime/days') is None
    assert xml.find('./{*}test/{*}animals/{*}animal/{*}name').text == 'cat'
    # Ignore the rest!
    m.close_session()

# TODO VALIDATE
# TODO COPY-CONFIG
# TODO DELETE-CONFIG
# TODO LOCK/UNLOCK
