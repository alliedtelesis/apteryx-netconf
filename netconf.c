/**
 * @file netconf.c
 * libnetconf2 to Apteryx glue
 *
 * Copyright 2019, Allied Telesis Labs New Zealand, Ltd
 *
 * This library is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 3 of the License, or (at your option) any later version.
 *
 * This library is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this library. If not, see <http://www.gnu.org/licenses/>
 */
#include "internal.h"
#define __USE_GNU
#include <sys/socket.h>
#include <pwd.h>
#define APTERYX_XML_LIBXML2
#include <apteryx-xml.h>

#define DEFAULT_LANG "en"

static sch_instance *g_schema = NULL;

struct netconf_session
{
    int fd;
    uint32_t id;
    char *username;
    gchar *rem_addr;
    gchar *rem_port;
    gchar *login_time;
    bool running;
};

static struct _running_ds_lock_t
{
    struct netconf_session nc_sess;
    gboolean locked;
} running_ds_lock;

#define NETCONF_BASE_1_0_END "]]>]]>"
#define NETCONF_BASE_1_1_END "\n##\n"
#define NETCONF_HELLO_END "hello>]]>]]>"
#define NETCONF_HELLO_END_LEN 12
#define HELLO_RX_SIZE 1024
#define MAX_HELLO_RX_SIZE 16384

#define NETCONF_STATE_SESSIONS_PATH "/netconf-state/sessions/session"
#define NETCONF_SESSION_STATUS "/netconf-state/sessions/session/*/status"
#define NETCONF_CONFIG_MAX_SESSIONS "/netconf/config/max-sessions"
#define NETCONF_STATE "/netconf/state"

/* Defines for the max-sessions variable - the maximum number of sessions allowed */
#define NETCONF_MAX_SESSIONS_MIN 1
#define NETCONF_MAX_SESSIONS_MAX 10
#define NETCONF_MAX_SESSIONS_DEF 4

static uint32_t netconf_session_id = 1;
static uint32_t netconf_max_sessions = NETCONF_MAX_SESSIONS_DEF;
static uint32_t netconf_num_sessions = 0;

/* Maintain a list of open sessions */
static GList *open_sessions_list = NULL;
GMutex session_lock;

static void
_set_xmlns (xmlNode* node)
{
    xmlNs *ns = xmlNewNs (node, BAD_CAST "urn:ietf:params:xml:ns:netconf:base:1.0", BAD_CAST "nc");
    xmlSetNs (node, ns);
}

/* Error handling helper routines */
static const char*
rpc_error_tag_to_msg (NC_ERR_TAG err_tag)
{
    switch (err_tag)
    {
    case NC_ERR_TAG_IN_USE:
        return "Resource is already in use";
    case NC_ERR_TAG_INVALID_VAL:
        return "Unacceptable value for one or more parameters";
    case NC_ERR_TAG_TOO_BIG:
        return "The request is too large to be handled";
    case NC_ERR_TAG_MISSING_ATTR:
        return "An expected attribute is missing";
    case NC_ERR_TAG_BAD_ATTR:
        return "An attribute value is not correct";
    case NC_ERR_TAG_UNKNOWN_ATTR:
        return "An unexpected attribute is present";
    case NC_ERR_TAG_MISSING_ELEM:
        return "An expected element is missing";
    case NC_ERR_TAG_BAD_ELEM:
        return "An element value is not correct";
    case NC_ERR_TAG_UNKNOWN_ELEM:
        return "An unexpected element is present";
    case NC_ERR_TAG_UNKNOWN_NS:
        return "An unexpected namespace is present";
    case NC_ERR_TAG_ACCESS_DENIED:
        return "Access to the requested resource is denied due to authorization failure";
    case NC_ERR_TAG_LOCK_DENIED:
        return "Access to the requested lock is denied because the lock is currently held by another entity";
    case NC_ERR_TAG_RESOURCE_DENIED:
        return "Request could not be completed because of insufficient resources";
    case NC_ERR_TAG_DATA_EXISTS:
        return "Requested data model content already exists";
    case NC_ERR_TAG_DATA_MISSING:
        return "Requested data model content does not exist";
    case NC_ERR_TAG_OPR_NOT_SUPPORTED:
        return "Requested operation is not supported by this implementation";
    case NC_ERR_TAG_OPR_FAILED:
        return "Requested operation failed due to some reason";
    case NC_ERR_TAG_MALFORMED_MSG:
        return "Failed to parse XML message";
    default:
        return NULL;
    }
}

static const char*
rpc_error_tag_to_string (NC_ERR_TAG err_tag)
{
    switch (err_tag)
    {
    case NC_ERR_TAG_IN_USE:
        return "in-use";
    case NC_ERR_TAG_INVALID_VAL:
        return "invalid-value";
    case NC_ERR_TAG_TOO_BIG:
        return "too-big";
    case NC_ERR_TAG_MISSING_ATTR:
        return "missing-attribute";
    case NC_ERR_TAG_BAD_ATTR:
        return "bad-attribute";
    case NC_ERR_TAG_UNKNOWN_ATTR:
        return "unknown-attribute";
    case NC_ERR_TAG_MISSING_ELEM:
        return "missing-element";
    case NC_ERR_TAG_BAD_ELEM:
        return "bad-element";
    case NC_ERR_TAG_UNKNOWN_ELEM:
        return "unknown-element";
    case NC_ERR_TAG_UNKNOWN_NS:
        return "unknown-namespace";
    case NC_ERR_TAG_ACCESS_DENIED:
        return "access-denied";
    case NC_ERR_TAG_LOCK_DENIED:
        return "lock-denied";
    case NC_ERR_TAG_RESOURCE_DENIED:
        return "resource-denied";
    case NC_ERR_TAG_DATA_EXISTS:
        return "data-exists";
    case NC_ERR_TAG_DATA_MISSING:
        return "data-missing";
    case NC_ERR_TAG_OPR_NOT_SUPPORTED:
        return "operation-not-supported";
    case NC_ERR_TAG_OPR_FAILED:
        return "operation-failed";
    case NC_ERR_TAG_MALFORMED_MSG:
        return "malformed-message";
    default:
        return NULL;
    }
}

static const char*
rpc_error_type_to_string (NC_ERR_TYPE err_type)
{
    switch (err_type)
    {
    case NC_ERR_TYPE_TRANSPORT:
        return "transport";
    case NC_ERR_TYPE_RPC:
        return "rpc";
    case NC_ERR_TYPE_PROTOCOL:
        return "protocol";
    case NC_ERR_TYPE_APP:
        return "application";
    default:
        return NULL;
    }
}

static xmlNode *
_create_error_info_xml (nc_error_parms parms)
{
    xmlNode *xml_err_info = xmlNewNode (NULL, BAD_CAST "error-info");
    _set_xmlns(xml_err_info);

    if (parms.tag == NC_ERR_TAG_UNKNOWN_NS)
    {
        char *bad_ns = NULL;
        char *bad_elem = NULL;
        bad_ns = g_hash_table_lookup (parms.info, "bad-namespace");
        bad_elem = g_hash_table_lookup (parms.info, "bad-element");
        if (bad_ns && bad_elem)
        {
            xmlNewChild (xml_err_info, NULL, BAD_CAST "bad-namespace", BAD_CAST bad_ns);
            xmlNewChild (xml_err_info, NULL, BAD_CAST "bad-element", BAD_CAST bad_elem);
        }

    }
    else if (parms.tag == NC_ERR_TAG_IN_USE || parms.tag == NC_ERR_TAG_LOCK_DENIED)
    {
        char *session_id = NULL;
        session_id = g_hash_table_lookup (parms.info, "session-id");
        if (session_id)
        {
            xmlNewChild (xml_err_info, NULL, BAD_CAST "session-id", BAD_CAST session_id);
        }
    }
    else if (parms.tag == NC_ERR_TAG_MISSING_ATTR || parms.tag == NC_ERR_TAG_BAD_ATTR ||
             parms.tag == NC_ERR_TAG_UNKNOWN_ATTR)
    {
        char *bad_attr = NULL;
        char *bad_elem = NULL;
        bad_attr = g_hash_table_lookup (parms.info, "bad-attribute");
        bad_elem = g_hash_table_lookup (parms.info, "bad-element");
        if (bad_elem && bad_attr)
        {
            xmlNewChild (xml_err_info, NULL, BAD_CAST "bad-attribute", BAD_CAST bad_attr);
            xmlNewChild (xml_err_info, NULL, BAD_CAST "bad-element", BAD_CAST bad_elem);
        }
    }
    else if (parms.tag == NC_ERR_TAG_MISSING_ELEM || parms.tag == NC_ERR_TAG_BAD_ELEM ||
             parms.tag == NC_ERR_TAG_UNKNOWN_ELEM)
    {
        char *bad_elem = NULL;
        bad_elem = g_hash_table_lookup (parms.info, "bad-element");
        if (bad_elem)
        {
            xmlNewChild (xml_err_info, NULL, BAD_CAST "bad-element", BAD_CAST bad_elem);
        }
    }

    return xml_err_info;
}

