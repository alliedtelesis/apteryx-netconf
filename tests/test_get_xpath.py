import apteryx
from conftest import _get_test_with_filter, _get_test_with_filter_expect_error


# GET XPATH


def test_get_xpath_node():
    xpath = '/test/settings/debug'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <debug>enable</debug>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'


def test_get_xpath_node_with_child():
    xpath = '/test/child::settings/child::debug'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <debug>enable</debug>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}debug').text == 'enable'


# No default or prefixed namespace - we use the internal default namespace
def test_get_xpath_node_ns_none():
    xpath = '/test/settings/priority'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '1'


def test_get_xpath_node_ns_aug_none():
    xpath = '/test/settings/volume'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <volume>1</volume>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}volume').text == '1'


def test_get_xpath_node_ns_default():
    xpath = '/test:test/settings/priority'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '1'


def test_get_xpath_node_ns_default_with_child_1():
    xpath = '/child::test:test/settings/priority'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '1'


def test_get_xpath_node_ns_default_with_child_2():
    xpath = '/test:test/child::settings/priority'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <priority>1</priority>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '1'


def test_get_xpath_node_ns_aug_default():
    xpath = '/test:test/settings/volume'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <volume>1</volume>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}volume').text == '1'


# Prefixed namespace is not the internal default namespace
def test_get_xpath_node_ns_other():
    xpath = '/t2:test/t2:settings/t2:priority'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <priority>2</priority>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '2'


def test_get_xpath_node_ns_other_with_child():
    xpath = '/child::t2:test/child::t2:settings/child::t2:priority'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <priority>2</priority>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '2'


def test_get_xpath_node_ns_aug_other():
    xpath = '/t2:test/t2:settings/aug2:speed'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing-2">
        <settings>
            <speed xmlns="http://test.com/ns/yang/testing2-augmented">2</speed>
        </settings>
    </test>
