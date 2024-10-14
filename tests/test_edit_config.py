import pytest
from ncclient.operations import RPCError
from lxml import etree
from conftest import connect, apteryx_set, apteryx_proxy

# EDIT-CONFIG


def _error_check(err, expect_err):
    assert err is not None
    assert err.tag == expect_err["tag"]
    assert err.type == expect_err["type"]
    assert err.severity == "error"
    if "message" in expect_err:
        assert err.message == expect_err["message"]


def _edit_config_test(payload, expect_err=None, post_xpath=None, targ="running", inc_str=[], exc_str=[]):
    """
    Run an edit-config with the given payload, optionally checking for error, and
    strings that should be included or excluded in the response,
    returning the response from a get carried out with the optional given xpath.
    """
    m = connect()
    xml = None
    try:
        response = m.edit_config(target=targ, config=payload)
        print(response)
    except RPCError as err:
        print(err)
        assert expect_err is not None
        _error_check(err, expect_err)
    else:
        assert expect_err is None
        if post_xpath is not None:
            xml = m.get(filter=('xpath', post_xpath)).data
            print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
            if len(inc_str) + len(exc_str) != 0:
                for s in inc_str:
                    assert s in etree.XPath("//text()")(xml)
                for s in exc_str:
                    assert s not in etree.XPath("//text()")(xml)
    finally:
        m.close_session()
    return xml


def test_edit_config_node():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <priority>5</priority>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/priority')
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '5'


def test_edit_config_bad_target():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <priority>5</priority>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, targ="candidate",
                      expect_err={"tag": "operation-not-supported", "type": "protocol"})


def test_edit_config_bad_operation():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <priority xc:operation="bob">5</priority>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "unknown-attribute", "type": "protocol"})


def test_edit_config_non_writable():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <state>
        <counter>7734</counter>
    </state>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_multi():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <enable>false</enable>
        <priority>4</priority>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings')
    assert xml.find('./{*}test/{*}settings/{*}enable').text == 'false'
    assert xml.find('./{*}test/{*}settings/{*}priority').text == '4'


def test_edit_config_list():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>frog</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", inc_str=["frog"])


def test_edit_config_toplevel_list():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test-list>
    <index>1</index>
    <name>frog</name>
  </test-list>
</config>
"""
    _edit_config_test(payload, post_xpath="/test-list", inc_str=["frog"])


def test_edit_config_list_key_colon():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>frog:y</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", inc_str=["frog:y"])


def test_edit_config_list_key_slash():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>frog/y</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", inc_str=["frog/y"])


# EDIT-CONFIG (operation="delete")


def test_edit_config_delete_invalid_path():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <missing xc:operation="delete">1</missing>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "malformed-message", "type": "rpc"})


def test_edit_config_delete_node():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <priority xc:operation="delete">1</priority>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/priority')
    assert xml.find('./{*}test/{*}settings/{*}priority') is None


def test_edit_config_delete_no_data():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <priority xc:operation="delete"></priority>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath='/test/settings', exc_str=["priority"])


def test_edit_config_delete_multi():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <enable xc:operation="delete">true</enable>
        <priority xc:operation="delete">1</priority>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath='/test/settings', exc_str=['<enable>', '<priority>'])


@pytest.mark.skip(reason="does not work yet")
def test_edit_config_delete_trunk():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings xc:operation="delete"/>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings')
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert etree.XPath("//text()")(xml) == []


def test_edit_config_delete_missing():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
      <animal xc:operation="delete">
        <name>unicorn</name>
      </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "data-missing", "type": "application"})


def test_edit_config_delete_list():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal xc:operation="delete">
            <name>cat</name>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", exc_str=["cat"])


def test_edit_config_delete_list_slash():
    apteryx_set("/test/animals/animal/cat%2Fbell/name", "cat/bell")
    apteryx_set("/test/animals/animal/cat%2Fbell/type", "little")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal xc:operation="delete">
            <name>cat/bell</name>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", exc_str=["cat/bell"])


def test_edit_config_delete_toplevel_list():
    apteryx_set("/test-list/1/index", "1")
    apteryx_set("/test-list/1/name", "cat")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test-list xc:operation="delete">
    <index>1</index>
  </test-list>
</config>
"""
    _edit_config_test(payload, post_xpath="/test-list", exc_str=["cat"])