static void
_free_error_parms (nc_error_parms error_parms)
{
    error_parms.tag = 0;
    error_parms.type = 0;
    g_string_free (error_parms.msg, TRUE);
    g_hash_table_destroy (error_parms.info);
}


/* Close open sessions */
void
netconf_close_open_sessions (void)
{
    if (open_sessions_list)
    {
        for (GList *iter = open_sessions_list; iter; iter = g_list_next (iter))
        {
            struct netconf_session *nc_session = iter->data;
            if (nc_session && nc_session->fd >= 0)
            {
                close (nc_session->fd);
                nc_session->fd = -1;
            }
        }
    }
}

/**
 * Remove specified netconf session from open_sessions_list. Can't guarantee
 * that the passed in session is the one on the list, hence the search by ID.
 */
static void
remove_netconf_session (struct netconf_session *session)
{
    if (!session || !open_sessions_list)
    {
        return;
    }

    g_mutex_lock (&session_lock);
    for (GList *iter = open_sessions_list; iter; iter = g_list_next (iter))
    {
        struct netconf_session *nc_session = iter->data;
        if (nc_session && session->id == nc_session->id)
        {
            open_sessions_list = g_list_remove (open_sessions_list, nc_session);
            netconf_num_sessions--;
            break;
        }
    }
    g_mutex_unlock (&session_lock);
}

/* Find open netconf session details by ID */
static struct netconf_session *
find_netconf_session_by_id (uint32_t session_id)
{
    struct netconf_session *ret = NULL;
    g_mutex_lock (&session_lock);
    for (GList *iter = open_sessions_list; iter; iter = g_list_next (iter))
    {
        struct netconf_session *nc_session = iter->data;
        if (nc_session && session_id == nc_session->id)
        {
            ret = nc_session;
            break;
        }
    }
    g_mutex_unlock (&session_lock);

    return ret;
}

static xmlDoc*
create_rpc (xmlChar *type, xmlChar *msg_id)
{
    xmlDoc *doc = xmlNewDoc (BAD_CAST "1.0");
    xmlNode *root = xmlNewNode (NULL, type);
    xmlNs *ns = xmlNewNs (root, BAD_CAST "urn:ietf:params:xml:ns:netconf:base:1.0", BAD_CAST "nc");
    xmlSetNs (root, ns);
    if (msg_id)
    {
        xmlSetProp (root, BAD_CAST "message-id", msg_id);
        free (msg_id);
    }
    xmlDocSetRootElement (doc, root);
    return doc;
}

