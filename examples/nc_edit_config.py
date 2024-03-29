#!/usr/bin/env python3
from ncclient import manager
from ncclient.operations import RPCError

m = manager.connect(host='localhost',
                    port=830,
                    username='manager',
                    password='friend',
                    hostkey_verify=False,
                    allow_agent=False,
                    look_for_keys=False)

try:
    payload = """
<config xmlns:xc="urn:ietf:params:xml:ns:netconf:base:1.0" xmlns="urn:ietf:params:xml:ns:netconf:base:1.0">
  <test xmlns="https://github.com/alliedtelesis/apteryx">
    <debug>enable</debug>
    <counter>33</counter>
  </test>
</config>
"""
    response = m.edit_config(target='running', config=payload).xml
except RPCError as e:
    response = e.message
finally:
    print(response)
    m.close_session()