</nc:data>
    """
    xml = _get_test_with_filter(xpath, expected, f_type='xpath')
    assert xml.find('./{*}test/{*}settings/{*}speed').text == '2'


def test_get_xpath_trunk():
    xpath = '/test/settings'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <settings>
            <debug>enable</debug>
            <enable>true</enable>
            <priority>1</priority>
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
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_trunk():
    xpath = '/test/animals'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
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
      </animal>
      <animal>
        <name>mouse</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:little</type>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>blue</colour>
        <toys>
          <toy>puzzles</toy>
          <toy>rings</toy>
        </toys>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_toplevel_list_all():
    apteryx.set("/test-list/1/index", "1")
    apteryx.set("/test-list/1/name", "cat")
    apteryx.set("/test-list/3/index", "3")
    apteryx.set("/test-list/3/name", "mouse")
    apteryx.set("/test-list/2/index", "2")
    apteryx.set("/test-list/2/name", "dog")
    xpath = '/test-list'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test-list xmlns="http://test.com/ns/yang/testing">
      <index>1</index>
      <name>cat</name>
    </test-list>
    <test-list xmlns="http://test.com/ns/yang/testing">
      <index>2</index>
      <name>dog</name>
    </test-list>
    <test-list xmlns="http://test.com/ns/yang/testing">
      <index>3</index>
      <name>mouse</name>
    </test-list>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_toplevel_leaflist():
    apteryx.set("/test-leaflist/cat", "cat")
    apteryx.set("/test-leaflist/mouse", "mouse")
    apteryx.set("/test-leaflist/dog", "dog")
    xpath = '/test-leaflist'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test-leaflist xmlns="http://test.com/ns/yang/testing">cat</test-leaflist>
    <test-leaflist xmlns="http://test.com/ns/yang/testing">dog</test-leaflist>
    <test-leaflist xmlns="http://test.com/ns/yang/testing">mouse</test-leaflist>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_select_one_trunk():
    xpath = "/test/animals/animal[name='cat']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_toplevel_list_select_one():
    apteryx.set("/test-list/1/index", "1")
    apteryx.set("/test-list/1/name", "cat")
    apteryx.set("/test-list/2/index", "2")
    apteryx.set("/test-list/2/name", "dog")
    xpath = "/test-list[index='2']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test-list xmlns="http://test.com/ns/yang/testing">
      <index>2</index>
      <name>dog</name>
    </test-list>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_select_one_trunk_with_child():
    xpath = "/child::test/animals/animal[name='cat']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_select_one_parameter():
    xpath = "/test/animals/animal[name='cat']/type"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_select_one_parameter_double_quotes():
    xpath = "/test/animals/animal[name=\"cat\"]/type"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_select_one_parameter_double_quotes_with_child():
    xpath = "/child::test/animals/child::animal[name=\"cat\"]/type"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_query_multi_with_child():
    xpath = ("/test/child::animals/animal[name='cat']/type | /test/animals/child::animal[name='dog']/child::colour")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_query_multi():
    xpath = ("/test/animals/animal[name='cat']/type | /test/animals/animal[name='dog']/colour")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_multi_select_multi():
    xpath = ("/test/animals/animal[name='cat']/type | /interfaces/interface[name='eth2']/mtu")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
  <interfaces xmlns="http://example.com/ns/interfaces">
    <interface>
      <name>eth2</name>
      <mtu>9000</mtu>
    </interface>
  </interfaces>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_simple_star():
    xpath = ("/test/animals/*/name")
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
    _get_test_with_filter(xpath, expected, f_type='xpath')


# expect no data - the star is only a wildcard for one tree level
def test_get_xpath_simple_invalid_star():
    xpath = ("/test/*/name")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_multi_layers_double_slash():
    xpath = ("/test/animals//name")
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
        <food>
          <name>banana</name>
        </food>
        <food>
          <name>nuts</name>
        </food>
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
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_multi_layers_star_field():
    xpath = ("/test/animals/*/colour")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
      <animal>
        <name>mouse</name>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <colour>blue</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_slash_slash_field():
    xpath = ("/test/animals//colour")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
      <animal>
        <name>mouse</name>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <colour>blue</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_multiple_slash_slash_field():
    xpath = ("/test/animals//food//type")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>hamster</name>
        <food>
          <type>fruit</type>
        </food>
        <food>
          <type>kibble</type>
        </food>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_multi_xpath_select_multi():
    xpath = ("/test:test/animals/animal[name='cat']/type | /exam:interfaces/interface[name='eth2']/mtu")
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
  <interfaces xmlns="http://example.com/ns/interfaces">
    <interface>
      <name>eth2</name>
      <mtu>9000</mtu>
    </interface>
  </interfaces>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_with_slash_slash():
    xpath = '//animal'
    nspace = 'xmlns:test="http://test.com/ns/yang/testing"'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
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
      </animal>
      <animal>
        <name>mouse</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:little</type>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>blue</colour>
        <toys>
          <toy>puzzles</toy>
          <toy>rings</toy>
        </toys>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, nspace, f_type='xpath')


def test_get_xpath_with_slash_slash_bad_ns():
    xpath = '//animal'
    nspace = 'xmlns:bob="http://test.com/ns/yang/bob" xmlns:test="http://test.com/ns/yang/testing"'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
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
      </animal>
      <animal>
        <name>mouse</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:little</type>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>blue</colour>
        <toys>
          <toy>puzzles</toy>
          <toy>rings</toy>
        </toys>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, nspace, f_type='xpath')


def test_get_xpath_with_missing_path_star_path():
    xpath = '/exam:interfaces/*/name'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="http://example.com/ns/interfaces">
    <interface>
      <name>eth0</name>
    </interface>
    <interface>
      <name>eth1</name>
    </interface>
    <interface>
      <name>eth2</name>
    </interface>
    <interface>
      <name>eth3</name>
    </interface>
  </interfaces>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_with_path_star():
    xpath = '/exam:interfaces/interface/*'
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
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_with_name_value():
    xpath = '/test:test//*[name="dog"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_with_name_first():
    xpath = '/test:test//animal[1]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_with_name_last():
    xpath = '/test:test//animal[last()]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>parrot</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>blue</colour>
        <toys>
          <toy>puzzles</toy>
          <toy>rings</toy>
        </toys>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a1():
    # A1 //L/*
    xpath = '/alpha:alphabet//L/*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a2():
    # A2 //L/parent::*
    xpath = '/alpha:alphabet//L/parent::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a3():
    # A3 //L/descendant::*
    xpath = '/alpha:alphabet//L/descendant::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a4():
    # A4 //L/descendant-or-self::*
    xpath = '/alpha:alphabet//L/descendant-or-self::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a5():
    # A5 //L/ancestor::*
    xpath = '/alpha:alphabet//L/ancestor::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a6():
    # A6 //L/ancestor-or-self::*
    xpath = '/alpha:alphabet//L/ancestor-or-self::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a7():
    # A7 //L/following-sibling::*
    xpath = '/alpha:alphabet//L/following-sibling::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a8():
    # A8 //L/preceding-sibling::*
    xpath = '/alpha:alphabet//L/preceding-sibling::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a9():
    # A9 //L/following::*
    xpath = '/alpha:alphabet//L/following::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a10():
    # A10 //L/preceding::*
    xpath = '/alpha:alphabet//L/preceding::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a11():
    # A11 //L/self::*
    xpath = '/alpha:alphabet//L/self::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a12():
    # A12 //L/child::*
    xpath = '/alpha:alphabet//L/child::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_axis_a13():
    # A13 //L/namespace::*
    # This returns namespace information not  data. Make sure it does not crash the server
    xpath = '/alpha:alphabet//L/namespace::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


# Filters
def test_get_xpath_filters_p1():
    # P1 //*[L]
    xpath = '/alpha:alphabet//*[L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p2():
    # P2 //*[parent::L]
    xpath = '/alpha:alphabet//*[parent::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p3():
    # P3 //*[descendant::L]
    xpath = '/alpha:alphabet//*[descendant::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p4():
    # P4 //*[descendant-or-self::L]
    xpath = '/alpha:alphabet//*[descendant-or-self::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p5():
    # P5 //*[ancestor::L]
    xpath = '/alpha:alphabet//*[ancestor::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p6():
    # P6 //*[ancestor-or-self::L]
    xpath = '/alpha:alphabet//*[ancestor-or-self::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p7():
    # P7 //*[following-sibling::L]
    xpath = '/alpha:alphabet//*[following-sibling::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p8():
    # P8 //*[preceding-sibling::L]
    xpath = '/alpha:alphabet//*[preceding-sibling::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p9():
    # P9 //*[following::L]
    xpath = '/alpha:alphabet//*[following::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p10():
    # P10 //*[preceding::L]
    xpath = '/alpha:alphabet//*[preceding::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p11():
    # P11 //*[self::L]
    xpath = '/alpha:alphabet//*[self::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p12():
    # P12 //*[./M]
    xpath = '/alpha:alphabet//*[./M]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_filters_p13():
    # P13 //*[../O]
    xpath = '/alpha:alphabet//*[../O]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


# Node Tests
def test_get_xpath_node_t1():
    # T1 //L/text()
    # We do not expect a result as no text is associated with the XML doc
    xpath = '/alpha:alphabet//L/text()'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_t2():
    # T2 //L/comment()
    # We do not expect a result as no comments are associated with the XML doc
    xpath = '/alpha:alphabet//L/comment()'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_t3():
    # T3 //L/processing-instruction()
    # We do not expect a result as no processing instructions are associated with the XML doc
    xpath = '/alpha:alphabet//L/processing-instruction()'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_t4():
    # T4 //L/processing-instruction("id")
    # We do not expect a result as no processing instructions are associated with the XML doc
    xpath = '/alpha:alphabet//L/processing-instruction("id")'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_t5():
    # T5 //L/node()
    xpath = '/alpha:alphabet//L/node()'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_t6():
    # T6 //L/N
    xpath = '/alpha:alphabet//L/N'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_t7():
    # //L/*
    xpath = '/alpha:alphabet//L/*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


# Operators
def test_get_xpath_operators_o1():
    # O1 //*[child::* and preceding::Q]
    xpath = '/alpha:alphabet//*[child::* and preceding::Q]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o2():
    # O2 //*[not(child::*) and preceding::Q]
    xpath = '/alpha:alphabet//*[not(child::*) and preceding::Q]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o3():
    # O3 //*[preceding::L or following::L]
    xpath = '/alpha:alphabet//*[preceding::L or following::L]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o4():
    # O4 //L/ancestor::* | //L/descendant::*
    xpath = '/alpha:alphabet//L/ancestor::* | /alpha:alphabet//L/descendant::*'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o5():
    # O5 //*[.="happy-go-lucky man"]
    xpath = '/alpha:alphabet//*[.="happy-go-lucky man"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <F>
          <H>
            <word>happy-go-lucky man</word>
          </H>
        </F>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o6():
    # O6 //*[pre > 12 and post < 15]
    xpath = '/alpha:alphabet//*[pre > 12 and post < 15]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o7():
    # O7 //*[pre != post]
    xpath = '/alpha:alphabet//*[pre != post]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o8():
    # O8 //*[((post * post + pre * pre) div (post + pre)) > ((post - pre) * (post - pre))]
    xpath = '/alpha:alphabet//*[((post * post + pre * pre) div (post + pre)) > ((post - pre) * (post - pre))]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o9():
    # O9 //*[pre mod 2 = 0]
    xpath = '/alpha:alphabet//*[pre mod 2 = 0]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_operators_o10():
    # O10 //*[pre >= 13 and post <= 14]
    xpath = '/alpha:alphabet//*[pre >= 13 and post <= 14]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


# Nothing matches this query so not expecting and data
def test_get_xpath_operators_o11():
    xpath = '/alpha:alphabet//*[pre >= 13 and post > 99]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


# Functions
def test_get_xpath_functions_f1():
    # F1 //*[contains(.,"plentiful")]
    xpath = '/alpha:alphabet//*[contains(.,"plentiful")]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f2():
    # F2 //*[starts-with(.,"plentiful")]
    xpath = '/alpha:alphabet//*[starts-with(.,"plentiful")]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <P>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f3():
    # F3 //*[substring(.,1,9) = "plentiful"]
    xpath = '/alpha:alphabet//*[substring(.,1,9) = "plentiful"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <P>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f4():
    # F4 //*[substring-after(.,"oven") = "ware"]
    xpath = '/alpha:alphabet//*[substring-after(.,"oven") = "ware"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f5():
    # F5 //*[substring-before(.,"ful") = "plenti"]
    xpath = '/alpha:alphabet//*[substring-before(.,"ful") = "plenti"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <P>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f6():
    # F6 //*[string-length(translate(normalize-space(.)," ","")) > 100]
    xpath = '/alpha:alphabet//*[string-length(translate(normalize-space(.)," ","")) > 100]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f8():
    # F8 //*[ceiling(pre div post) = 1]
    xpath = '/alpha:alphabet//*[ceiling(pre div post) = 1]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f9():
    # F9 //*[floor(pre div post) = 0]
    xpath = '/alpha:alphabet//*[floor(pre div post) = 0]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f10():
    # F10 //*[round(pre div post) = 0]
    xpath = '/alpha:alphabet//*[round(pre div post) = 0]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f11():
    # F11 //*[name(.) = "X"]
    xpath = '/alpha:alphabet//*[name(.) = "X"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f13():
    # F13 //L/child::*[last()]
    xpath = '/alpha:alphabet//L/child::*[last()]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f14():
    # F14 //L/descendant::*[17]
    xpath = '/alpha:alphabet//L/descendant::*[17]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f15():
    # F15 //L/ancestor::*[2]
    xpath = '/alpha:alphabet//L/ancestor::*[2]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f16():
    # F16 //L/following-sibling::*[1]
    xpath = '/alpha:alphabet//L/following-sibling::*[1]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f17():
    # F17 //L/preceding-sibling::*[1]
    xpath = '/alpha:alphabet//L/preceding-sibling::*[1]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f18():
    # F18 //L/following::*[29]
    xpath = '/alpha:alphabet//L/following::*[29]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f19():
    # F19 //L/preceding::*[36]
    xpath = '/alpha:alphabet//L/preceding::*[36]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <B>
        <D>
          <id>n4</id>
        </D>
      </B>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f20():
    # F20 //*[count(ancestor::*) > 5]
    xpath = '/alpha:alphabet//*[count(ancestor::*) > 5]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f21():
    # F21 //*[sum(ancestor::*/pre) < sum(descendant::*/pre)]
    xpath = '/alpha:alphabet//*[sum(ancestor::*/pre) < sum(descendant::*/pre)]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f24():
    # F24 //*[number(pre) < number(post)]
    xpath = '/alpha:alphabet//*[number(pre) < number(post)]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f25():
    # F25 //*[string(pre - 1) = "0"]
    xpath = '/alpha:alphabet//*[string(pre - 1) = "0"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <id>n1</id>
      <pre>1</pre>
      <post>26</post>
      <B>
        <id>n2</id>
        <pre>2</pre>
        <post>3</post>
        <C>
          <id>n3</id>
          <pre>3</pre>
          <post>1</post>
          <word>clergywoman</word>
        </C>
        <D>
          <id>n4</id>
          <pre>4</pre>
          <post>2</post>
          <word>decadent</word>
        </D>
      </B>
      <E>
        <id>n5</id>
        <pre>5</pre>
        <post>22</post>
        <F>
          <id>n6</id>
          <pre>6</pre>
          <post>6</post>
          <G>
            <id>n7</id>
            <pre>7</pre>
            <post>4</post>
            <word>gentility</word>
          </G>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <I>
          <id>n9</id>
          <pre>9</pre>
          <post>9</post>
          <J>
            <id>n10</id>
            <pre>10</pre>
            <post>7</post>
            <word>jigsaw</word>
          </J>
          <K>
            <id>n11</id>
            <pre>11</pre>
            <post>8</post>
            <word>kerchief</word>
          </K>
        </I>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
        <R>
          <id>n18</id>
          <pre>18</pre>
          <post>18</post>
          <S>
            <id>n19</id>
            <pre>19</pre>
            <post>16</post>
            <word>sage</word>
          </S>
          <T>
            <id>n20</id>
            <pre>20</pre>
            <post>17</post>
            <word>tattered</word>
          </T>
        </R>
        <U>
          <id>n21</id>
          <pre>21</pre>
          <post>21</post>
          <V>
            <id>n22</id>
            <pre>22</pre>
            <post>19</post>
            <word>volume</word>
          </V>
          <W>
            <id>n23</id>
            <pre>23</pre>
            <post>20</post>
            <word>wriggle</word>
          </W>
        </U>
      </E>
      <X>
        <id>n24</id>
        <pre>24</pre>
        <post>25</post>
        <Y>
          <id>n25</id>
          <pre>25</pre>
          <post>23</post>
          <word>yawn</word>
        </Y>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f26():
    # F26 //*[boolean(id) = true() and boolean(idrefs) = true()]
    xpath = '/alpha:alphabet//*[boolean(id) = true() and boolean(idrefs) = true()]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <F>
          <H>
            <id>n8</id>
            <pre>8</pre>
            <post>5</post>
            <idrefs>n17 n26</idrefs>
            <word>happy-go-lucky man</word>
          </H>
        </F>
        <L>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
      <X>
        <Z>
          <id>n26</id>
          <pre>26</pre>
          <post>24</post>
          <idrefs>n8 n17</idrefs>
          <word>zuzzurellone</word>
        </Z>
      </X>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f27():
    # F27 //L/*[position() = 4]
    xpath = '/alpha:alphabet//L/*[position() = 4]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f28():
    # F28 //L/*[local-name() = "id"]
    xpath = '/alpha:alphabet//L/*[local-name() = "id"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f29():
    # F29 //L/*[name() = "pre"]
    xpath = '/alpha:alphabet//L/*[name() = "pre"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <pre>12</pre>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f30():
    # F30 //L/*[namespace-uri() = ""]
    xpath = '/alpha:alphabet//L/*[namespace-uri() = ""]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <id>n12</id>
          <pre>12</pre>
          <post>15</post>
          <M>
            <id>n13</id>
            <pre>13</pre>
            <post>10</post>
          </M>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
          <Q>
            <id>n17</id>
            <pre>17</pre>
            <post>14</post>
            <idrefs>n8 n26</idrefs>
            <word>quarrelsome</word>
          </Q>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_functions_f31():
    # F31 //L/*[concat(pre, post) = "1413"]
    xpath = '/alpha:alphabet//L/*[concat(pre, post) = "1413"]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <alphabet xmlns="http://test.com/ns/yang/alphabet">
    <A>
      <E>
        <L>
          <N>
            <id>n14</id>
            <pre>14</pre>
            <post>13</post>
            <O>
              <id>n15</id>
              <pre>15</pre>
              <post>11</post>
              <word>ovenware</word>
            </O>
            <P>
              <id>n16</id>
              <pre>16</pre>
              <post>12</post>
              <word>plentiful</word>
            </P>
          </N>
        </L>
      </E>
    </A>
  </alphabet>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path():
    xpath = "/test/animals/animal[name='cat']/type/."
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
    <test xmlns="http://test.com/ns/yang/testing">
        <animals>
            <animal>
                <name>cat</name>
                <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
            </animal>
        </animals>
    </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path_dot_dot():
    xpath = "/test/animals/animal[name='hamster']/type/.."
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
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
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path_dot_dot_root():
    xpath = "/.."
    expected = """
