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

static sch_instance *g_schema = NULL;

struct netconf_session
{
    int fd;
    uint32_t id;
    char *username;
};

static struct _running_ds_lock_t
{
    struct netconf_session nc_sess;
    gboolean locked;
} running_ds_lock;

#define NETCONF_BASE_1_0_END "]]>]]>"
#define NETCONF_BASE_1_1_END "\n##\n"

static uint32_t netconf_session_id = 1;

/* Maintain a list of open sessions */
static GSList *open_sessions_list = NULL;

#define ERR_MSG_NOT_SUPPORTED 0
#define ERR_MSG_MISSING_ATTRIB 1
#define ERR_MSG_MALFORMED 2

static char *error_msgs[] = {
    "operation-not-supported",
    "missing-attribute",
    "malformed-message",
};

/* Close open sessions */
void
netconf_close_open_sessions (void)
{
    if (open_sessions_list)
    {
        for (guint i = 0; i < g_slist_length (open_sessions_list); i++)
        {
            struct netconf_session *nc_session =
                (struct netconf_session *) g_slist_nth_data (open_sessions_list, i);
            if (nc_session->fd >= 0)
            {
                close (nc_session->fd);
                nc_session->fd = -1;
            }
        }
    }
}

/* Remove specified netconf session from open_sessions_list */
static void
remove_netconf_session (struct netconf_session *session)
{
    if (!session || !open_sessions_list)
    {
        return;
    }

    for (guint i = 0; i < g_slist_length (open_sessions_list); i++)
    {
        struct netconf_session *nc_session =
            (struct netconf_session *) g_slist_nth_data (open_sessions_list, i);
        if (session->id == nc_session->id)
        {
            open_sessions_list = g_slist_remove (open_sessions_list, nc_session);
            break;
        }
    }
}

