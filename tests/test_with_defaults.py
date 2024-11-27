from lxml import etree
import apteryx
from conftest import connect, _get_test_with_defaults_and_filter
from test_edit_config import _edit_config_test


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


def test_with_defaults_report_all_subtree_list():
    with_defaults = 'report-all'
    select = '<interfaces><interface></interface></interfaces>'
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


# Test case where a query fails and returns no result. This is a specific request for a list item.
# As the list item does not exist no data is returned.
def test_with_defaults_report_all_subtree_no_match():
    with_defaults = 'report-all'
    select = '<interfaces><interface><name>eth4</name></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_defaults_report_all_leaf():
    apteryx.set("/test/settings/debug", "")
    with_defaults = 'report-all'
    select = '<test><settings><debug/></settings></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <settings>
      <debug>disable</debug>
    </settings>
  </test>
</nc:data>
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


def test_with_defaults_get_subtree_select_one_node_other_2():
    with_defaults = 'report-all'
    select = '<test><animals><animal><name>dog</name><config><type/></config></animal></animals></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <config>
          <type>big</type>
        </config>
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


def test_with_default_report_all_get_missing_leaf():
    with_defaults = 'report-all'
    select = '<interfaces><interface><name>eth1</name></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth1</name>
            <mtu>1500</mtu>
            <status>up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_get_specific_leaf():
    with_defaults = 'report-all'
    select = '<interfaces><interface><name>eth1</name><status/></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
            <name>eth1</name>
            <status>up</status>
        </interface>
    </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_no_name_get_specific_leaf():
    with_defaults = 'report-all'
    select = '<interfaces><interface><name></name><mtu/></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="http://example.com/ns/interfaces">
    <interface>
      <name>eth0</name>
      <mtu>8192</mtu>
    </interface>
    <interface>
      <name>eth1</name>
      <mtu>1500</mtu>
    </interface>
    <interface>
      <name>eth2</name>
      <mtu>9000</mtu>
    </interface>
    <interface>
      <name>eth3</name>
      <mtu>1500</mtu>
    </interface>
  </interfaces>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_no_defaults_set_leaf():
    apteryx.set("/interfaces/interface/eth0/mtu", "")
    apteryx.set("/interfaces/interface/eth2/mtu", "")
    apteryx.set("/interfaces/interface/eth3/mtu", "")
    with_defaults = 'report-all'
    select = '<interfaces><interface><mtu/></interface></interfaces>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="http://example.com/ns/interfaces">
    <interface>
      <name>eth0</name>
      <mtu>1500</mtu>
    </interface>
    <interface>
      <name>eth1</name>
      <mtu>1500</mtu>
    </interface>
    <interface>
      <name>eth2</name>
      <mtu>1500</mtu>
    </interface>
    <interface>
      <name>eth3</name>
      <mtu>1500</mtu>
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


def test_with_default_report_all_on_empty_branch():
    del_payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings xc:operation="delete" />
  </test>
</config>
"""
    xml = _edit_config_test(del_payload, post_xpath='/test/settings')
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert etree.XPath("//text()")(xml) == []
    with_defaults = 'report-all'
    select = '<test></test>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <settings>
      <debug>disable</debug>
      <enable>false</enable>
      <readonly>yes</readonly>
      <time>
        <active>false</active>
      </time>
    </settings>
    <state>
      <counter>42</counter>
      <uptime>
        <days>5</days>
        <hours>50</hours>
        <minutes>30</minutes>
        <seconds>20</seconds>
      </uptime>
    </state>
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <config>
          <type>big</type>
        </config>
      </animal>
      <animal>
        <name>dog</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>brown</colour>
        <config>
          <type>big</type>
        </config>
      </animal>
      <animal>
        <name>hamster</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:little</type>
        <food>
          <name>banana</name>
          <type>fruit</type>
        </food>
        <food>
          <name>nuts</name>
          <type>kibble</type>
        </food>
        <config>
          <type>big</type>
        </config>
      </animal>
      <animal>
        <name>mouse</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:little</type>
        <colour>grey</colour>
        <config>
          <type>big</type>
        </config>
      </animal>
      <animal>
        <name>parrot</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>blue</colour>
        <config>
          <type>big</type>
        </config>
        <toys>
          <toy>puzzles</toy>
          <toy>rings</toy>
        </toys>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_trunk_data():
    apteryx.set("/test/settings/users/alfred/name", "alfred")
    apteryx.set("/test/settings/users/alfred/age", "87")
    apteryx.set("/test/settings/debug", "")
    with_defaults = 'report-all'
    select = '''
            <test>
                <settings/>
            </test>
            '''
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <settings>
      <debug>disable</debug>
      <enable>true</enable>
      <priority>1</priority>
      <readonly>yes</readonly>
      <time>
        <active>false</active>
      </time>
      <users>
        <name>alfred</name>
        <age>87</age>
        <active>false</active>
      </users>
      <users>
        <name>bob</name>
        <age>34</age>
        <active>true</active>
        <groups>2</groups>
        <groups>23</groups>
      </users>
      <volume>1</volume>
    </settings>
  </test>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_proxy_get_leaf():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205", "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    with_defaults = 'report-all'
    select = '<logical-elements><logical-element><name>loopy</name><interfaces><interface><name>eth0</name><status/></interface></interfaces></logical-element></logical-elements>'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <logical-elements xmlns="http://example.com/ns/logical-elements">
    <logical-element>
      <interfaces xmlns="http://example.com/ns/interfaces">
        <interface>
          <name>eth0</name>
          <status>up</status>
        </interface>
      </interfaces>
    </logical-element>
  </logical-elements>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)


def test_with_default_report_all_complex_tree():
    """
    Use the complex objects tree of the test schema to verify correct operation.
    """
    apteryx.set("/test/objects/object/fred/name", "fred")
    apteryx.set("/test/objects/object/fred/top-container/conf/enabled", "false")
    with_defaults = 'report-all'
    select = """
        <test xmlns="http://test.com/ns/yang/testing">
            <objects>
                <object>
                    <name>fred</name>
                    <top-container>
                        <inner-container>
                            <conf>
                                <enabled/>
                            </conf>
                        </inner-container>
                    </top-container>
                </object>
            </objects>
        </test>
    """
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <objects>
      <object>
        <name>fred</name>
        <top-container>
          <conf>
            <enabled>true</enabled>
          </conf>
          <inner-container>
            <conf>
              <enabled>false</enabled>
            </conf>
          </inner-container>
        </top-container>
      </object>
    </objects>
  </test>
</nc:data>
    """
    _get_test_with_defaults_and_filter(select, with_defaults, expected)