XPATH: malformed filter
    """
    _get_test_with_filter_expect_error(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path_dot_dot_field():
    xpath = "/test/animals/animal[name='hamster']/type/../food"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>hamster</name>
        <food>
          <name>banana</name>
          <type>fruit</type>
        </food>
        <food>
          <name>nuts</name>
          <type>kibble</type>
        </food>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path_dot_dot_field_dot_dot():
    xpath = "/test/animals/animal[name='hamster']/type/../food/.."
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
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
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path_dot_dot_dot_dot():
    xpath = "/test/animals/animal[name='cat']/type/../.."
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
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
      </animal>
      <animal>
        <name>mouse</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:little</type>
        <colour>grey</colour>
      </animal>
      <animal>
        <name>parrot</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <colour>blue</colour>
        <toys>
          <toy>puzzles</toy>
          <toy>rings</toy>
        </toys>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_relative_path_dot_dot_dot_dot_dot_dot():
    xpath = "/test/animals/animal/../../.."
    expected = """
XPATH: malformed filter
    """
    _get_test_with_filter_expect_error(xpath, expected, f_type='xpath')


def test_get_xpath_slash_slash_ns():
    xpath = ("//mtu")
    nspace = 'xmlns:exam="http://example.com/ns/interfaces"'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <interfaces xmlns="http://example.com/ns/interfaces">
    <interface>
      <name>eth0</name>
      <mtu>8192</mtu>
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
    _get_test_with_filter(xpath, expected, f_ns=nspace, f_type='xpath')


# This query will return no data and not crash
def test_get_xpath_slash_star_ns():
    xpath = ("/*/mtu")
    nspace = 'xmlns:exam="http://example.com/ns/interfaces"'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0"/>
    """
    _get_test_with_filter(xpath, expected, f_ns=nspace, f_type='xpath')