def test_edit_config_delete_leaf_list_item():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys>
              <toy xc:operation="delete">rings</toy>
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["puzzles"], exc_str=["rings"])


def test_edit_config_delete_leaf_list_item_slash():
    apteryx_set("/test/animals/animal/parrot/toys/toy/toy%2Frings", "toy/rings")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys>
              <toy xc:operation="delete">toy/rings</toy>
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["puzzles"], exc_str=["toy/rings"])


def test_edit_config_delete_leaf_list():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys xc:operation="delete">
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot", exc_str=["rings", "puzzles"])


def test_edit_config_merge_delete():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <enable>false</enable>
        <priority xc:operation="delete">1</priority>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings')
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert etree.XPath("//text()")(xml) == ['enable', 'false', 'bob', '34', 'true', '2', '23', '1']


# EDIT-CONFIG (operation=replace)
#  replace:  The configuration data identified by the element
#     containing this attribute replaces any related configuration
#     in the configuration datastore identified by the <target>
#     parameter.  If no such configuration data exists in the
#     configuration datastore, it is created.  Unlike a
#     <copy-config> operation, which replaces the entire target
#     configuration, only the configuration actually present in
#     the <config> parameter is affected.

def test_edit_config_replace_list_item():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal xc:operation="replace">
            <name>cat</name>
            <colour>brown</colour>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal[name='cat']", inc_str=["brown"], exc_str=["big"])


def test_edit_config_replace_all():
    """
    Replace all animals with one (existing) animal.
    """
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals xc:operation="replace">
      <animal>
        <name>cat</name>
        <type>big</type>
        <colour>tawny</colour>
      </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath='/test/animals', inc_str=["cat"], exc_str=["dog", "mouse"])


def test_edit_config_replace_one_full():
    """
    Replace one animal. Fully specify the replacement.
    """
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
      <animal xc:operation="replace">
        <name>cat</name>
        <type>little</type>
        <colour>tawny</colour>
      </animal>
    </animals>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/animals', inc_str=["cat", "dog", "mouse"])
    assert xml.find('./{*}test/{*}animals/{*}animal[{*}name="cat"]/{*}type').text == 'a-types:little'
    assert xml.find('./{*}test/{*}animals/{*}animal[{*}name="cat"]/{*}colour').text == 'tawny'


@pytest.mark.skip(reason="nothing found, no defaults even")
def test_edit_config_replace_one_default():
    """
    Replace one animal. Allow all values to revert to default.
    """
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
      <animal xc:operation="replace">
        <name>mouse</name>
      </animal>
    </animals>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/animals', inc_str=["cat", "dog", "mouse"])
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert xml.find('./{*}test/{*}animals/{*}animal[name="mouse"]/{*}type').text == 'big'
    assert xml.find('./{*}test/{*}animals/{*}animal[name="mouse"]/{*}colour') is None


def test_edit_config_replace_leaf_list():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys xc:operation="replace">
              <toy>bell</toy>
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["bell"])


# EDIT-CONFIG (operation=create)
#  create:  The configuration data identified by the element
#     containing this attribute is added to the configuration if
#     and only if the configuration data does not already exist in
#     the configuration datastore.  If the configuration data
#     exists, an <rpc-error> element is returned with an
#     <error-tag> value of "data-exists".

def test_edit_config_create_list_item():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal xc:operation="create">
            <name>penguin</name>
            <type>big</type>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", inc_str=["penguin"])