static bool
send_rpc_ok (struct netconf_session *session, xmlNode * rpc, bool closing)
{
    xmlDoc *doc;
    xmlChar *xmlbuff = NULL;
    char *header = NULL;
    int len;
    bool ret = true;

    /* Generate reply */
    doc = create_rpc (BAD_CAST "rpc-reply", xmlGetProp (rpc, BAD_CAST "message-id"));
    xmlNewChild (xmlDocGetRootElement (doc), NULL, BAD_CAST "ok", NULL);
    xmlDocDumpMemoryEnc (doc, &xmlbuff, &len, "UTF-8");
    header = g_strdup_printf ("\n#%d\n", len);

    /* Send reply */
    if (write (session->fd, header, strlen (header)) != strlen (header))
    {
        if (!closing)
        {
            ERROR ("TX failed: Sending %ld bytes of header\n", strlen (header));
        }
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s", strlen (header), header);
    if (write (session->fd, xmlbuff, len) != len)
    {
        if (!closing)
        {
            ERROR ("TX failed: Sending %d bytes of hello\n", len);
        }
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%d):\n%.*s", len, len, (char *) xmlbuff);
    if (write (session->fd, NETCONF_BASE_1_1_END, strlen (NETCONF_BASE_1_1_END)) !=
        strlen (NETCONF_BASE_1_1_END))
    {
        if (!closing)
        {
            ERROR ("TX failed: Sending %ld bytes of trailer\n",
                   strlen (NETCONF_BASE_1_1_END));
        }
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s\n", strlen (NETCONF_BASE_1_1_END), NETCONF_BASE_1_1_END);

  cleanup:
    g_free (header);
    xmlFree (xmlbuff);
    xmlFreeDoc (doc);
    return ret;
}

/**
 * Actually send the RPC error message - all information is contained in the nc_error_parms structure.
 */
static bool
_send_rpc_error (struct netconf_session *session, xmlNode * rpc, nc_error_parms error_parms)
{
    xmlDoc *doc;
    xmlNode *child;
    xmlNode *error_msg = NULL;
    xmlNode *error_info = NULL;
    xmlChar *xmlbuff = NULL;
    char *header = NULL;
    int len;
    bool ret = true;

    /* Generate reply */
    doc = create_rpc (BAD_CAST "rpc-reply", xmlGetProp (rpc, BAD_CAST "message-id"));
    child = xmlNewChild (xmlDocGetRootElement (doc), NULL, BAD_CAST "rpc-error", NULL);
    xmlNewChild (child, NULL, BAD_CAST "error-tag",
                 BAD_CAST rpc_error_tag_to_string (error_parms.tag));
    xmlNewChild (child, NULL, BAD_CAST "error-type",
                 BAD_CAST rpc_error_type_to_string (error_parms.type));
    xmlNewChild (child, NULL, BAD_CAST "error-severity", BAD_CAST "error");

    if (!error_parms.msg || g_strcmp0 (error_parms.msg->str, "") == 0)
    {
        g_string_printf (error_parms.msg, "%s", rpc_error_tag_to_msg (error_parms.tag));
    }
    error_msg = xmlNewNode (child->ns, BAD_CAST "error-message");
    xmlSetProp (error_msg, (const xmlChar *) "xml:lang", (const xmlChar *) DEFAULT_LANG);
    xmlNodeSetContent (error_msg, BAD_CAST error_parms.msg->str);
    xmlAddChild (child, error_msg);

    if (error_parms.info != NULL && g_hash_table_size (error_parms.info) > 0)
    {
        error_info = _create_error_info_xml (error_parms);
        xmlAddChild (child, error_info);
    }

    xmlDocDumpMemoryEnc (doc, &xmlbuff, &len, "UTF-8");
    header = g_strdup_printf ("\n#%d\n", len);

    /* Send reply */
    if (write (session->fd, header, strlen (header)) != strlen (header))
    {
        ERROR ("TX failed: Sending %ld bytes of header\n", strlen (header));
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s", strlen (header), header);
    if (write (session->fd, xmlbuff, len) != len)
    {
        ERROR ("TX failed: Sending %d bytes of hello\n", len);
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%d):\n%.*s", len, len, (char *) xmlbuff);
    if (write (session->fd, NETCONF_BASE_1_1_END, strlen (NETCONF_BASE_1_1_END)) !=
        strlen (NETCONF_BASE_1_1_END))
    {
        ERROR ("TX failed: Sending %ld bytes of trailer\n", strlen (NETCONF_BASE_1_1_END));
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s\n", strlen (NETCONF_BASE_1_1_END), NETCONF_BASE_1_1_END);

  cleanup:
    g_free (header);
    xmlFree (xmlbuff);
    xmlFreeDoc (doc);
    return ret;
}

/**
 * Fully parameterised send_rpc_error. This can be used to send a variety of RPC error types, depending
 * on what is passed in. Parameters session, rpc, err_tag, err_type and error_msg are mandatory, the rest are
 * optional. Valid combinations of optional parameters are:
 *  session error - no optional parameters set, no_info flag false
 *  element error - set bad_elem only, no_info flag false (actually don't care)
 *  attribute error - set bad_elem and bad_attr only, no_info flag false (actually don't care)
 *  no_info error - no optional parameters set, no_info flag true
 */
static bool
send_rpc_error_full (struct netconf_session *session, xmlNode *rpc, NC_ERR_TAG err_tag, NC_ERR_TYPE err_type,
                     gchar *error_msg, char *bad_elem, char *bad_attr, bool no_info)
{
    nc_error_parms error_parms = NC_ERROR_PARMS_INIT;
    bool ret = false;

    error_parms.tag = err_tag;
    error_parms.type = err_type;
    if (!bad_elem && !no_info)
    {
        gchar *sess_id_str = g_strdup_printf ("%u", running_ds_lock.nc_sess.id);
        g_hash_table_insert (error_parms.info, "session-id", sess_id_str);
        /* No need to free, hash table cleanup will do that */
    }
    if (error_msg)
    {
        g_string_printf (error_parms.msg, "%s", error_msg);
        ERROR ("%s\n", error_msg);
    }
    if (bad_elem)
    {
        g_hash_table_insert (error_parms.info, "bad_element", g_strdup (bad_elem));
        /* No need to free, hash table cleanup will do that */
    }
    if (bad_attr)
    {
        g_hash_table_insert (error_parms.info, "bad-attribute", g_strdup (bad_attr));
        /* No need to free, hash table cleanup will do that */
    }
    ret = _send_rpc_error (session, rpc, error_parms);
    _free_error_parms (error_parms);
    return ret;
}

static bool
send_rpc_data (struct netconf_session *session, xmlNode * rpc, GList *xml_list)
{
    xmlDoc *doc;
    xmlNode * data;
    xmlNode *child;
    xmlChar *xmlbuff;
    GList *list;
    char *header = NULL;
    int len;
    bool ret = true;

    /* Generate reply */
    doc = create_rpc ( BAD_CAST "rpc-reply", xmlGetProp (rpc, BAD_CAST "message-id"));
    child = xmlNewChild (xmlDocGetRootElement (doc), NULL, BAD_CAST "data", NULL);
    if (!xml_list)
    {
        xmlAddChildList (child, NULL);
    }
    else
    {
        for (list = g_list_first (xml_list); list; list = g_list_next (list))
        {
            data = list->data;
            xmlAddChildList (child, data);
        }
    }

    xmlDocDumpMemoryEnc (doc, &xmlbuff, &len, "UTF-8");
    header = g_strdup_printf ("\n#%d\n", len);

    /* Send reply */
    if (write (session->fd, header, strlen (header)) != strlen (header))
    {
        ERROR ("TX failed: Sending %ld bytes of header\n", strlen (header));
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s", strlen (header), header);
    if (write (session->fd, xmlbuff, len) != len)
    {
        ERROR ("TX failed: Sending %d bytes of hello\n", len);
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%d):\n%.*s", len, len, (char *) xmlbuff);
    if (write (session->fd, NETCONF_BASE_1_1_END, strlen (NETCONF_BASE_1_1_END)) !=
        strlen (NETCONF_BASE_1_1_END))
    {
        ERROR ("TX failed: Sending %ld bytes of trailer\n", strlen (NETCONF_BASE_1_1_END));
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s\n", strlen (NETCONF_BASE_1_1_END), NETCONF_BASE_1_1_END);

  cleanup:
    g_free (header);
    xmlFree (xmlbuff);
    xmlFreeDoc (doc);
    if (xml_list)
        g_list_free (xml_list);

    return ret;
}

static void
schema_set_model_information (xmlNode * cap)
{
    xmlNode *xml_child;
    sch_loaded_model *loaded;
    GList *list;
    char *capability;
    GList *loaded_models = sch_get_loaded_models (g_schema);

    for (list = g_list_first (loaded_models); list; list = g_list_next (list))
    {
        loaded = list->data;
        if (loaded->organization && loaded->version && loaded->model &&
            strlen (loaded->organization) && strlen (loaded->version) &&
            strlen (loaded->model))
        {
            char *old;
            xml_child = xmlNewChild (cap, NULL, BAD_CAST "capability", NULL);
            capability = g_strdup_printf ("%s?module=%s&amp;revision=%s",
                                          loaded->ns_href, loaded->model, loaded->version);
            if (loaded->features)
            {
                old = capability;
                capability = g_strdup_printf ("%s&amp;features=%s", capability, loaded->features);
                g_free (old);
            }
            if (loaded->deviations)
            {
                old = capability;
                capability = g_strdup_printf ("%s&amp;deviations=%s", capability, loaded->deviations);
                g_free (old);
            }
            xmlNodeSetContent (xml_child, BAD_CAST capability);
            g_free (capability);
        }
    }
}

static bool
validate_hello (char *buffer, int buf_len)
{
    xmlDoc *doc = NULL;
    xmlNode *root;
    xmlNode *node;
    xmlNode *cap_node;
    xmlChar *cap;
    bool found_base11 = false;

    doc = xmlParseMemory (buffer, buf_len);
    if (!doc)
    {
        ERROR ("XML: Invalid hello message\n");
        return false;
    }
    root = xmlDocGetRootElement (doc);
    if (!root || g_strcmp0 ((char *) root->name, "hello") != 0)
    {
        ERROR ("XML: No root HELLO element\n");
        xmlFreeDoc (doc);
        return false;
    }
    node = xmlFirstElementChild (root);
    if (!node || g_strcmp0 ((char *) node->name, "capabilities") != 0)
    {
        ERROR ("XML: No capabilities element in HELLO\n");
        xmlFreeDoc (doc);
        return false;
    }

    /* Check capabilities - we want to see base:1.1 */
    for (cap_node = xmlFirstElementChild (node); cap_node; cap_node = xmlNextElementSibling (cap_node))
    {
        if (g_strcmp0 ((char *) cap_node->name, "capability") == 0)
        {
            cap = xmlNodeGetContent (cap_node);
            if (cap)
            {
                if (g_strcmp0 ((char *) cap, "urn:ietf:params:netconf:base:1.1") == 0)
                {
                    found_base11 = true;
                }
                xmlFree (cap);
                if (found_base11)
                {
                    break;
                }
            }
        }
    }

    if (found_base11)
    {
        VERBOSE ("Received valid hello message\n");
    }
    else
    {
        ERROR ("NETCONF: No compatible base version found\n");
    }
    xmlFreeDoc (doc);

    return found_base11;
}

static bool
handle_hello (struct netconf_session *session)
{
    bool ret = true;
    char buf[HELLO_RX_SIZE];
    char *pt;
    char *buffer = NULL;
    char *endpt = NULL;
    int len;
    int recv_len = HELLO_RX_SIZE - NETCONF_HELLO_END_LEN;
    int total_len = 0;
    int offset = 0;

    /* Allow MSG_PEEK to read sequentially through the buffer */
    setsockopt (session->fd, SOL_SOCKET, SO_PEEK_OFF, &offset, sizeof (offset));

    /* Reserve NETCONF_HELLO_END_LEN bytes at the front of the buffer */
    pt = buf + NETCONF_HELLO_END_LEN;
    memset (buf, ' ', NETCONF_HELLO_END_LEN);
    while (g_main_loop_is_running (g_loop))
    {
        len = recv (session->fd, pt, recv_len, MSG_PEEK);
        if (len > 0)
        {
            char *match = g_strstr_len (buf, len + NETCONF_HELLO_END_LEN, NETCONF_HELLO_END);
            if (match)
            {
                total_len += match - buf;
                break;
            }
            else if (len < recv_len)
            {
                /* Reached the end of the message with no hello end */
                return false;
            }

            if (len == recv_len)
            {
                /* Copy NETCONF_HELLO_END_LEN bytes from the end of the buffer to the front of the
                   receive buffer so that we can guard against the end string being split over two recveives */
                total_len += recv_len;
                if (total_len >= MAX_HELLO_RX_SIZE)
                {
                    return false;
                }
                memcpy (buf, pt + recv_len - NETCONF_HELLO_END_LEN, NETCONF_HELLO_END_LEN);
            }
        }
        else
        {
            return false;
        }
    }

    buffer = g_malloc0 (total_len);
    if (!buffer)
    {
        return false;
    }

    len = recv (session->fd, buffer, total_len, 0);
    if (len <= 0)
    {
        g_free (buffer);
        return false;
    }

    VERBOSE ("RX(%d):\n%.*s", len, (int) len, buffer);

    /* Find trailer */
    endpt = g_strstr_len (buffer, len, NETCONF_BASE_1_0_END);
    if (!endpt)
    {
        ERROR ("XML: Invalid hello message (no 1.0 trailer)\n");
        g_free (buffer);
        return false;
    }

    /* Validate hello */
    if (!validate_hello (buffer, (endpt - buffer)))
    {
        ret = false;
    }

    g_free (buffer);
    return ret;
}

static bool
send_hello (struct netconf_session *session)
{
    bool ret = true;
    xmlDoc *doc = NULL;
    xmlNode *root, *node, *child;
    xmlChar *hello_resp = NULL;
    char session_id_str[32];
    int hello_resp_len = 0;

    doc = create_rpc (BAD_CAST "hello", NULL);
    root = xmlDocGetRootElement (doc);
    node = xmlNewChild (root, NULL, BAD_CAST "capabilities", NULL);
    child = xmlNewChild (node, NULL, BAD_CAST "capability", NULL);
    xmlNodeSetContent (child, BAD_CAST "urn:ietf:params:netconf:base:1.1");
    child = xmlNewChild (node, NULL, BAD_CAST "capability", NULL);
    xmlNodeSetContent (child, BAD_CAST "urn:ietf:params:netconf:capability:xpath:1.0");
    child = xmlNewChild (node, NULL, BAD_CAST "capability", NULL);
    xmlNodeSetContent (child,
                       BAD_CAST "urn:ietf:params:netconf:capability:writable-running:1.0");
    child = xmlNewChild (node, NULL, BAD_CAST "capability", NULL);
    xmlNodeSetContent (child,
                       BAD_CAST "urn:ietf:params:netconf:capability:with-defaults:1.0?basic-mode=explicit&amp;also-supported=report-all,trim");
    /* Find all models in the entire tree */
    schema_set_model_information (node);
    snprintf (session_id_str, sizeof (session_id_str), "%u", session->id);
    node = xmlNewChild (root, NULL, BAD_CAST "session-id", NULL);
    xmlNodeSetContent (node, BAD_CAST session_id_str);
    xmlDocDumpMemoryEnc (doc, &hello_resp, &hello_resp_len, "UTF-8");
    xmlFreeDoc (doc);

    /* Send reply */
    if (write (session->fd, hello_resp, hello_resp_len) != hello_resp_len)
    {
        ERROR ("TX failed: Sending %d bytes of hello\n", hello_resp_len);
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%d):\n%.*s", hello_resp_len, hello_resp_len, (char *) hello_resp);
    if (write (session->fd, NETCONF_BASE_1_0_END, strlen (NETCONF_BASE_1_0_END)) !=
        strlen (NETCONF_BASE_1_0_END))
    {
        ERROR ("TX failed: Sending %ld bytes of hello trailer\n",
               strlen (NETCONF_BASE_1_0_END));
        ret = false;
        goto cleanup;
    }
    VERBOSE ("TX(%ld):\n%s\n", strlen (NETCONF_BASE_1_0_END), NETCONF_BASE_1_0_END);

  cleanup:
    xmlFree (hello_resp);
    return ret;
}

static GNode *
get_full_tree ()
{
    GNode *tree = APTERYX_NODE (NULL, g_strdup_printf ("/"));
    GList *children, *iter;

    /* Search root and then get tree for each root entry */
    children = apteryx_search ("/");
    for (iter = children; iter; iter = g_list_next (iter))
    {
        const char *path = (const char *) iter->data;
        GNode *subtree = apteryx_get_tree (path);
        if (subtree)
        {
            g_free (subtree->data);
            subtree->data = g_strdup (path + 1);
            g_node_append (tree, subtree);
        }
    }
    g_list_free_full (children, free);
    return tree;
}

static GNode*
get_response_node (GNode *tree, int rdepth)
{
    GNode *rnode = tree;

    while (--rdepth && rnode)
        rnode = rnode->children;

    return rnode;
}

static void
get_query_to_xml (struct netconf_session *session, GNode *query, sch_node *rschema, GNode *rnode,
                  int rdepth, GNode *qnode, int schflags, GList **xml_list)
{
    GNode *tree;
    xmlNode *xml = NULL;

    /* Query database */
    DEBUG ("NETCONF: GET %s\n", query ? APTERYX_NAME (query) : "/");
    if (netconf_logging_test_flag (LOG_GET | LOG_GET_CONFIG))
        NOTICE ("%s: user:%s session-id:%d path:%s\n",
                (schflags & SCH_F_CONFIG) ? "GET-CONFIG" : "GET", session->username, session->id,
                query ? APTERYX_NAME (query) : "/");

    tree = query ? apteryx_query (query) : get_full_tree ();
    if (rschema && (schflags & SCH_F_ADD_DEFAULTS))
    {
        if (tree)
        {
            rnode = get_response_node (tree, rdepth);
            sch_traverse_tree (g_schema, rschema, rnode, schflags);
        }
        else if (!tree)
        {
            /* Nothing in the database, but we may have defaults! */
            tree = query;
            query = NULL;
            sch_traverse_tree (g_schema, rschema, qnode, schflags);
        }
    }

    if (tree && (schflags & SCH_F_TRIM_DEFAULTS))
    {
        /* Get rid of any unwanted nodes */
        GNode *rnode = get_response_node (tree, rdepth);
        sch_traverse_tree (g_schema, rschema, rnode, schflags);
     }
    apteryx_free_tree (query);

    /* Convert result to XML */
    xml = tree ? sch_gnode_to_xml (g_schema, NULL, tree, schflags) : NULL;
    apteryx_free_tree (tree);
    *xml_list = g_list_append (*xml_list, xml);
}

static void
get_query_schema (struct netconf_session *session, GNode *query, sch_node *qschema,
                  int schflags, bool is_filter, GList **xml_list)
{
    GNode *rnode = NULL;
    sch_node *rschema = NULL;
    GNode *qnode = NULL;
    int qdepth = 0;
    int rdepth;
    int diff;

    /* Get the depth of the response which is the depth of the query
        OR the up until the first path wildcard */
    qdepth = g_node_max_height (query);
    rdepth = 1;
    rnode = query;
    while (rnode &&
            g_node_n_children (rnode) == 1 &&
            g_strcmp0 (APTERYX_NAME (g_node_first_child (rnode)), "*") != 0)
    {
        rnode = g_node_first_child (rnode);
        rdepth++;
    }

    qnode = rnode;
    while (qnode->children)
        qnode = qnode->children;

    if (qdepth && qnode && !g_node_first_child (qnode) &&
            g_strcmp0 (APTERYX_NAME (qnode), "*") == 0)
        qdepth--;

    rschema = qschema;
    diff = qdepth - rdepth;
    while (diff--)
        rschema = sch_node_parent (rschema);

    if (sch_node_parent (rschema) && sch_is_list (sch_node_parent (rschema)))
    {
        /* We need to present the list rather than the key */
        rschema = sch_node_parent (rschema);
        rdepth--;
    }

    /* Without a query we may need to add a wildcard to get everything from here down */
    if (is_filter && qdepth == g_node_max_height (query) && !(schflags & SCH_F_DEPTH_ONE))
    {
        if (qschema && sch_node_child_first (qschema) && !(schflags & SCH_F_STRIP_DATA))
        {
            /* Get everything from here down if we do not already have a star */
            if (!g_node_first_child (qnode) && g_strcmp0 (APTERYX_NAME (qnode), "*") != 0)
            {
                APTERYX_NODE (qnode, g_strdup ("*"));
                DEBUG ("%*s%s\n", qdepth * 2, " ", "*");
            }
        }
    }

    get_query_to_xml (session, query, rschema, rnode, rdepth, qnode, schflags, xml_list);
}

static int
get_process_action (struct netconf_session *session, xmlNode *rpc, xmlNode *node,
                    int schflags, GList **xml_list, bool *ret)
{
    char *attr;
    xmlNode *tnode;
    GNode *query = NULL;
    gchar **split;
    sch_xml_to_gnode_parms parms;
    sch_node *qschema = NULL;
    bool is_filter = false;
    int i;
    int count;

    /* Check the requested datastore */
    if (g_strcmp0 ((char *) node->name, "source") == 0)
    {
        if (!xmlFirstElementChild (node) ||
            g_strcmp0 ((char *) xmlFirstElementChild (node)->name, "running") != 0)
        {
            gchar *error_msg = g_strdup_printf ("Datastore \"%s\" not supported",
                                                (char *) xmlFirstElementChild (node)->name);
            VERBOSE ("%s\n", error_msg);
            *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_PROTOCOL,
                                        error_msg, NULL, NULL, true);
            g_free (error_msg);
            return -1;
        }
    }
    /* Parse any filters */
    else if (g_strcmp0 ((char *) node->name, "filter") == 0)
    {
        attr = (char *) xmlGetProp (node, BAD_CAST "type");

        /* Default type is "subtree" */
        if (attr == NULL)
        {
            attr = g_strdup ("subtree");    /* for the later free */
        }
        if (g_strcmp0 (attr, "xpath") == 0)
        {
            free (attr);
            attr = (char *) xmlGetProp (node, BAD_CAST "select");
            if (!attr)
            {
                *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_MISSING_ATTR, NC_ERR_TYPE_PROTOCOL,
                                            "XPATH filter missing select attribute", "xpath", "select", false);
                VERBOSE ("XPATH filter missing select attribute");
                return -1;
            }
            VERBOSE ("FILTER: XPATH: %s\n", attr);
            is_filter = true;
            split = g_strsplit (attr, "|", -1);
            count = g_strv_length (split);
            for (i = 0; i < count; i++)
            {
                char *path = g_strstrip (split[i]);
                qschema = NULL;
                schflags |= SCH_F_XPATH;
                query = sch_path_to_gnode (g_schema, NULL, path, schflags, &qschema);
                if (!query)
                {
                    VERBOSE ("XPATH: malformed filter\n");
                    *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_MALFORMED_MSG, NC_ERR_TYPE_RPC,
                                                "XPATH: malformed filter", NULL, NULL, true);
                    free (attr);
                    g_strfreev(split);
                    return -1;
                }

                if (qschema)
                {
                    if (sch_is_leaf (qschema) && !sch_is_readable (qschema))
                    {
                        gchar *error_msg = g_strdup_printf ("NETCONF: Path \"%s\" not readable", attr);
                        VERBOSE ("%s\n", error_msg);
                        *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_APP,
                                                    error_msg, NULL, NULL, true);
                        g_free (error_msg);
                        free (attr);
                        g_strfreev(split);
                        return -1;
                    }
                    get_query_schema (session, query, qschema, schflags, is_filter, xml_list);
                }
            }
            g_strfreev(split);
        }
        else if (g_strcmp0 (attr, "subtree") == 0)
        {
            if (!xmlFirstElementChild (node))
            {
                VERBOSE ("SUBTREE: empty query\n");
                free (attr);
                *xml_list = g_list_append (*xml_list, NULL);
                return 0;
            }

            for (tnode = xmlFirstElementChild (node); tnode; tnode = xmlNextElementSibling (tnode))
            {
                qschema = NULL;
                parms =
                    sch_xml_to_gnode (g_schema, NULL, tnode,
                                        schflags | SCH_F_STRIP_DATA | SCH_F_STRIP_KEY, "none",
                                        false, &qschema);
                query = sch_parm_tree (parms);
                sch_parm_free (parms);
                if (!query)
                {
                    VERBOSE ("SUBTREE: malformed query\n");
                    *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_MALFORMED_MSG, NC_ERR_TYPE_RPC,
                                                "SUBTREE: malformed query", NULL, NULL, true);
                    free (attr);
                    return -1;
                }

                if (qschema)
                {
                    if (sch_is_leaf (qschema) && !sch_is_readable (qschema))
                    {
                        gchar *error_msg = g_strdup_printf ("NETCONF: Path \"%s\" not readable", attr);
                        VERBOSE ("%s\n", error_msg);
                        *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_APP,
                                                    error_msg, NULL, NULL, true);
                        g_free (error_msg);
                        return -1;
                    }
                    get_query_schema (session, query, qschema, schflags, is_filter, xml_list);
                }
            }
        }
        else
        {
            gchar *error_msg = g_strdup_printf ("FILTER: unsupported/missing type (%s)", attr);
            VERBOSE ("%s\n", error_msg);
            *ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_APP,
                                        error_msg, NULL, NULL, true);
            g_free (error_msg);
            free (attr);
            return -1;
        }
        free (attr);
    }

    return 0;
}