def test_get_xpath_node_wildcard():
    xpath = '/test/animals/node()/name'
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
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_node_wildcard_2():
    xpath = "/test/animals/animal[name='hamster']/node()/name"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>hamster</name>
        <food>
          <name>banana</name>
        </food>
        <food>
          <name>nuts</name>
        </food>
      </animal>
    </animals>
  </test>
</nc:data>

    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_entry_leaf_node_1():
    xpath = "/test/animals/animal[name='hamster']"
    expected = """
    <nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <test xmlns="http://test.com/ns/yang/testing">
        <animals>
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
          </animal>
        </animals>
      </test>
    </nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_entry_leaf_node_2():
    xpath = "/test/animals/animal/name"
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
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_entry_leaf_node_3():
    xpath = "/test/animals/animal/colour"
    expected = """
    <nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <test xmlns="http://test.com/ns/yang/testing">
        <animals>
          <animal>
            <name>dog</name>
            <colour>brown</colour>
          </animal>
          <animal>
            <name>mouse</name>
            <colour>grey</colour>
          </animal>
          <animal>
            <name>parrot</name>
            <colour>blue</colour>
          </animal>
        </animals>
      </test>
    </nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_entry_leaf_node_4():
    xpath = "/test/animals/animal/toys"
    expected = """
    <nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <test xmlns="http://test.com/ns/yang/testing">
        <animals>
          <animal>
            <name>parrot</name>
            <toys>
              <toy>puzzles</toy>
              <toy>rings</toy>
            </toys>
          </animal>
        </animals>
      </test>
    </nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_entry_leaf_node_5():
    xpath = "/test/animals/animal/food/name"
    expected = """
    <nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
      <test xmlns="http://test.com/ns/yang/testing">
        <animals>
          <animal>
            <name>hamster</name>
            <food>
              <name>banana</name>
            </food>
            <food>
              <name>nuts</name>
            </food>
          </animal>
        </animals>
      </test>
    </nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_proxy_list_select_one_trunk():
    apteryx.set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx.set("/logical-elements/logical-element/loop/root", "root")
    apteryx.set("/apteryx/sockets/E18FE205", "tcp://127.0.0.1:9999")
