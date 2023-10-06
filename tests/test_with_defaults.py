from lxml import etree
from conftest import connect, _get_test_with_defaults_and_filter


def test_with_defaults_explicit():
    with_defaults = 'explicit'
    xpath = '/interfaces'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth1</name>
            <status>up</status>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <mtu>1500</mtu>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(xpath, with_defaults, expected, f_type='xpath')


def test_with_defaults_report_all():
    with_defaults = 'report-all'
    xpath = '/interfaces'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth1</name>
            <mtu>1500</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <mtu>1500</mtu>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(xpath, with_defaults, expected, f_type='xpath')


def test_with_defaults_report_all_level_1():
    with_defaults = 'report-all'
    xpath = '/interfaces/interface'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth1</name>
            <mtu>1500</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <mtu>1500</mtu>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(xpath, with_defaults, expected, f_type='xpath')


def test_with_defaults_report_all_level_2():
    with_defaults = 'report-all'
    xpath = '/interfaces/interface/*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth1</name>
            <mtu>1500</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <mtu>1500</mtu>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(xpath, with_defaults, expected, f_type='xpath')


def test_with_defaults_trim():
    with_defaults = 'trim'
    xpath = '/interfaces'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
        </interface>
        <interface>
            <name>eth1</name>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(xpath, with_defaults, expected, f_type='xpath')


def test_with_defaults_explicit_subtree():
    with_defaults = 'explicit'
    select = '<interfaces></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth1</name>
            <status>up</status>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <mtu>1500</mtu>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_defaults_report_all_subtree():
    with_defaults = 'report-all'
    select = '<interfaces></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth1</name>
            <mtu>1500</mtu>
            <status>up</status>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <mtu>1500</mtu>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


# Test case where a query fails returns no result and the query itself is used to fill in defaults
def test_with_defaults_report_all_subtree_no_match():
    with_defaults = 'report-all'
    select = '<interfaces><interface><name>eth4</name></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_defaults_trim_subtree():
    with_defaults = 'trim'
    select = '<interfaces></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <mtu>8192</mtu>
        </interface>
        <interface>
            <name>eth1</name>
        </interface>
        <interface>
            <name>eth2</name>
            <mtu>9000</mtu>
            <status>not feeling so good</status>
        </interface>
        <interface>
            <name>eth3</name>
            <status>waking up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_defaults_trim_subtree_all():
    m = connect()
    xml = m.get(with_defaults='trim').data
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    # Full tree should be returned
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'
    assert xml.find('./{*}test/{*}state/{*}counter').text == '42'
    assert xml.find('./{*}test/{*}animals/{*}animal/{*}name').text == 'cat'
    assert xml.find('./{*}interfaces/{*}interface/{*}name').text == 'eth0'
    # interfaces/interface/eth1/mtu should not be present as it is a default
    assert xml.find('./{*}interfaces/{*}interface[{*}name="eth1"]/{*}mtu') is None
    m.close_session()


def test_with_defaults_get_subtree_select_one_node_other():
    with_defaults = 'report-all'
    select = '<test><animals><animal><name>cat</name><food/></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_get_leaf():
    with_defaults = 'report-all'
    select = '<interfaces><interface><name>eth0</name><status/></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth0</name>
            <status>up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_get_leaf_different_depths():
    with_defaults = 'report-all'
    select = '''
              <test>
                <settings>
                  <enable/>
                </settings>
                <state>
                    <uptime>
                        <seconds/>
                    </uptime>
                </state>
                <animals>
                    <animal>
                        <name>hamster</name>
                        <food>
                            <name>banana</name>
                            <type/>
                        </food>
                    </animal>
                </animals>
            </test>
            '''

    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <settings>
      <enable>true</enable>
    </settings>
    <state>
      <uptime>
        <seconds>20</seconds>
      </uptime>
    </state>
    <animals>
      <animal>
        <name>hamster</name>
        <food>
          <name>banana</name>
          <type>fruit</type>
        </food>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)