static bool
handle_get (struct netconf_session *session, xmlNode * rpc, gboolean config_only)
{
    xmlNode *action = xmlFirstElementChild (rpc);
    xmlNode *node;
    GList *xml_list = NULL;
    GList *list;
    int schflags = 0;
    bool ret = false;

    if (apteryx_netconf_verbose)
        schflags |= SCH_F_DEBUG;

    if (config_only)
    {
        schflags |= SCH_F_CONFIG;
    }

    /* Validate lock if configured on the running datastore */
    if (running_ds_lock.locked == TRUE && (session->id != running_ds_lock.nc_sess.id))
    {
        /* A lock is already held by another NETCONF session, return lock-denied */
        VERBOSE ("Lock failed, lock is already held\n");
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_IN_USE, NC_ERR_TYPE_APP,
                                   "Lock is already held", NULL, NULL, false);
        return ret;
    }

    /* Parse options - first look for with-defaults option as this changes the way query lookup works */
    for (node = xmlFirstElementChild (action); node; node = xmlNextElementSibling (node))
    {
        if (g_strcmp0 ((char *) node->name, "with-defaults") == 0)
        {
            char *defaults_type = (char *) xmlNodeGetContent (node);
            if (g_strcmp0 (defaults_type, "report-all") == 0)
            {
                schflags |= SCH_F_ADD_DEFAULTS;
            }
            else if (g_strcmp0 (defaults_type, "trim") == 0)
            {
                schflags |= SCH_F_TRIM_DEFAULTS;
            }
            else if (g_strcmp0 (defaults_type, "explicit") != 0)
            {
                gchar *error_msg = g_strdup_printf ("WITH-DEFAULTS: No support for with-defaults query type \"%s\"",
                                                    defaults_type);
                ERROR ("%s\n", error_msg);
                ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_PROTOCOL,
                                           error_msg, NULL, NULL, true);
                g_free (error_msg);
                free (defaults_type);
                return ret;
            }
            free (defaults_type);
            break;
        }
    }

    /* Parse the remaining options */
    for (node = xmlFirstElementChild (action); node; node = xmlNextElementSibling (node))
    {
        if (g_strcmp0 ((char *) node->name, "with-defaults") == 0)
            continue;

        if (get_process_action (session, rpc, node, schflags, &xml_list, &ret) < 0)
        {
            /* Cleanup any requests added to the xml_list before hitting an error */
            for (list = g_list_first (xml_list); list; list = g_list_next (list))
            {
                xmlFree (list->data);
            }
            g_list_free (xml_list);

            return ret;
        }
    }

    /* Catch for get without filter */
    if (!xml_list)
        get_query_to_xml (session, NULL, NULL, NULL, 0, NULL, schflags, &xml_list);

    /* Send response */
    send_rpc_data (session, rpc, xml_list);

    return true;
}