#     apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    apteryx.proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    xpath = "/logical-elements/logical-element[name='loopy']/test/animals/animal[name='cat']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <logical-elements xmlns="http://example.com/ns/logical-elements">
    <logical-element>
      <name>loopy</name>
      <test xmlns="http://test.com/ns/yang/testing">
        <animals>
          <animal>
            <name>cat</name>
            <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
          </animal>
        </animals>
      </test>
    </logical-element>
  </logical-elements>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_when_derived_from():
    apteryx.set("/test/animals/animal/cat/n-type", "big")
    xpath = "/test/animals/animal[name='cat']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <n-type>big</n-type>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_when_condition_true():
    apteryx.set("/test/animals/animal/wombat/name", "wombat")
    apteryx.set("/test/animals/animal/cat/claws", "5")
    xpath = "/test/animals/animal[name='cat']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
        <claws>5</claws>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_when_condition_false():
    apteryx.set("/test/animals/animal/cat/claws", "5")
    xpath = "/test/animals/animal[name='cat']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_must_condition_true():
    apteryx.set("/test/animals/animal/dog/friend", "ben")
    xpath = "/test/animals/animal[name='dog']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
        <friend>ben</friend>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_must_condition_false():
    apteryx.set("/test/animals/animal/dog/friend", "ben")
    apteryx.prune("/test/animals/animal/cat")
    xpath = "/test/animals/animal[name='dog']"
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>dog</name>
        <colour>brown</colour>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')


def test_get_xpath_list_trunk_predicate_one():
    xpath = '/test/animals/animal[1]'
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="http://test.com/ns/yang/testing">
    <animals>
      <animal>
        <name>cat</name>
        <type xmlns="http://test.com/ns/yang/animal-types">a-types:big</type>
      </animal>
    </animals>
  </test>
</nc:data>
    """
    _get_test_with_filter(xpath, expected, f_type='xpath')