def test_edit_config_create_list_item_exists():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal xc:operation="create">
            <name>cat</name>
            <type>little</type>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "data-exists", "type": "application"})


def test_edit_config_create_list_item_field():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <colour xc:operation="create">white</colour>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals", inc_str=["white"])


def test_edit_config_create_list_item_field_exists():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <type xc:operation="create">little</type>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "data-exists", "type": "application"})


def test_edit_config_create_leaf_list_item():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys>
              <toy xc:operation="create">bell</toy>
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["bell"])


def test_edit_config_create_leaf_list_item_slash():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys>
              <toy xc:operation="create">cat/bell</toy>
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["cat/bell"])


def test_edit_config_create_toplevel_leaf_list_item():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test-leaflist xmlns="http://test.com/ns/yang/testing" xc:operation="create">bell</test-leaflist>
</config>
"""
    _edit_config_test(payload, post_xpath="/test-leaflist", inc_str=["bell"])


# EDIT-CONFIG (operation=remove)
#  remove:  The configuration data identified by the element
#     containing this attribute is deleted from the configuration
#     if the configuration data currently exists in the
#     configuration datastore.  If the configuration data does not
#     exist, the "remove" operation is silently ignored by the
#     server.

def test_edit_config_remove_invalid_path():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
        <missing xc:operation="remove">1</missing>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "malformed-message", "type": "rpc"})


def test_edit_config_remove_missing_data():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
      <animal>
        <dog>
          <colour xc:operation="remove">brown</colour>
        </dog>
      </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "malformed-message", "type": "rpc"})


def test_edit_config_remove_leaf_list_item():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>parrot</name>
            <toys>
              <toy xc:operation="remove">rings</toy>
            </toys>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["puzzles"], exc_str=["rings"])


def test_edit_config_remove_toplevel_leaf_list_item():
    apteryx_set("/test-leaflist/cat", "cat")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test-leaflist xmlns="http://test.com/ns/yang/testing" xc:operation="remove">cat</test-leaflist>
</config>
"""
    _edit_config_test(payload, post_xpath="/test-leaflist", exc_str=["cat"])


# Empty value for nodes that have a non-empty pattern or values

def test_edit_config_invalid_empty_merge():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <debug></debug>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_invalid_empty_replace():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <debug xc:operation="replace"></debug>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_empty_delete():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <enable xc:operation="delete"></enable>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/enable')
    print(etree.tostring(xml, pretty_print=True, encoding="unicode"))
    assert etree.XPath("//text()")(xml) == []


def test_edit_config_proxy_named_element():
    apteryx_set("/logical-elements/logical-element/loop/name", "loopy")
    apteryx_set("/logical-elements/logical-element/loop/root", "root")
    apteryx_set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx_proxy("/logical-elements/logical-element/loopy/*", "tcp://127.0.0.1:9999")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <logical-elements>
    <logical-element>
      <name>loopy</name>
      <test>
        <animals>
          <animal>
              <name>parrot</name>
              <toys>
                <toy xc:operation="create">bell</toy>
              </toys>
          </animal>
        </animals>
      </test>
    </logical-element>
  </logical-elements>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal/parrot/toys", inc_str=["bell"])