static xmlNode *
xmlFindNodeByName (xmlNode * root, const xmlChar * name)
{
    xmlNode *child;

    for (child = xmlFirstElementChild (root); child; child = xmlNextElementSibling (child))
    {
        if (!xmlStrcmp (child->name, name))
        {
            return child;
        }
    }
    return NULL;
}

/**
 * Check for existence of data at a particular xpath or below. This is
 * required for NC_OP_CREATE and NC_OP_DELETE. Fill in the error_tag if we don't
 * get expected result, otherwise leave it alone (so we can accumulate errors).
 */
static void
_check_exist (const char *check_xpath, NC_ERR_TAG *err_tag, bool expected)
{
    GNode *check_result;

    check_result = apteryx_get_tree (check_xpath);
    if (check_result && !expected)
    {
        *err_tag = NC_ERR_TAG_DATA_EXISTS;
    }
    else if (!check_result && expected)
    {
        *err_tag = NC_ERR_TAG_DATA_MISSING;
    }
    apteryx_free_tree (check_result);
}

static bool
handle_edit (struct netconf_session *session, xmlNode * rpc)
{
    xmlNode *action = xmlFirstElementChild (rpc);
    xmlNode *node;
    GNode *tree = NULL;
    sch_xml_to_gnode_parms parms;
    sch_node *qschema = NULL;
    int schflags = 0;
    GList *iter;
    bool ret = false;

    if (apteryx_netconf_verbose)
        schflags |= SCH_F_DEBUG;

    /* Check the target */
    node = xmlFindNodeByName (action, BAD_CAST "target");
    if (!node || !xmlFirstElementChild (node) ||
        xmlStrcmp (xmlFirstElementChild (node)->name, BAD_CAST "running"))
    {
        gchar *error_msg = g_strdup_printf ("Datastore \"%s\" not supported",
                                            (char *) xmlFirstElementChild (node)->name);
        VERBOSE ("%s\n", error_msg);
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_PROTOCOL,
                                   error_msg, NULL, NULL, true);
        g_free (error_msg);
        return ret;
    }

    //TODO Check default-operation
    //TODO Check test-option
    //TODO Check error-option
    //
    /* Validate lock if configured on the running datastore */
    if (running_ds_lock.locked == TRUE && (session->id != running_ds_lock.nc_sess.id))
    {
        /* A lock is already held by another NETCONF session, return in-use */
        VERBOSE ("Lock failed, lock is already held\n");
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_IN_USE, NC_ERR_TYPE_APP,
                                   "Lock is already held", NULL, NULL, false);
        return ret;
    }

    /* Find the config */
    node = xmlFindNodeByName (action, BAD_CAST "config");
    if (!node)
    {
        VERBOSE ("Missing \"config\" element\n");
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_MISSING_ELEM, NC_ERR_TYPE_PROTOCOL,
                                   "Missing config element", "config", NULL, false);
        return ret;
    }

    /* Convert to gnode */
    parms =
        sch_xml_to_gnode (g_schema, NULL, xmlFirstElementChild (node), schflags, "merge",
                          true, &qschema);
    tree = sch_parm_tree (parms);
    nc_error_parms error_parms = sch_parm_error (parms);

    if (error_parms.tag != 0)
    {
        VERBOSE ("error parsing XML\n");
        ret = _send_rpc_error (session, rpc, error_parms);
        sch_parm_free (parms);
        apteryx_free_tree (tree);
        return ret;
    }

    /* Check delete and create paths */
    NC_ERR_TAG err_tag = NC_ERR_TAG_UNKNOWN;
    for (iter = sch_parm_deletes (parms); iter; iter = g_list_next (iter))
    {
        _check_exist ((char *) iter->data, &err_tag, true);
    }
    for (iter = sch_parm_creates (parms); iter; iter = g_list_next (iter))
    {
        _check_exist ((char *) iter->data, &err_tag, false);
    }
    if (err_tag != NC_ERR_TAG_UNKNOWN)
    {
        VERBOSE ("error in delete or create paths\n");
        ret = send_rpc_error_full (session, rpc, err_tag, NC_ERR_TYPE_APP, NULL, NULL, NULL, true);
        sch_parm_free (parms);
        apteryx_free_tree (tree);
        return ret;
    }

    /* Delete delete, remove and replace paths */
    for (iter = sch_parm_deletes (parms); iter; iter = g_list_next (iter))
    {
        apteryx_prune (iter->data);
    }
    for (iter = sch_parm_removes (parms); iter; iter = g_list_next (iter))
    {
        apteryx_prune (iter->data);
    }
    for (iter = sch_parm_replaces (parms); iter; iter = g_list_next (iter))
    {
        apteryx_prune (iter->data);
    }
    sch_parm_free (parms);

    //TODO - permissions
    //TODO - patterns

    /* Edit database */
    DEBUG ("NETCONF: SET %s\n", tree ? APTERYX_NAME (tree) : "NULL");
    if (tree && !apteryx_set_tree (tree))
    {
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_FAILED, NC_ERR_TYPE_APP, NULL, NULL, NULL, true);
        apteryx_free_tree (tree);
        return ret;
    }
    if (netconf_logging_test_flag (LOG_EDIT_CONFIG))
        NOTICE ("EDIT-CONFIG: user:%s session-id:%d path:%s\n",
                session->username, session->id, tree ? APTERYX_NAME (tree) : "/");

    apteryx_free_tree (tree);

    /* Success */
    return send_rpc_ok (session, rpc, false);
}

