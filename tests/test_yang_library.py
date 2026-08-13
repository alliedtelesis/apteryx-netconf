from conftest import _get_test_with_filter, toXML, diffXML
from lxml import etree


# ietf-yang-library
# module: ietf-yang-library
#   +--ro yang-library
#   |  +--ro module-set* [name]
#   |  |  +--ro name                  string
#   |  |  +--ro module* [name]
#   |  |  |  +--ro name         yang:yang-identifier
#   |  |  |  +--ro revision?    revision-identifier
#   |  |  |  +--ro namespace    inet:uri
#   |  |  |  +--ro location*    inet:uri
#   |  |  |  +--ro submodule* [name]
#   |  |  |  |  +--ro name        yang:yang-identifier
#   |  |  |  |  +--ro revision?   revision-identifier
#   |  |  |  |  +--ro location*   inet:uri
#   |  |  |  +--ro feature*     yang:yang-identifier
#   |  |  |  +--ro deviation*   -> ../../module/name
#   |  |  +--ro import-only-module* [name revision]
#   |  |     +--ro name         yang:yang-identifier
#   |  |     +--ro revision     union
#   |  |     +--ro namespace    inet:uri
#   |  |     +--ro location*    inet:uri
#   |  |     +--ro submodule* [name]
#   |  |        +--ro name        yang:yang-identifier
#   |  |        +--ro revision?   revision-identifier
#   |  |        +--ro location*   inet:uri
#   |  +--ro schema* [name]
#   |  |  +--ro name          string
#   |  |  +--ro module-set*   -> ../../module-set/name
#   |  +--ro datastore* [name]
#   |  |  +--ro name      ds:datastore-ref
#   |  |  +--ro schema    -> ../../schema/name
#   |  +--ro content-id    string
def test_netconf_yang_library_tree():
    select = '<yang-library xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-library"/>'
    xml = _get_test_with_filter(select)
    _xml = xml
    print(etree.tostring(_xml, pretty_print=True, encoding="unicode"))
    contentid = _xml.find('./{*}yang-library/{*}content-id').text
    expected = """
<nc:data xmlns:nc="urn:ietf:params:xml:ns:netconf:base:1.0">
  <yang-library xmlns="urn:ietf:params:xml:ns:yang:ietf-yang-library">
    <module-set>
      <name>common</name>
      <module>
        <name>alphabet</name>
        <revision>2023-01-01</revision>
        <namespace>http://test.com/ns/yang/alphabet</namespace>
      </module>
      <module>
        <name>example</name>
        <revision>2023-04-04</revision>
        <namespace>http://example.com/ns/interfaces</namespace>
        <feature>ether</feature>
        <feature>fast</feature>
        <deviation>user-example-deviation</deviation>
      </module>
      <module>
        <name>ietf-yang-library</name>
        <revision>2019-01-04</revision>
        <namespace>urn:ietf:params:xml:ns:yang:ietf-yang-library</namespace>
      </module>
      <module>
        <name>logical-elements</name>
        <revision>2024-04-04</revision>
        <namespace>http://example.com/ns/logical-elements</namespace>
      </module>
      <module>
        <name>testing</name>
        <revision>2023-01-01</revision>
        <namespace>http://test.com/ns/yang/testing</namespace>
        <feature>dummy</feature>
        <feature>test-time</feature>
      </module>
      <module>
        <name>testing-2</name>
        <revision>2023-02-01</revision>
        <namespace>http://test.com/ns/yang/testing-2</namespace>
      </module>
      <module>
        <name>testing-3</name>
        <revision>2023-03-01</revision>
        <namespace>http://test.com/ns/yang/testing-3</namespace>
      </module>
      <module>
        <name>testing-4</name>
        <revision>2024-02-01</revision>
        <namespace>http://test.com/ns/yang/testing-4</namespace>
      </module>
      <module>
        <name>testing2-augmented</name>
        <revision>2023-02-02</revision>
        <namespace>http://test.com/ns/yang/testing2-augmented</namespace>
      </module>
    </module-set>
    <schema>
      <name>common</name>
      <module-set>common</module-set>
    </schema>
    <datastore>
      <name>ietf-datastores:running</name>
      <schema>common</schema>
    </datastore>
    <content-id>%s</content-id>
  </yang-library>
</nc:data>
    """ % (contentid)
    expected = toXML(expected)
    assert diffXML(xml, expected) is None