/* Find open netconf session details by ID */
static struct netconf_session *
find_netconf_session_by_id (uint32_t session_id)
{

    for (guint i = 0; i < g_slist_length (open_sessions_list); i++)
    {
        struct netconf_session *nc_session =
            (struct netconf_session *) g_slist_nth_data (open_sessions_list, i);
        if (session_id == nc_session->id)
        {
            return nc_session;
        }
    }

    return NULL;
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

static bool
send_rpc_error (struct netconf_session *session, xmlNode * rpc, const char *error,
                const char *error_msg, xmlNode * error_info)
{
    xmlDoc *doc;
    xmlNode *child;
    xmlChar *xmlbuff = NULL;
    char *header = NULL;
    int len;
    bool ret = true;

    /* Generate reply */
    doc = create_rpc (BAD_CAST "rpc-reply", xmlGetProp (rpc, BAD_CAST "message-id"));
    child = xmlNewChild (xmlDocGetRootElement (doc), NULL, BAD_CAST "rpc-error", NULL);
    xmlNewChild (child, NULL, BAD_CAST "error-tag", BAD_CAST error);
    xmlNewChild (child, NULL, BAD_CAST "error-type", BAD_CAST "rpc");
    xmlNewChild (child, NULL, BAD_CAST "error-severity", BAD_CAST "error");

    if (error_msg != NULL)
    {
        xmlNewChild (child, NULL, BAD_CAST "error-message", BAD_CAST error_msg);
    }

    if (error_info != NULL)
    {
        xmlAddChild (child, error_info);
    }
    else
    {
        xmlNewChild (child, NULL, BAD_CAST "error-info", BAD_CAST NULL);
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
            xml_child = xmlNewChild (cap, NULL, BAD_CAST "capability", NULL);
            capability = g_strdup_printf ("%s?module=%s&amp;revision=%s",
                                          loaded->ns_href, loaded->model, loaded->version);
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
    xmlDoc *doc = NULL;
    xmlNode *root, *node, *child;
    xmlChar *hello_resp = NULL;
    char buffer[4096];
    char session_id_str[32];
    char *endpt;
    int hello_resp_len = 0;
    int len;

    /* Read all of the hello from the peer */
    while (g_main_loop_is_running (g_loop))
    {
        len = recv (session->fd, buffer, 4096, 0);
        // TODO
        break;
    }

    VERBOSE ("RX(%d):\n%.*s", len, (int) len, buffer);

    /* Find trailer */
    endpt = g_strstr_len (buffer, len, NETCONF_BASE_1_0_END);
    if (!endpt)
    {
        ERROR ("XML: Invalid hello message (no 1.0 trailer)\n");
        return false;
    }

    /* Validate hello */
    if (!validate_hello (buffer, (endpt - buffer)))
    {
        return false;
    }

    /* Generate reply */
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
    apteryx_free_tree (query);

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
get_process_action (struct netconf_session *session, xmlNode *node, int schflags,
                    GList **xml_list, char **error)
{
    char *attr;
    xmlNode *tnode;
    GNode *query = NULL;
    sch_xml_to_gnode_parms parms;
    sch_node *qschema = NULL;
    bool is_filter = false;

    /* Check the requested datastore */
    if (g_strcmp0 ((char *) node->name, "source") == 0)
    {
        if (!xmlFirstElementChild (node) ||
            g_strcmp0 ((char *) xmlFirstElementChild (node)->name, "running") != 0)
        {
            VERBOSE ("Datastore \"%s\" not supported",
                        (char *) xmlFirstElementChild (node)->name);
            *error = error_msgs[ERR_MSG_NOT_SUPPORTED];
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
                VERBOSE ("XPATH filter missing select attribute");
                *error = error_msgs[ERR_MSG_MISSING_ATTRIB];
                return -1;
            }
            VERBOSE ("FILTER: XPATH: %s\n", attr);
            is_filter = true;
            query = sch_path_to_gnode (g_schema, NULL, attr, schflags | SCH_F_XPATH, &qschema);
            if (!query)
            {
                VERBOSE ("XPATH: malformed filter\n");
                *error = error_msgs[ERR_MSG_MALFORMED];
                return -1;
            }

            if (qschema)
            {
                if (sch_is_leaf (qschema) && !sch_is_readable (qschema))
                {
                    VERBOSE ("NETCONF: Path \"%s\" not readable\n", attr);
                    *error = error_msgs[ERR_MSG_NOT_SUPPORTED];
                    return -1;
                }
                get_query_schema (session, query, qschema, schflags, is_filter, xml_list);
            }
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
                    free (attr);
                    *error = error_msgs[ERR_MSG_MALFORMED];
                    return -1;
                }

                if (qschema)
                {
                    if (sch_is_leaf (qschema) && !sch_is_readable (qschema))
                    {
                        VERBOSE ("NETCONF: Path \"%s\" not readable\n", attr);
                        *error = error_msgs[ERR_MSG_NOT_SUPPORTED];
                        return -1;
                    }
                    get_query_schema (session, query, qschema, schflags, is_filter, xml_list);
                }
            }
        }
        else
        {
            VERBOSE ("FILTER: unsupported/missing type (%s)\n", attr);
            free (attr);
            *error = error_msgs[ERR_MSG_NOT_SUPPORTED];
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
    char *error = NULL;
    GList *xml_list = NULL;
    GList *list;
    int schflags = 0;
    char *msg = NULL;
    char session_id_str[32];
    xmlNode *error_info;

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
        error_info = xmlNewNode (NULL, BAD_CAST "error-info");
        snprintf (session_id_str, sizeof (session_id_str), "%u",
                  running_ds_lock.nc_sess.id);
        xmlNewChild (error_info, NULL, BAD_CAST "session-id", BAD_CAST session_id_str);
        msg = "Lock failed, lock is already held";
        return send_rpc_error (session, rpc, "lock-denied", msg, error_info);
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
                ERROR ("WITH-DEFAULTS: No support for with-defaults query type \"%s\"\n", defaults_type);
                free (defaults_type);
                return send_rpc_error (session, rpc, error_msgs[ERR_MSG_NOT_SUPPORTED], NULL, NULL);
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

        if (get_process_action (session, node, schflags, &xml_list, &error) < 0)
        {
            /* Cleanup any requests added to the xml_list before hitting an error */
            for (list = g_list_first (xml_list); list; list = g_list_next (list))
            {
                xmlFree (list->data);
            }
            g_list_free (xml_list);

            return send_rpc_error (session, rpc, error, NULL, NULL);
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
_check_exist (const char *check_xpath, char **error_tag, bool expected)
{
    GNode *check_result;

    check_result = apteryx_get_tree (check_xpath);
    if (check_result && !expected)
    {
        *error_tag = "data-exists";
    }
    else if (!check_result && expected)
    {
        *error_tag = "data-missing";
    }
    apteryx_free_tree (check_result);
}

static bool
handle_edit (struct netconf_session *session, xmlNode * rpc)
{
    xmlNode *action = xmlFirstElementChild (rpc);
    xmlNode *node;
    GNode *tree = NULL;
    char *error_tag;
    sch_xml_to_gnode_parms parms;
    sch_node *qschema = NULL;
    int schflags = 0;
    GList *iter;
    char *msg = NULL;
    char session_id_str[32];
    xmlNode *error_info;

    if (apteryx_netconf_verbose)
        schflags |= SCH_F_DEBUG;

    /* Check the target */
    node = xmlFindNodeByName (action, BAD_CAST "target");
    if (!node || !xmlFirstElementChild (node) ||
        xmlStrcmp (xmlFirstElementChild (node)->name, BAD_CAST "running"))
    {
        VERBOSE ("Datastore \"%s\" not supported",
                 (char *) xmlFirstElementChild (node)->name);
        return send_rpc_error (session, rpc, error_msgs[ERR_MSG_NOT_SUPPORTED], NULL, NULL);
    }

    //TODO Check default-operation
    //TODO Check test-option
    //TODO Check error-option
    //
    /* Validate lock if configured on the running datastore */
    if (running_ds_lock.locked == TRUE && (session->id != running_ds_lock.nc_sess.id))
    {
        /* A lock is already held by another NETCONF session, return lock-denied */
        VERBOSE ("Lock failed, lock is already held\n");
        error_info = xmlNewNode (NULL, BAD_CAST "error-info");
        snprintf (session_id_str, sizeof (session_id_str), "%u",
                  running_ds_lock.nc_sess.id);
        xmlNewChild (error_info, NULL, BAD_CAST "session-id", BAD_CAST session_id_str);
        msg = "Lock failed, lock is already held";
        return send_rpc_error (session, rpc, "lock-denied", msg, error_info);
    }

    /* Find the config */
    node = xmlFindNodeByName (action, BAD_CAST "config");
    if (!node)
    {
        VERBOSE ("Missing \"config\" element");
        return send_rpc_error (session, rpc, "missing-element", NULL, NULL);
    }

    /* Convert to gnode */
    parms =
        sch_xml_to_gnode (g_schema, NULL, xmlFirstElementChild (node), schflags, "merge",
                          true, &qschema);
    tree = sch_parm_tree (parms);
    error_tag = sch_parm_error_tag (parms);

    if (error_tag)
    {
        VERBOSE ("error parsing XML\n");
        sch_parm_free (parms);
        apteryx_free_tree (tree);
        return send_rpc_error (session, rpc, error_tag, NULL, NULL);
    }

    /* Check delete and create paths */
    for (iter = sch_parm_deletes (parms); iter; iter = g_list_next (iter))
    {
        _check_exist ((char *) iter->data, &error_tag, true);
    }
    for (iter = sch_parm_creates (parms); iter; iter = g_list_next (iter))
    {
        _check_exist ((char *) iter->data, &error_tag, false);
    }
    if (error_tag)
    {
        VERBOSE ("error in delete or create paths\n");
        sch_parm_free (parms);
        apteryx_free_tree (tree);
        return send_rpc_error (session, rpc, error_tag, NULL, NULL);
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
        apteryx_free_tree (tree);
        return send_rpc_error (session, rpc, "operation-failed", NULL, NULL);
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
    xmlNode *error_info, *node;
    char *msg = NULL;
    char session_id_str[32];

    /* Check the target */
    node = xmlFindNodeByName (action, BAD_CAST "target");
    if (!node || !xmlFirstElementChild (node) ||
        xmlStrcmp (xmlFirstElementChild (node)->name, BAD_CAST "running"))
    {
        VERBOSE ("Datastore \"%s\" not supported",
                 (char *) xmlFirstElementChild (node)->name);
        return send_rpc_error (session, rpc, error_msgs[ERR_MSG_NOT_SUPPORTED], NULL, NULL);
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
        VERBOSE ("Lock failed, lock is already held\n");
        error_info = xmlNewNode (NULL, BAD_CAST "error-info");
        snprintf (session_id_str, sizeof (session_id_str), "%u",
                  running_ds_lock.nc_sess.id);
        xmlNewChild (error_info, NULL, BAD_CAST "session-id", BAD_CAST session_id_str);
        msg = "Lock failed, lock is already held";
        return send_rpc_error (session, rpc, "lock-denied", msg, error_info);
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
    xmlNode *error_info, *node;
    char *msg = NULL;
    char session_id_str[32];

    /* Check the target */
    node = xmlFindNodeByName (action, BAD_CAST "target");
    if (!node || !xmlFirstElementChild (node) ||
        xmlStrcmp (xmlFirstElementChild (node)->name, BAD_CAST "running"))
    {
        VERBOSE ("Datastore \"%s\" not supported",
                 (char *) xmlFirstElementChild (node)->name);
        return send_rpc_error (session, rpc, error_msgs[ERR_MSG_NOT_SUPPORTED], NULL, NULL);
    }

    /* Check unlock operation validity */
    if ((running_ds_lock.locked != TRUE) ||
        ((running_ds_lock.locked == TRUE) && (session->id != running_ds_lock.nc_sess.id)))
    {
        /* Lock held by another session */
        VERBOSE ("Unlock failed, session does not own lock on the datastore\n");
        error_info = xmlNewNode (NULL, BAD_CAST "error-info");
        snprintf (session_id_str, sizeof (session_id_str), "%u",
                  running_ds_lock.nc_sess.id);
        xmlNewChild (error_info, NULL, BAD_CAST "session-id", BAD_CAST session_id_str);
        msg = "Unlock failed, session does not own lock on the datastore";
        return send_rpc_error (session, rpc, "operation-failed", msg, error_info);
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
    char *msg = NULL;
    struct netconf_session *kill_session = NULL;
    xmlChar* content = NULL;

    /* Validate request */
    node = xmlFindNodeByName (action, BAD_CAST "session-id");
    if (!node)
    {
        VERBOSE ("Missing \"session-id\" element");
        msg = "Missing \"session-id\" element";
        return send_rpc_error (session, rpc, "missing-element", msg, NULL);
    }

    /* Return an "invalid-error" if the request is made by the current session */
    content = xmlNodeGetContent (node);
    sscanf ((char *) content, "%u", &kill_session_id);
    xmlFree (content);

    if (kill_session_id == 0)
    {
        VERBOSE ("Invalid session ID");
        return send_rpc_error (session, rpc, "invalid-value", NULL, NULL);
    }
    else if (session->id == kill_session_id)
    {
        VERBOSE ("Attempt to kill own session is forbidden");
        msg = "Attempt to kill own session is forbidden";
        return send_rpc_error (session, rpc, "invalid-value", msg, NULL);
    }

    kill_session = find_netconf_session_by_id (kill_session_id);

    if (!kill_session)
    {
        VERBOSE ("Invalid session ID");
        return send_rpc_error (session, rpc, "invalid-value", NULL, NULL);
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


static struct netconf_session *
create_session (int fd)
{
    struct netconf_session *session = g_malloc (sizeof (struct netconf_session));
    session->fd = fd;
    session->id = netconf_session_id++;

    /* If the counter rounds, then the value 0 is not allowed */
    if (!session->id)
    {
        session->id = netconf_session_id++;
    }

    /* Append to open sessions list */
    open_sessions_list = g_slist_append (open_sessions_list, session);

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

    if (session->username)
        g_free (session->username);

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
    while (g_main_loop_is_running (g_loop))
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
    while (g_main_loop_is_running (g_loop))
    {
        int chunk_len;

        /* Get chunk length */
        chunk_len = read_chunk_size (session);
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

    /* Get user information from the calling process */
    if (getsockopt (fd, SOL_SOCKET, SO_PEERCRED, &ucred, &len) >= 0)
    {
        struct passwd *pw = getpwuid(ucred.uid);
        if (pw)
        {
            session->username = g_strdup(pw->pw_name);
        }
    }

    /* Process hello's first */
    if (!handle_hello (session))
    {
        destroy_session (session);
        return NULL;
    }

    /* Process chunked RPC's */
    while (g_main_loop_is_running (g_loop))
    {
        xmlDoc *doc = NULL;
        xmlNode *rpc, *child;
        char *message;
        int len;

        /* Receive message */
        message = receive_message (session, &len);
        if (!message)
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
            VERBOSE ("Unknown RPC (%s)\n", child->name);
            send_rpc_error (session, rpc, error_msgs[ERR_MSG_NOT_SUPPORTED], NULL, NULL);
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