static void
set_lock (struct netconf_session *session)
{
    running_ds_lock.locked = TRUE;
    running_ds_lock.nc_sess.id = session->id;
    running_ds_lock.nc_sess.fd = session->fd;
}

static bool
handle_lock (struct netconf_session *session, xmlNode * rpc)
{
    xmlNode *action = xmlFirstElementChild (rpc);
    xmlNode *node;
    bool ret = true;

    /* Check the target */
    node = xmlFindNodeByName (action, BAD_CAST "target");
    if (!node || !xmlFirstElementChild (node) ||
        xmlStrcmp (xmlFirstElementChild (node)->name, BAD_CAST "running"))
    {
        gchar *error_msg = g_strdup_printf ("Datastore \"%s\" not supported",
                                            (char *) xmlFirstElementChild (node)->name);
        VERBOSE ("%s\n", error_msg);
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_PROTOCOL,
                                   error_msg, NULL, NULL, true);
        g_free (error_msg);
        return ret;
    }

    /* Attempt to acquire lock */
    if (running_ds_lock.locked == FALSE)
    {
        /* Acquire lock on the running datastore */
        set_lock (session);
    }
    else
    {
        /* Return lock-denied */
        gchar *error_msg = g_strdup_printf ("Lock is already held by session id %d",
                                            running_ds_lock.nc_sess.id);
        VERBOSE ("%s\n", error_msg);
        ret =  send_rpc_error_full (session, rpc, NC_ERR_TAG_LOCK_DENIED, NC_ERR_TYPE_PROTOCOL,
                                    error_msg, NULL, NULL, false);
        g_free (error_msg);
        return ret;
    }
    if (netconf_logging_test_flag (LOG_LOCK))
        NOTICE ("LOCK: user:%s session-id:%d\n", session->username, session->id);

    /* Success */
    return send_rpc_ok (session, rpc, false);
}

static void
reset_lock (void)
{
    running_ds_lock.locked = FALSE;
    running_ds_lock.nc_sess.id = 0;
    running_ds_lock.nc_sess.fd = -1;
}

static bool
handle_unlock (struct netconf_session *session, xmlNode * rpc)
{
    xmlNode *action = xmlFirstElementChild (rpc);
    xmlNode *node;
    bool ret = false;

    /* Check the target */
    node = xmlFindNodeByName (action, BAD_CAST "target");
    if (!node || !xmlFirstElementChild (node) ||
        xmlStrcmp (xmlFirstElementChild (node)->name, BAD_CAST "running"))
    {
        gchar *error_msg = g_strdup_printf ("Datastore \"%s\" not supported",
                                            (char *) xmlFirstElementChild (node)->name);
        VERBOSE ("%s\n", error_msg);
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_PROTOCOL,
                                   error_msg, NULL, NULL, false);
        g_free (error_msg);
        return ret;
    }

    /* Check unlock operation validity */
    if (!running_ds_lock.locked)
    {
        gchar *error_msg = g_strdup_printf ("Unlock failed, no lock configured on the \"%s\" datastore",
                                            (char *) xmlFirstElementChild (node)->name);
        VERBOSE ("%s\n", error_msg);
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_FAILED, NC_ERR_TYPE_PROTOCOL,
                                   error_msg, NULL, NULL, true);
        g_free (error_msg);
        return ret;
    }
    else if ((running_ds_lock.locked == TRUE) && (session->id != running_ds_lock.nc_sess.id))
    {
        /* Lock held by another session */
        gchar *error_msg = g_strdup_printf ("Unlock failed, session %u does not own the lock", session->id);
        VERBOSE ("%s\n", error_msg);
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_LOCK_DENIED, NC_ERR_TYPE_PROTOCOL,
                                   error_msg, NULL, NULL, false);
        g_free (error_msg);
        return ret;
    }

    /* Unlock running datastore */
    reset_lock ();

    if (netconf_logging_test_flag (LOG_UNLOCK))
        NOTICE ("UNLOCK: user:%s session-id:%d\n", session->username, session->id);

    /* Success */
    return send_rpc_ok (session, rpc, false);
}

