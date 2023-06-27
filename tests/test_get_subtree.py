import pytest
from ncclient.xml_ import to_ele
from lxml import etree
from conftest import connect, _get_test_with_filter, apteryx_set


def test_get_subtree_no_filter():
    m = connect()
    xml = m.get().data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    # Full tree should be returned
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter').text == '42'
    assert xml.find('./{*}test/{*}animals/{*}animal/{*}name').text == 'cat'
    m.close_session()


@pytest.mark.skip(reason="exception creating RPC")
def test_get_subtree_empty_filter():
    m = connect()
    # ncclient does not allow empty filter strings - so make our own rpc
    rpc = """<get><filter type="subtree"></filter></get>"""

    xml = to_ele(m.rpc(to_ele(rpc)).xml)
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    # Nothing but an rpc-reply with an empty data attribute should be returned
    assert len(xml) and len(xml[0]) == 0
    m.close_session()


def test_get_subtree_node():
    select = '<test xmlns="http://test.com/ns/yang/testing"><settings><debug/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <debug>enable</debug>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


# No default or prefixed namespace - we use the internal default namespace
def test_get_subtree_node_ns_none():
    select = '<test><settings><priority/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_node_ns_aug_none():
    select = '<test><settings><volume/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <volume>1</volume>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


# Default namespace is the same as the internal default namespace
def test_get_subtree_node_ns_default():
    select = '<test xmlns="https://github.com/alliedtelesis/apteryx"><settings><priority/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_node_ns_aug_default():
    select = '<test xmlns="https://github.com/alliedtelesis/apteryx"><settings><volume/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <volume>1</volume>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


# Default namespace is not the internal default namespace
def test_get_subtree_node_ns_other_no_prefix():
    select = '<test xmlns="http://test.com/ns/yang/testing-2"><settings><priority/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <priority>2</priority>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_node_ns_aug_other_no_prefix():
    select = '<test xmlns="http://test.com/ns/yang/testing-2"><settings><speed xmlns="http://test.com/ns/yang/testing2-augmented"/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <speed xmlns="http://test.com/ns/yang/testing2-augmented">2</speed>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


# Prefixed namespace is not the internal default namespace
# Note that prefixes are not inherited, so must be specified on every node

def test_get_subtree_node_ns_other_prefix():
    select = '<t2:test xmlns:t2="http://test.com/ns/yang/testing-2"><t2:settings><t2:priority/></t2:settings></t2:test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <priority>2</priority>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_node_ns_aug_other_prefix():
    select = '<t2:test xmlns:t2="http://test.com/ns/yang/testing-2" xmlns:aug2="http://test.com/ns/yang/testing2-augmented"><t2:settings><aug2:speed/></t2:settings></t2:test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <speed xmlns="http://test.com/ns/yang/testing2-augmented">2</speed>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_empty():
    apteryx_set("/test/settings/empty", "empty")
    select = '<test><settings><empty/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <empty></empty>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_trunk():
    select = '<test><settings/></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <debug>enable</debug>
            <enable>true</enable>
            <priority>1</priority>
            <volume>1</volume>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_multi_parameters():
    select = '<test><settings><debug/><priority/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <debug>enable</debug>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_list_container():
    select = '<test><animals/></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type>big</type>
      </animal>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
      <animal>
        <name>hamster</name>
        <type>little</type>
        <food>
          <name>banana</name>
          <type>fruit</type>
        </food>
        <food>
          <name>nuts</name>
          <type>kibble</type>
        </food>
      </animal>
      <animal>
        <name>mouse</name>
        <type>little</type>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <type>big</type>
        <colour>blue</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_list_element():
    select = '<test><animals><animal/></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type>big</type>
      </animal>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
      <animal>
        <name>hamster</name>
        <type>little</type>
        <food>
          <name>banana</name>
          <type>fruit</type>
        </food>
        <food>
          <name>nuts</name>
          <type>kibble</type>
        </food>
      </animal>
      <animal>
        <name>mouse</name>
        <type>little</type>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <type>big</type>
        <colour>blue</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_list_parameter():
    select = '<test><animals><animal><name/></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
      </animal>
      <animal>
        <name>dog</name>
      </animal>
      <animal>
        <name>hamster</name>
      </animal>
      <animal>
        <name>mouse</name>
      </animal>
      <animal>
        <name>parrot</name>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_selection_multi():
    select = '<test><animals><animal><name/><type/></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type>big</type>
      </animal>
      <animal>
        <name>dog</name>
      </animal>
      <animal>
        <name>hamster</name>
        <type>little</type>
      </animal>
      <animal>
        <name>mouse</name>
        <type>little</type>
      </animal>
      <animal>
        <name>parrot</name>
        <type>big</type>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_one_node():
    select = '<test><animals><animal><name>cat</name></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_one_with_colon():
    apteryx_set("/test/animals/animal/cat:ty/name", "cat:ty")
    apteryx_set("/test/animals/animal/cat:ty/type", "1")
    select = '<test><animals><animal><name>cat:ty</name></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat:ty</name>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_one_elements():
    select = '<test><animals><animal><name>cat</name><type/></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_multi():
    select = """
<test>
  <animals>
    <animal>
      <name>cat</name>
    </animal>
    <animal>
      <name>dog</name>
    </animal>
  </animals>
</test>
    """
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type>big</type>
            </animal>
            <animal>
                <name>dog</name>
                <colour>brown</colour>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_attr_named_only():
    select = '<test><animals><animal name="cat"/></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_attr_named_element():
    select = '<test><animals><animal name="mouse"><type/></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>mouse</name>
                <type>little</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_no_key_other_field():
    """
    Don't specify key node in filter. RFC states that we MAY include key in output,
    we are not currentl doing this.
    """
    select = '<test><animals><animal><type/></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <type>big</type>
            </animal>
            <animal>
                <type>little</type>
            </animal>
            <animal>
                <type>little</type>
            </animal>
            <animal>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_no_key_other_field_value():
    """
    RFC states 'Filtering of list content is not supported.' This means that this query will return
    all types.
    """
    select = '<test><animals><animal><type>little</type></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <type>big</type>
            </animal>
            <animal>
                <type>little</type>
            </animal>
            <animal>
                <type>little</type>
            </animal>
            <animal>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_key_other_field_value():
    """
    This test may not be showing correct behaviour.
    """
    select = '<test><animals><animal><name/><type>little</type></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type>big</type>
            </animal>
            <animal>
                <name>dog</name>
            </animal>
            <animal>
                <name>hamster</name>
                <type>little</type>
            </animal>
            <animal>
                <name>mouse</name>
                <type>little</type>
            </animal>
            <animal>
                <name>parrot</name>
                <type>big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_select_key_value_other_field_value():
    """
    This test may not be showing correct behaviour.
    """
    select = """
<test>
    <animals>
        <animal>
            <name>mouse</name>
            <type>little</type>
        </animal>
    </animals>
</test>
    """
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>mouse</name>
                <type>little</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(select, expected)


def test_get_subtree_missing():
    select = '<test><animals><animal><name>elephant</name></animal></animals></test>'
    xml = _get_test_with_filter(select)
    assert xml.tag == '{urn:ietf:params:xml:ns:netconf:base:1.0}data'
    assert len(xml.getchildren()) == 0
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
