from conftest import _get_test_with_defaults_and_filter


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