static bool
handle_kill_session (struct netconf_session *session, xmlNode * rpc)
{
    xmlNode *action = xmlFirstElementChild (rpc);
    xmlNode *node;
    uint32_t kill_session_id = 0;
    struct netconf_session *kill_session = NULL;
    xmlChar* content = NULL;
    bool ret = false;

    /* Validate request */
    node = xmlFindNodeByName (action, BAD_CAST "session-id");
    if (!node)
    {
        VERBOSE ("Missing \"session-id\" element");
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_MISSING_ELEM, NC_ERR_TYPE_PROTOCOL,
                                   "Missing \"session-id\" element", "session-id", NULL, false);
        return ret;
    }

    /* Return an "invalid-error" if the request is made by the current session */
    content = xmlNodeGetContent (node);
    sscanf ((char *) content, "%u", &kill_session_id);
    xmlFree (content);

    if (kill_session_id == 0)
    {
        VERBOSE ("Invalid session ID");
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_INVALID_VAL, NC_ERR_TYPE_PROTOCOL,
                                   "Invalid session ID - 0", NULL, NULL, true);
        return ret;
    }
    else if (session->id == kill_session_id)
    {
        VERBOSE ("Attempt to kill own session is forbidden");
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_INVALID_VAL, NC_ERR_TYPE_PROTOCOL,
                                   "Attempt to kill own session is forbidden", NULL, NULL, true);
        return ret;
    }

    kill_session = find_netconf_session_by_id (kill_session_id);

    if (!kill_session)
    {
        gchar *error_msg = g_strdup_printf ("Session ID - %u not found!", kill_session_id);
        VERBOSE ("%s\n", error_msg);
        ret = send_rpc_error_full (session, rpc, NC_ERR_TAG_INVALID_VAL, NC_ERR_TYPE_PROTOCOL,
                                   error_msg, NULL, NULL, true);
        g_free (error_msg);
        return ret;
    }

    /* Shutdown session fd */
    VERBOSE ("NETCONF: session killed\n");
    if (netconf_logging_test_flag (LOG_KILL_SESSION))
        NOTICE ("KILL-SESSION: user:%s session-id:%d killed session user:%s: session-id:%d\n",
                session->username, session->id, kill_session->username, kill_session->id);

    shutdown (kill_session->fd, SHUT_RDWR);

    /**
     * NOTE: Allow the g_main_loop to handle the actual cleanup of the (broken) killed session
     **/

    /* Success */
    return send_rpc_ok (session, rpc, false);
}

/**
 * Add session data for this session based on the PID of the remote socat process.
 */
static void
add_session_data (struct netconf_session *session, uint32_t pid)
{
    gchar *fname;
    gchar *contents;
    gchar *one_env;
    gsize length;
    gsize length_left;
    gsize env_len;
    gchar **env_split;
    GDateTime *now = NULL;

    /* Get initial environment of remote process. */
    fname = g_strdup_printf ("/proc/%d/environ", pid);
    if (!g_file_get_contents (fname, &contents, &length, NULL))
    {
        g_free (fname);
        return;
    }
    g_free (fname);

    /* Read each null-terminated string in contents */
    one_env = contents;
    length_left = length;
    while (length_left > 0 && one_env[0] != '\0')
    {
        if (g_str_has_prefix (one_env, "SSH_CLIENT"))
        {
            env_split = g_strsplit_set (one_env, "= ", 4);
            if (env_split[0] == NULL || env_split[1] == NULL || env_split[2] == NULL ||
                env_split[3] == NULL || env_split[4] != NULL)
            {
                g_strfreev (env_split);
                goto cleanup;
            }
            session->rem_addr = g_strdup (env_split[1]);
            session->rem_port = g_strdup (env_split[2]);
            g_strfreev (env_split);
            break;
        }
        env_len = strlen (one_env);
        length_left -= env_len + 1;
        one_env += env_len + 1;
    }

    if (session->rem_addr)
    {
        /* Get local time */
        now = g_date_time_new_now_utc ();
        session->login_time = g_date_time_format (now, "%Y-%m-%dT%H:%M:%SZ%:z");
        g_date_time_unref (now);
    }

cleanup:
    g_free (contents);
}

/**
 * Refresh function for /netconf-state/sessions/session/<*>
 */
static uint64_t
_netconf_sessions_refresh (const char *path)
{
    GNode *root;
    GNode *sess;
    gboolean done_one = false;
    gchar *sess_id;
    struct netconf_session *nc_session;
    gboolean has_lock;
    gchar *lock_str;

    root = APTERYX_NODE (NULL, g_strdup (NETCONF_STATE_SESSIONS_PATH));
    g_mutex_lock (&session_lock);
    for (GList *iter = open_sessions_list; iter; iter = g_list_next (iter))
    {
        nc_session = iter->data;
        if (!nc_session)
        {
            continue;
        }

        /* Get lock value for session */
        has_lock = running_ds_lock.locked && nc_session->id == running_ds_lock.nc_sess.id;
        lock_str = has_lock ? "R" : "-";

        /* Create Apteryx sub-tree */
        sess_id = g_strdup_printf ("%d", nc_session->id);
        sess = APTERYX_NODE (root, g_strdup (sess_id));
        APTERYX_LEAF (sess, g_strdup ("session-id"), g_strdup (sess_id));
        APTERYX_LEAF (sess, g_strdup ("transport"), g_strdup ("netconf-ssh"));
        APTERYX_LEAF (sess, g_strdup ("username"), g_strdup (nc_session->username));
        APTERYX_LEAF (sess, g_strdup ("login-time"), g_strdup (nc_session->login_time));
        APTERYX_LEAF (sess, g_strdup ("source-host"), g_strdup (nc_session->rem_addr));
        APTERYX_LEAF (sess, g_strdup ("source-port"), g_strdup (nc_session->rem_port));
        APTERYX_LEAF (sess, g_strdup ("lock"), g_strdup (lock_str));
        APTERYX_LEAF (sess, g_strdup ("status"), g_strdup ("active"));
        g_free (sess_id);
        done_one = true;
    }
    g_mutex_unlock (&session_lock);
    apteryx_prune (NETCONF_STATE_SESSIONS_PATH);
    if (done_one)
    {
        apteryx_set_tree (root);
    }
    apteryx_free_tree (root);
    return 1000 * 1000;
}

static bool
_netconf_clear_session (const char *path, const char *value)
{
    uint32_t id;
    struct netconf_session *clear_session;
    gchar **path_split;

    if (g_strcmp0 (value, "inactive") == 0)
    {
        path_split = g_strsplit (path, "/", 5);
        if (path_split[4] != NULL)
        {
            id = (uint32_t) g_ascii_strtoull (path_split[4], NULL, 10);
            clear_session = find_netconf_session_by_id (id);
            if (clear_session == NULL)
            {
                apteryx_set (path, "unknown");
            }
            else
            {
                shutdown (clear_session->fd, SHUT_RDWR);
            }
        }
        g_strfreev (path_split);
    }
    return true;
}

static bool
_netconf_max_sessions (const char *path, const char *value)
{
    uint32_t max_sessions;

    if (!value || strlen (value) == 0)
    {
        max_sessions = NETCONF_MAX_SESSIONS_DEF;
    }
    else
    {
        max_sessions = g_ascii_strtoull (value, NULL, 10);
        if (max_sessions < NETCONF_MAX_SESSIONS_MIN)
        {
            max_sessions = NETCONF_MAX_SESSIONS_MIN;
        }
        else if (max_sessions > NETCONF_MAX_SESSIONS_MAX)
        {
            max_sessions = NETCONF_MAX_SESSIONS_MAX;
        }
    }
    if (netconf_max_sessions != max_sessions)
    {
        netconf_max_sessions = max_sessions;
        apteryx_set_int (NETCONF_STATE, "max-sessions", netconf_max_sessions);
    }
    return true;
}

static struct netconf_session *
create_session (int fd)
{
    struct netconf_session *session = g_malloc0 (sizeof (struct netconf_session));
    session->fd = fd;
    session->running = g_main_loop_is_running (g_loop);

    g_mutex_lock (&session_lock);
    session->id = netconf_session_id++;

    /* If the counter rounds, then the value 0 is not allowed */
    if (!session->id)
    {
        session->id = netconf_session_id++;
    }

    /* Append to open sessions list */
    open_sessions_list = g_list_append (open_sessions_list, session);
    netconf_num_sessions++;
    g_mutex_unlock (&session_lock);

    return session;
}