def test_edit_config_proxy_named_element_read_only():
    apteryx_set("/logical-elements/logical-element-ro/loop/name", "loopy")
    apteryx_set("/logical-elements/logical-element-ro/loop/root", "root")
    apteryx_set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx_proxy("/logical-elements/logical-element-ro/loopy/*", "tcp://127.0.0.1:9999")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <logical-elements>
    <logical-element-ro>
      <name>loopy</name>
      <test>
        <animals>
          <animal>
              <name>parrot</name>
              <toys>
                <toy xc:operation="create">bell</toy>
              </toys>
          </animal>
        </animals>
      </test>
    </logical-element-ro>
  </logical-elements>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_proxy_remove_leaf_list_item_read_only():
    apteryx_set("/logical-elements/logical-element-ro/loop/name", "loopy")
    apteryx_set("/logical-elements/logical-element-ro/loop/root", "root")
    apteryx_set("/apteryx/sockets/E18FE205",  "tcp://127.0.0.1:9999")
    apteryx_proxy("/logical-elements/logical-element-ro/loopy/*", "tcp://127.0.0.1:9999")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <logical-elements>
    <logical-element-ro>
      <name>loopy</name>
        <test>
          <animals>
              <animal>
                  <name>parrot</name>
                  <toys>
                    <toy xc:operation="remove">rings</toy>
                  </toys>
              </animal>
          </animals>
        </test>
    </logical-element-ro>
  </logical-elements>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_if_feature_false():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <magictime>
        <days>1</days>
      </magictime>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_if_feature_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <testtime>
        <days>1</days>
      </testtime>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/testtime/days')
    assert xml.find('./{*}test/{*}settings/{*}testtime/{*}days').text == '1'


def test_edit_config_if_feature_or_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <testtime>
        <hours>2</hours>
      </testtime>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/testtime/hours')
    assert xml.find('./{*}test/{*}settings/{*}testtime/{*}hours').text == '2'


def test_edit_config_if_feature_or_or_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <testtime>
        <minutes>10</minutes>
      </testtime>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/testtime/minutes')
    assert xml.find('./{*}test/{*}settings/{*}testtime/{*}minutes').text == '10'


def test_edit_config_if_feature_or_or_false():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <testtime>
        <seconds>20</seconds>
      </testtime>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_create_when_condition_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>dog</name>
            <houses>
              <house xc:operation="create">kennel</house>
            </houses>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal[name='dog']", inc_str=["kennel"])


def test_edit_config_create_when_condition_false():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <houses>
              <house xc:operation="create">cat house</house>
            </houses>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_when_condition_true():
    apteryx_set("/test/animals/animal/wombat/name", "wombat")
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <claws>5</claws>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal[name='cat']", inc_str=["5"])


def test_edit_config_when_condition_false():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>cat</name>
            <claws>5</claws>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_when_name_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <complextime>
        <hours>7</hours>
      </complextime>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/complextime/hours')
    assert xml.find('./{*}test/{*}settings/{*}complextime/{*}hours').text == '7'


def test_edit_config_when_name_false():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <complextime>
        <minutes>6</minutes>
      </complextime>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_when_count_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <complextime>
        <seconds>9</seconds>
      </complextime>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/complextime/seconds')
    assert xml.find('./{*}test/{*}settings/{*}complextime/{*}seconds').text == '9'


def test_edit_config_when_path_exists():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <complextime>
        <days>2</days>
      </complextime>
    </settings>
  </test>
</config>
"""
    xml = _edit_config_test(payload, post_xpath='/test/settings/complextime/days')
    assert xml.find('./{*}test/{*}settings/{*}complextime/{*}days').text == '2'


def test_edit_config_must_condition_true():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
        <animal>
            <name>dog</name>
            <friend>ben</friend>
        </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath="/test/animals/animal[name='dog']", inc_str=["ben"])


def test_edit_config_must_condition_false():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <animals>
      <animal xc:operation="delete">
        <name>cat</name>
      </animal>
      <animal>
        <name>dog</name>
        <friend xc:operation="merge">ben</friend>
      </animal>
    </animals>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_leaf_list_invalid_value():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <users>
        <name>bob</name>
        <groups>admin</groups>
        <groups>software</groups>
      </users>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, expect_err={"tag": "invalid-value", "type": "protocol"})


def test_edit_config_leaf_list_valid_value():
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0"
        xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test>
    <settings>
      <users>
        <name>bob</name>
        <groups>123</groups>
        <groups>321</groups>
      </users>
    </settings>
  </test>
</config>
"""
    _edit_config_test(payload, post_xpath='/test/settings/users[name="bob"]', inc_str=['123', '321'])