static void
destroy_session (struct netconf_session *session)
{
    if (session->fd >= 0)
    {
        close (session->fd);
        session->fd = -1;
    }

    if (session->id == running_ds_lock.nc_sess.id)
    {
        reset_lock ();
    }

    remove_netconf_session (session);

    g_free (session->username);
    g_free (session->rem_addr);
    g_free (session->rem_port);
    g_free (session->login_time);

    g_free (session);
}

/* \n#<chunk-size>\n with max chunk-size = 4294967295 */
#define MAX_CHUNK_HEADER_SIZE 13

static int
read_chunk_size (struct netconf_session *session)
{
    char chunk_header[MAX_CHUNK_HEADER_SIZE + 1];
    int chunk_len = 0;
    char *pt = chunk_header;
    int len = 0;

    /* Read chunk-size (\n#<chunk-size>\n */
    while ((session->running = g_main_loop_is_running (g_loop)))
    {
        if (len > MAX_CHUNK_HEADER_SIZE || recv (session->fd, pt, 1, 0) != 1)
        {
            ERROR ("RX Failed to read chunk header byte\n");
            break;
        }
        pt[1] = '\0';
        if (len >= 3 && chunk_header[0] == '\n' && chunk_header[1] == '#' &&
            chunk_header[len] == '\n')
        {
            if (g_strcmp0 (chunk_header, "\n##\n") == 0)
                break;
            if (sscanf (chunk_header, "\n#%d", &chunk_len) == 1)
            {
                VERBOSE ("RX(%ld): %.*s\n", (pt - chunk_header), (int) (pt - chunk_header),
                         chunk_header);
                break;
            }
        }
        len++;
        pt++;
    }
    return chunk_len;
}

static char *
receive_message (struct netconf_session *session, int *rlen)
{
    char *message = NULL;
    int len = 0;

    /* Read chunks until we get the end of message marker */
    while ((session->running = g_main_loop_is_running (g_loop)))
    {
        int chunk_len;

        /* Get chunk length */
        chunk_len = read_chunk_size (session);
        if (!session->running)
        {
            g_free (message);
            message = NULL;
            len = 0;
            break;
        }

        if (!chunk_len)
        {
            /* End of message */
            break;
        }

        /* Read chunk */
        if (!message)
            message = g_malloc (chunk_len);
        else
            message = g_realloc (message, len + chunk_len);
        if (recv (session->fd, message + len, chunk_len, 0) != chunk_len)
        {
            ERROR ("RX Failed to read %d bytes of chunk\n", chunk_len);
            g_free (message);
            message = NULL;
            len = 0;
            break;
        }
        VERBOSE ("RX(%d):\n%.*s\n", chunk_len, chunk_len, message + len);
        len += chunk_len;
    }

    *rlen = len;
    return message;
}

void *
netconf_handle_session (int fd)
{
    struct netconf_session *session = create_session (fd);
    struct ucred ucred;
    socklen_t len = sizeof (struct ucred);

    if (!session->running || netconf_num_sessions > netconf_max_sessions)
    {
        destroy_session (session);
        return NULL;
    }

    /* Get user information from the calling process */
    if (getsockopt (fd, SOL_SOCKET, SO_PEERCRED, &ucred, &len) >= 0)
    {
        struct passwd *pw = getpwuid(ucred.uid);
        if (pw)
        {
            session->username = g_strdup(pw->pw_name);
        }
        add_session_data (session, ucred.pid);
    }

    /* Send our hello - RFC 6241 section 8.1 last paragraph */
    session->running = g_main_loop_is_running (g_loop);
    if (!session->running || !send_hello (session))
    {
        destroy_session (session);
        return NULL;
    }

    /* Process hello's first */
    session->running = g_main_loop_is_running (g_loop);
    if (!session->running || !handle_hello (session))
    {
        destroy_session (session);
        return NULL;
    }

    /* Process chunked RPC's */
    while ((session->running = g_main_loop_is_running (g_loop)))
    {
        xmlDoc *doc = NULL;
        xmlNode *rpc, *child;
        char *message;
        int len;

        /* Receive message */
        message = receive_message (session, &len);
        if (!session->running || !message)
        {
            break;
        }

        /* Parse RPC */
        doc = xmlParseMemory (message, len);
        if (!doc)
        {
            ERROR ("XML: Invalid Netconf message\n");
            g_free (message);
            break;
        }
        rpc = xmlDocGetRootElement (doc);
        if (!rpc || g_strcmp0 ((char *) rpc->name, "rpc") != 0)
        {
            ERROR ("XML: No root RPC element\n");
            xmlFreeDoc (doc);
            g_free (message);
            break;
        }

        /* Process RPC */
        child = xmlFirstElementChild (rpc);
        if (!child)
        {
            ERROR ("XML: No RPC child element\n");
            xmlFreeDoc (doc);
            g_free (message);
            break;
        }

        /* Check whether the <rpc> element has the mandatory attribute - "message-id "*/
        if (!xmlHasProp (rpc, BAD_CAST "message-id"))
        {
            send_rpc_error_full (session, rpc, NC_ERR_TAG_MISSING_ATTR, NC_ERR_TYPE_PROTOCOL,
                                 "RPC missing message-id attribute",
                                 "rpc", "message-id", false);
            xmlFreeDoc (doc);
            g_free (message);
            break;
        }

        if (g_strcmp0 ((char *) child->name, "close-session") == 0)
        {
            VERBOSE ("Closing session\n");
            send_rpc_ok (session, rpc, true);
            xmlFreeDoc (doc);
            g_free (message);
            break;
        }
        else if (g_strcmp0 ((char *) child->name, "kill-session") == 0)
        {
            VERBOSE ("Handle RPC %s\n", (char *) child->name);
            handle_kill_session (session, rpc);
        }
        else if (g_strcmp0 ((char *) child->name, "get") == 0)
        {
            VERBOSE ("Handle RPC %s\n", (char *) child->name);
            handle_get (session, rpc, false);
        }
        else if (g_strcmp0 ((char *) child->name, "get-config") == 0)
        {
            VERBOSE ("Handle RPC %s\n", (char *) child->name);
            handle_get (session, rpc, true);
        }
        else if (g_strcmp0 ((char *) child->name, "edit-config") == 0)
        {
            VERBOSE ("Handle RPC %s\n", (char *) child->name);
            handle_edit (session, rpc);
        }
        else if (g_strcmp0 ((char *) child->name, "lock") == 0)
        {
            VERBOSE ("Handle RPC %s\n", (char *) child->name);
            handle_lock (session, rpc);
        }
        else if (g_strcmp0 ((char *) child->name, "unlock") == 0)
        {
            VERBOSE ("Handle RPC %s\n", (char *) child->name);
            handle_unlock (session, rpc);
        }
        else
        {
            gchar *error_msg = g_strdup_printf ("Unknown RPC (%s)", child->name);
            VERBOSE ("%s\n", error_msg);
            send_rpc_error_full (session, rpc, NC_ERR_TAG_OPR_NOT_SUPPORTED, NC_ERR_TYPE_PROTOCOL,
                                 error_msg, NULL, NULL, true);
            g_free (error_msg);
            xmlFreeDoc (doc);
            g_free (message);
            break;
        }

        xmlFreeDoc (doc);
        g_free (message);
    }

    VERBOSE ("NETCONF: session terminated\n");
    destroy_session (session);
    return NULL;
}

gboolean
netconf_init (const char *path, const char *supported, const char *logging,
              const char *cp, const char *rm)
{
    if (logging)
    {
        netconf_logging_init (path, logging);
    }

    /* Load Data Models */
    g_schema = sch_load_with_model_list_filename (path, supported);
    if (!g_schema)
    {
        return false;
    }

    /* Create a random starting session ID */
    srand (time (NULL));
    netconf_session_id = rand () % 32768;

    /* Initialise lock */
    reset_lock ();

    /* Set up Apteryx refresh on session information */
    apteryx_refresh (NETCONF_STATE_SESSIONS_PATH "/*", _netconf_sessions_refresh);
    apteryx_watch (NETCONF_SESSION_STATUS, _netconf_clear_session);
    apteryx_watch (NETCONF_CONFIG_MAX_SESSIONS, _netconf_max_sessions);
    apteryx_set_int (NETCONF_STATE, "max-sessions", netconf_max_sessions);

    return true;
}

void
netconf_shutdown (void)
{
    /* Cleanup datamodels */
    if (g_schema)
        sch_free (g_schema);

    netconf_logging_shutdown ();
}
