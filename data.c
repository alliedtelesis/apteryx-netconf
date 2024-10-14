/**
 * @file data.c
 * Data translation utilities
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
#include <apteryx-xml.h>

typedef struct _sch_xml_to_gnode_parms_s
{
    sch_instance *in_instance;
    int in_flags;
    char *in_def_op;
    bool in_is_edit;
    GNode *out_tree;
    nc_error_parms out_error;
    GList *out_deletes;
    GList *out_removes;
    GList *out_creates;
    GList *out_replaces;
    GList *out_merges;
    GList *conditions;
} _sch_xml_to_gnode_parms;

/* List keys must escape any '/' which is the only reserved
   character in apteryx */
static char *
_sch_key_encode (const char *key)
{
    GString *encoded = g_string_new (NULL);
    const char *c = key;
    while (c && *c)
    {
        if (*c == '/')
            g_string_append_printf (encoded, "%%%02X", *c);
        else
            g_string_append_c (encoded, *c);
        c++;
    }
    return g_string_free (encoded, false);
}

static bool
_sch_node_find_name (xmlNs *ns, sch_node * parent, const char *path_name, GList **path_list)
{
    xmlNode *xml = (xmlNode *) parent;
    xmlNode *n = NULL;
    bool found = false;

    n = xml->children;
    while (n)
    {
        if (n->type == XML_ELEMENT_NODE && n->name[0] == 'N')
        {
            char *name = (char *) xmlGetProp (n, (xmlChar *) "name");
            if (sch_match_name (name, path_name) && sch_ns_match (n, ns))
            {
                xmlFree (name);
                found = true;
                break;
            }
            if (n->children)
            {
                found = _sch_node_find_name (ns, n, path_name, path_list);
                if (found)
                {
                    *path_list = g_list_prepend (*path_list, g_strdup (name));
                    xmlFree (name);
                    break;
                }
            }
            xmlFree (name);
        }
        n = n->next;
    }
    return found;
}

static bool
sch_node_find_name (sch_instance *instance, xmlNs *ns, sch_node *parent, const char *path, int flags, GList **path_list)
{
    char *name;
    char *next;
    char *colon;
    bool found = false;

    if (path && path[0] == '/')
    {
        path++;

        /* Parse path element */
        next = strchr (path, '/');
        if (next)
            name = g_strndup (path, next - path);
        else
            name = g_strdup (path);
        colon = strchr (name, ':');
        if (colon)
        {
            colon[0] = '\0';
            xmlNs *nns = sch_lookup_ns (instance, parent, name, flags, false);
            if (!nns)
            {
                /* No namespace found assume the node is supposed to have a colon in it */
                colon[0] = ':';
            }
            else
            {
                /* We found a namespace. Remove the prefix */
                char *_name = name;
                name = g_strdup (colon + 1);
                free (_name);
                ns = nns;
            }
        }
        found = _sch_node_find_name (ns, parent, name, path_list);
        g_free (name);
    }
    return found;
}

static void
sch_check_condition_parms (_sch_xml_to_gnode_parms *_parms, sch_node *node, char *new_xpath)
{
    xmlChar *when_clause = xmlGetProp ((xmlNode *) node, BAD_CAST "when");
    xmlChar *must_clause = xmlGetProp ((xmlNode *) node, BAD_CAST "must");
    xmlChar *if_feature = xmlGetProp ((xmlNode *) node, BAD_CAST "if-feature");

    if (when_clause)
    {
        _parms->conditions = g_list_append (_parms->conditions, g_strdup (new_xpath));
        _parms->conditions = g_list_append (_parms->conditions, g_strdup ((char *) when_clause));
        DEBUG ("when_clause <%s - %s>\n", new_xpath, when_clause);
        xmlFree (when_clause);
    }

    if (must_clause)
    {
        _parms->conditions = g_list_append (_parms->conditions, g_strdup (new_xpath));
        _parms->conditions = g_list_append (_parms->conditions, g_strdup ((char *) must_clause));
        DEBUG ("must_clause <%s - %s>\n", new_xpath, must_clause);
        xmlFree (must_clause);
    }

    if (if_feature)
    {
        _parms->conditions = g_list_append (_parms->conditions, g_strdup (new_xpath));
        _parms->conditions = g_list_append (_parms->conditions,
                                                 g_strdup_printf ("if-feature(%s)", (char *) if_feature));
        DEBUG("if_feature <%s - %s>\n", new_xpath, if_feature);
        xmlFree (if_feature);
    }
}


static xmlNode *
_sch_gnode_to_xml (sch_instance * instance, sch_node * schema, sch_ns *ns, xmlNode * parent,
                   GNode * node, int flags, int depth)
{
    sch_node *pschema = schema;
    xmlNode *data = NULL;
    char *colon = NULL;
    char *name;
    char *condition = NULL;
    char *path = NULL;

    /* Get the actual node name */
    if (depth == 0 && strlen (APTERYX_NAME (node)) == 1)
    {
        return _sch_gnode_to_xml (instance, schema, ns, parent, node->children, flags, depth);
    }
    else if (depth == 0 && APTERYX_NAME (node)[0] == '/')
    {
        name = g_strdup (APTERYX_NAME (node) + 1);
    }
    else
    {
        name = g_strdup (APTERYX_NAME (node));
    }

    colon = strchr (name, ':');
    if (colon)
    {
        colon[0] = '\0';
        sch_ns *nns = sch_lookup_ns (instance, schema, name, flags, false);
        if (!nns)
        {
            /* No namespace found assume the node is supposed to have a colon in it */
            colon[0] = ':';
        }
        else
        {
            /* We found a namespace. Remove the prefix */
            char *_name = name;
            name = g_strdup (colon + 1);
            free (_name);
            ns = nns;
        }
    }

    /* Find schema node */
    if (sch_is_proxy (schema))
    {
        /* Two possible cases, the node is a child of the proxy node or we need to
         * move to access the remote database via the proxy */
        schema = sch_ns_node_child (ns, schema, name);
        if (!schema)
        {
            schema = sch_get_root_schema (instance);
            colon = strchr (name, ':');
            if (schema && colon)
            {
                colon[0] = '\0';
                xmlNs *nns = sch_lookup_ns (instance, schema, name, flags, false);
                if (!nns)
                {
                    /* No namespace found assume the node is supposed to have a colon in it */
                    colon[0] = ':';
                }
                else
                {
                    /* We found a namespace. Remove the prefix */
                    char *_name = name;
                    name = g_strdup (colon + 1);
                    free (_name);
                    ns = nns;
                }
            }
            schema = sch_ns_node_child (ns, schema, name);
        }
    }
    else
    {
        if (!schema)
            schema = sch_get_root_schema (instance);
        schema = sch_ns_node_child (ns, schema, name);
    }

    if (schema == NULL)
    {
        DEBUG ("No schema match for gnode %s%s%s\n",
               ns ? sch_ns_prefix (instance, ns) : "", ns ? ":" : "", name);
        free (name);
        return NULL;
    }
    if (!sch_is_readable (schema))
    {
        DEBUG ("Ignoring non-readable node %s%s%s\n",
               ns ? sch_ns_prefix (instance, ns) : "", ns ? ":" : "", name);
        free (name);
        return NULL;
    }

    flags |= SCH_F_CONDITIONS;
    sch_check_condition (schema, node, flags, &path, &condition);
    if (condition)
    {
        if (!sch_process_condition (netconf_get_g_schema (), node, path, condition))
        {
            g_free (condition);
            g_free (path);
            free (name);
            return NULL;
        }
        g_free (condition);
        g_free (path);
    }

    if (sch_is_leaf_list (schema))
    {
        xmlNode *prev = NULL;
        apteryx_sort_children (node, g_strcmp0);
        for (GNode * child = node->children; child; child = child->next)
        {
            GNode *value_node = child->children;
            if (value_node)
            {
                char *leaf_name = APTERYX_NAME (value_node);
                xmlNode *list_data = xmlNewNode (NULL, BAD_CAST name);
                xmlNodeSetContent (list_data, (const xmlChar *) leaf_name);
                sch_ns *sns = sch_node_ns (schema);
                if (!pschema || !sch_ns_match (pschema, sns))
                {
                    const xmlChar *href = (const xmlChar *) sch_ns_href (instance, sns);
                    xmlNsPtr nns = xmlNewNs (list_data, href, NULL);
                    xmlSetNs (list_data, nns);
                }
                if (parent)
                    xmlAddChildList (parent, list_data);
                else if (prev)
                    prev = xmlAddSibling (prev, list_data);
                else
                    prev = list_data;
                if (!data)
                    data = list_data;
                DEBUG ("%*s%s = %s\n", depth * 2, " ", APTERYX_NAME (node), leaf_name);
            }
        }
    }
    else if (sch_is_list (schema))
    {
        xmlNode *prev = NULL;
        xmlNode *list_data = NULL;
        data = NULL;

        apteryx_sort_children (node, g_strcmp0);
        for (GNode * child = node->children; child; child = child->next)
        {
            gboolean has_child = false;

            DEBUG ("%*s%s[%s]\n", depth * 2, " ", APTERYX_NAME (node),
                   APTERYX_NAME (child));
            list_data = xmlNewNode (NULL, BAD_CAST name);
            sch_ns *sns = sch_node_ns (schema);
            if (!pschema || !sch_ns_match (pschema, sns))
            {
                const xmlChar *href = (const xmlChar *) sch_ns_href (instance, sns);
                xmlNsPtr nns = xmlNewNs (list_data, href, NULL);
                xmlSetNs (list_data, nns);
            }
            sch_gnode_sort_children (sch_node_child_first (schema), child);
            for (GNode * field = child->children; field; field = field->next)
            {
                if (_sch_gnode_to_xml (instance, sch_node_child_first (schema), ns,
                                       list_data, field, flags, depth + 1))
                {
                    has_child = true;
                }
            }
            if (has_child)
            {
                if ((flags & SCH_F_XPATH))
                {
                    char *key = sch_list_key (schema);
                    if (key)
                    {
                        xmlNode *n = list_data->children;
                        while (n)
                        {
                            if (n->type == XML_ELEMENT_NODE && g_strcmp0 (key, (char *) n->name) == 0)
                                break;
                            n = n->next;
                        }

                        if (!n)
                        {
                            xmlNode *key_data = xmlNewNode (NULL, BAD_CAST key);
                            xmlNodeSetContent (key_data, (const xmlChar *) APTERYX_NAME (child));
                            xmlAddPrevSibling (list_data->children, key_data);
                        }
                        g_free (key);
                    }
                }
                if (parent)
                    xmlAddChildList (parent, list_data);
                else if (prev)
                    prev = xmlAddSibling (prev, list_data);
                else
                    prev = list_data;
                if (!data)
                    data = list_data;
            }
            else
            {
                xmlFreeNode (list_data);
                list_data = NULL;
            }
        }
    }
    else if (!sch_is_leaf (schema))
    {
        gboolean has_child = false;

        DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
        data = xmlNewNode (NULL, BAD_CAST name);
        sch_gnode_sort_children (schema, node);
        for (GNode * child = node->children; child; child = child->next)
        {
            if (_sch_gnode_to_xml (instance, schema, ns, data, child, flags, depth + 1))
            {
                has_child = true;
            }
        }
        /* Add this node if we found children or its an empty presence container */
        if (parent && (has_child || !((xmlNode *)schema)->children))
        {
            xmlAddChild (parent, data);
        }
        else if (!has_child)
        {
            xmlFreeNode (data);
            data = NULL;
        }
    }
    else if (APTERYX_HAS_VALUE (node))
    {
        if (!(flags & SCH_F_CONFIG) || sch_is_writable (schema))
        {
            char *value = g_strdup (APTERYX_VALUE (node) ? APTERYX_VALUE (node) : "");
            xmlChar *idref_href;
            xmlChar *idref_prefix;

            data = xmlNewNode (NULL, BAD_CAST name);
            value = sch_translate_to (schema, value);
            idref_href = xmlGetProp ((xmlNode *) schema, BAD_CAST "idref_href");
            if (idref_href)
            {
                char *temp = value;
                idref_prefix = xmlGetProp ((xmlNode *) schema, BAD_CAST "idref_prefix");
                if (idref_prefix)
                {
                    value = g_strdup_printf ("%s:%s", (char *) idref_prefix, value);
                    xmlNs *nns = xmlNewNs (data, idref_href, NULL);
                    xmlSetNs (data, nns);
                    g_free (temp);
                    xmlFree (idref_prefix);
                }
                xmlFree (idref_href);
            }

            xmlNodeSetContent (data, (const xmlChar *) value);
            if (parent)
                xmlAddChildList (parent, data);
            DEBUG ("%*s%s = %s\n", depth * 2, " ", APTERYX_NAME (node), value);
            free (value);
        }
    }

    /* Record any changes to the namespace (including the root node) */
    if (data && schema && (!pschema || ((xmlNode *)pschema)->ns != ((xmlNode *)schema)->ns))
    {
        /* Dont store a prefix as we set the default xmlns at each node */
        xmlNsPtr nns = xmlNewNs (data, ((xmlNode *)schema)->ns->href, NULL);
        xmlSetNs (data, nns);
    }

    free (name);
    return data;
}

xmlNode *
sch_gnode_to_xml (sch_instance * instance, sch_node * schema, GNode * node, int flags)
{
    if (node && g_node_n_children (node) > 1 && strlen (APTERYX_NAME (node)) == 1)
    {
        xmlNode *first = NULL;
        xmlNode *last = NULL;
        xmlNode *next;

        apteryx_sort_children (node, g_strcmp0);
        for (GNode * child = node->children; child; child = child->next)
        {
            next = _sch_gnode_to_xml (instance, schema, NULL, NULL, child, flags, 1);
            if (next)
            {
                if (last)
                    xmlAddSibling (last, next);
                last = next;
                if (!first)
                    first = next;
            }
        }
        return first;
    }
    else
        return _sch_gnode_to_xml (instance, schema, NULL, NULL, node, flags, 0);
}

static bool
xml_node_has_content (xmlNode * xml)
{
    char *content = (char *) xmlNodeGetContent (xml);
    bool ret = (content && strlen (content) > 0);
    free (content);
    return ret;
}

/**
 * Check XML node for the operation attribute and extract it. Return whether the
 * operation is recognised or not.
 */
static bool
_operation_ok (_sch_xml_to_gnode_parms *_parms, xmlNode *xml, char *curr_op, char **new_op)
{
    char *attr;

    attr = (char *) xmlGetProp (xml, BAD_CAST "operation");
    if (attr != NULL)
    {
        if (!_parms->in_is_edit)
        {
            _parms->out_error.tag = NC_ERR_TAG_BAD_ATTR;
            _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
            g_hash_table_insert (_parms->out_error.info, "bad-element", g_strdup ("operation"));
            g_hash_table_insert (_parms->out_error.info, "bad-attribute", attr);

            return false;
        }

        /* Find new attribute. */
        if (g_strcmp0 (attr, "delete") == 0)
        {
            *new_op = "delete";
        }
        else if (g_strcmp0 (attr, "merge") == 0)
        {
            *new_op = "merge";
        }
        else if (g_strcmp0 (attr, "replace") == 0)
        {
            *new_op = "replace";
        }
        else if (g_strcmp0 (attr, "create") == 0)
        {
            *new_op = "create";
        }
        else if (g_strcmp0 (attr, "remove") == 0)
        {
            *new_op = "remove";
        }
        else
        {
            _parms->out_error.tag = NC_ERR_TAG_UNKNOWN_ATTR;
            _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
            g_hash_table_insert (_parms->out_error.info, "bad-element", g_strdup ("operation"));
            g_hash_table_insert (_parms->out_error.info, "bad-attribute", attr);
            return false;
        }
        g_free (attr);

        /* Check for invalid transitions between sub-operations. We only allow
         * merge->anything transitions.
         */
        if (g_strcmp0 (curr_op, *new_op) != 0 && g_strcmp0 (curr_op, "merge") != 0 &&
            g_strcmp0 (curr_op, "none") != 0)
        {
            _parms->out_error.tag = NC_ERR_TAG_OPR_NOT_SUPPORTED;
            _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
            return false;
        }
    }
    return true;
}

static void
_perform_actions (_sch_xml_to_gnode_parms *_parms, int depth, char *curr_op, char *new_op, char *new_xpath)
{
    /* Do nothing if not an edit, or operation not changing, unless depth is 0. */
    if (!_parms->in_is_edit || (g_strcmp0 (curr_op, new_op) == 0 && depth != 0))
    {
        return;
    }

    /* Handle operations. */
    if (g_strcmp0 (new_op, "delete") == 0)
    {
        _parms->out_deletes = g_list_append (_parms->out_deletes, g_strdup (new_xpath));
        DEBUG ("delete <%s>\n", new_xpath);
    }
    else if (g_strcmp0 (new_op, "remove") == 0)
    {
        _parms->out_removes = g_list_append (_parms->out_removes, g_strdup (new_xpath));
        DEBUG ("remove <%s>\n", new_xpath);
    }
    else if (g_strcmp0 (new_op, "create") == 0)
    {
        _parms->out_creates = g_list_append (_parms->out_creates, g_strdup (new_xpath));
        DEBUG ("create <%s>\n", new_xpath);
    }
    else if (g_strcmp0 (new_op, "replace") == 0)
    {
        _parms->out_replaces = g_list_append (_parms->out_replaces, g_strdup (new_xpath));
        DEBUG ("replace <%s>\n", new_xpath);
    }
}

static GNode *
_sch_xml_to_gnode (_sch_xml_to_gnode_parms *_parms, sch_node * schema, sch_ns *ns, char * part_xpath,
                   char * curr_op, GNode * pparent, xmlNode * xml, int depth, sch_node **rschema, char ** edit_op)
{
    sch_instance *instance = _parms->in_instance;
    int flags = _parms->in_flags;
    char *name = (char *) xml->name;
    xmlNode *child;
    char *attr;
    GNode *tree = NULL;
    GNode *node = NULL;
    char *key = NULL;
    char *new_xpath = NULL;
    char *new_op = curr_op;
    bool key_valid = false;
    bool ret_tree = false;
    bool is_proxy = false;
    bool read_only = false;

    /* Detect change in namespace */
    if (xml->ns && xml->ns->href)
    {
         sch_ns *nns = sch_lookup_ns (instance, schema, (const char *) xml->ns->href, flags, true);
         if (nns)
            ns = nns;
    }

    /* Find schema node */
    if (schema && sch_is_proxy (schema))
    {
        /* The schema containing the proxy node can have children */
        sch_node *child = sch_ns_node_child (ns, schema, name);
        if (!child)
        {
            is_proxy = sch_is_proxy (schema);
            read_only = sch_is_read_only_proxy (schema);
        }
    }

    if (!schema || is_proxy)
    {
        schema = sch_get_root_schema (instance);
        /* Detect change in namespace with the new schema */
        if (xml->ns && xml->ns->href)
        {
             sch_ns *nns = sch_lookup_ns (instance, schema, (const char *) xml->ns->href, flags, true);
             if (nns)
                ns = nns;
        }
    }
    schema = sch_ns_node_child (ns, schema, name);
    if (schema == NULL)
    {
        DEBUG ("No schema match for xml node %s%s%s\n",
               ns ? sch_ns_prefix (instance, ns) : "", ns ? ":" : "", name);
        _parms->out_error.tag = NC_ERR_TAG_MALFORMED_MSG;
        _parms->out_error.type = NC_ERR_TYPE_RPC;
        return NULL;
    }
    if (_parms->in_is_edit && read_only)
    {
        DEBUG ("Invalid operation\n");
        _parms->out_error.tag = NC_ERR_TAG_INVALID_VAL;
        _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
        return NULL;
    }
    if (rschema)
        *rschema = schema;

    /* Prepend non default namespaces to root nodes */
    if ((depth == 0 || is_proxy) && ns && sch_ns_prefix (instance, ns) && !sch_ns_native (instance, ns))
        name = g_strdup_printf ("%s:%s", sch_ns_prefix (instance, ns), (const char *) xml->name);
    else
        name = g_strdup ((char *) xml->name);

    /* Update xpath. */
    new_xpath = g_strdup_printf ("%s/%s", part_xpath, name);

    /* Check operation, error tag set on exit from routine. */
    if (!_operation_ok (_parms, xml, curr_op, &new_op))
    {
        DEBUG ("Invalid operation\n");
        free (new_xpath);
        free (name);
        return NULL;
    }

    if (edit_op && new_op)
        *edit_op = new_op;

    /* LIST */
    if (sch_is_leaf_list (schema))
    {
        char *old_xpath = new_xpath;
        sch_node *parent = schema;

        DEBUG ("%*s%s%s\n", depth * 2, " ", depth ? "" : "/", name);
        tree = APTERYX_NODE (NULL, g_strdup_printf ("%s%s", depth ? "" : "/", name));
        schema = sch_node_child_first (schema);

        if (xml_node_has_content (xml))
        {
            if (_parms->in_is_edit)
                sch_check_condition_parms (_parms, parent, new_xpath);

            char *content = (char *) xmlNodeGetContent (xml);
            if (_parms->in_is_edit && !sch_validate_pattern (schema, content))
            {
                DEBUG ("Invalid value \"%s\" for node \"%s\"\n", content, name);
                g_free (content);
                apteryx_free_tree (tree);
                _parms->out_error.tag = NC_ERR_TAG_INVALID_VAL;
                _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
                tree = NULL;
                goto exit;
            }

            char *key_value = _sch_key_encode (content);
            if (g_strcmp0 (new_op, "delete") == 0 || g_strcmp0 (new_op, "remove") == 0 ||
                g_strcmp0 (new_op, "none") == 0)
            {
                new_xpath = g_strdup_printf ("%s/%s", old_xpath, key_value);
            }
            else
            {
                new_xpath = g_strdup_printf ("%s/%s", old_xpath, key_value);
                node = APTERYX_NODE (tree, g_strdup (key_value));
                node = APTERYX_NODE (node, g_strdup (content));
                if (_parms->in_is_edit && g_strcmp0 (new_op, "merge") == 0)
                {
                    _parms->out_merges =
                        g_list_append (_parms->out_merges, g_strdup(new_xpath));
                    DEBUG ("merge <%s>\n", new_xpath);
                }
            }
            g_free (content);
            g_free (key_value);
            g_free (old_xpath);
            ret_tree = true;
        }
        else
        {
            node = APTERYX_NODE (tree, g_strdup ("*"));
        }

        if (rschema)
            *rschema = schema;
    }
    else if (sch_is_list (schema))
    {
        char *old_xpath = new_xpath;
        char *key_value;

        key = sch_name (sch_node_child_first (sch_node_child_first (schema)));
        DEBUG ("%*s%s%s\n", depth * 2, " ", depth ? "" : "/", name);
        tree = node = APTERYX_NODE (NULL, g_strdup_printf ("%s%s", depth ? "" : "/", name));
        depth++;
        attr = (char *) xmlGetProp (xml, BAD_CAST key);
        if (attr)
        {
            key_value = _sch_key_encode (attr);
            free (attr);
            node = APTERYX_NODE (node, key_value);
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
            if (!(_parms->in_flags & SCH_F_STRIP_KEY) || xmlFirstElementChild (xml))
            {
                GNode *_node = APTERYX_NODE (node, g_strdup (key));
                DEBUG ("%*s%s\n", (depth + 1) * 2, " ", key);
                if (!_parms->in_is_edit)
                    g_node_prepend_data (_node, NULL);
            }
        }
        else if (xmlFirstElementChild (xml) &&
                 g_strcmp0 ((const char *) xmlFirstElementChild (xml)->name, key) == 0 &&
                 xml_node_has_content (xmlFirstElementChild (xml)))
        {
            char *content = (char *) xmlNodeGetContent (xmlFirstElementChild (xml));
            key_value = _sch_key_encode (content);
            free (content);
            node = APTERYX_NODE (node, key_value);
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
        }
        else
        {
            key_value = g_strdup ("*");
            node = APTERYX_NODE (node, key_value);
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
        }

        if (_parms->in_is_edit)
            sch_check_condition_parms (_parms, schema, new_xpath);

        schema = sch_node_child_first (schema);
        if (rschema)
            *rschema = schema;

        new_xpath = g_strdup_printf ("%s/%s", old_xpath, key_value);
        g_free (old_xpath);
    }
    /* CONTAINER */
    else if (!sch_is_leaf (schema))
    {
        DEBUG ("%*s%s%s\n", depth * 2, " ", depth ? "" : "/", name);
        tree = node = APTERYX_NODE (NULL, g_strdup_printf ("%s%s", depth ? "" : "/", name));
        if (_parms->in_is_edit)
            sch_check_condition_parms (_parms, schema, new_xpath);
    }
    /* LEAF */
    else
    {
        /* Check that this leaf is writable */
        if (_parms->in_is_edit && !sch_is_writable (schema))
        {
            DEBUG ("Attempt to edit non-writable node \"%s\"\n", name);
            apteryx_free_tree (tree);
            _parms->out_error.tag = NC_ERR_TAG_INVALID_VAL;
            _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
            tree = NULL;
            goto exit;
        }

        if (g_strcmp0 (new_op, "delete") != 0 && g_strcmp0 (new_op, "remove") != 0 &&
            g_strcmp0 (new_op, "none") != 0)
        {
            sch_node *sch_parent;
            gboolean validate = true;
            char *value = NULL;

            tree = node = APTERYX_NODE (NULL, g_strdup (name));
            ret_tree = true;
            if (!xml_node_has_content (xml) && !(_parms->in_flags & SCH_F_STRIP_DATA)
                    && (_parms->in_is_edit))
            {
                value = g_strdup ("");
            }
            else if (xml_node_has_content (xml) && !(_parms->in_flags & SCH_F_STRIP_DATA))
            {
                value = (char *) xmlNodeGetContent (xml);
                value = sch_translate_from (schema, value);
            }
            else
            {
                DEBUG ("%*s%s%s\n", depth * 2, " ", depth ? "" : "/", name);
                validate = false;
            }

            /* Can now validate value, whether or not it is an empty string */
            if (validate)
            {
                if (_parms->in_is_edit && !sch_validate_pattern (schema, value))
                {
                    DEBUG ("Invalid value \"%s\" for node \"%s\"\n", value, name);
                    free (value);
                    apteryx_free_tree (tree);
                    _parms->out_error.tag = NC_ERR_TAG_INVALID_VAL;
                    _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
                    tree = NULL;
                    goto exit;
                }

                if (_parms->in_is_edit)
                    sch_check_condition_parms (_parms, schema, new_xpath);

                /* Test for RFC6241 section 6.2.5 compliance */
                sch_parent = sch_node_parent (sch_node_parent (schema));
                if (!_parms->in_is_edit && sch_parent && sch_is_list (sch_parent))
                {
                    xmlNode *xml_parent = xml->parent;
                    xml_parent = xml_parent->parent;
                    char * key = sch_name (sch_node_child_first (sch_node_child_first (sch_parent)));

                    xml_parent = xml->parent;
                    for (child = xmlFirstElementChild (xml_parent); child; child = xmlNextElementSibling (child))
                    {
                        if (key && g_strcmp0 ((const char *) child->name, key) == 0)
                        {
                            key_valid = true;
                            break;
                        }
                    }

                    if (key_valid)
                    {
                        node = APTERYX_NODE (tree, value);
                        DEBUG ("%*s%s = %s\n", depth * 2, " ", name, APTERYX_NAME (node));
                    }
                    else
                        g_free (value);

                    g_free (key);
                }
                else
                {
                    node = APTERYX_NODE (tree, value);
                    DEBUG ("%*s%s = %s\n", depth * 2, " ", name, APTERYX_NAME (node));

                    if (_parms->in_is_edit)
                    {
                        bool is_key = false;

                        if (sch_parent && sch_is_list (sch_parent) &&
                            (schema == sch_node_child_first (sch_node_child_first (sch_parent))))
                            is_key = true;

                        if (!is_key)
                        {
                            _parms->out_merges =
                                g_list_append (_parms->out_merges, g_strdup_printf ("%s/%s", new_xpath, value));
                            DEBUG ("merge <%s>\n", new_xpath);
                        }
                    }
                }
            }
            else if (!_parms->in_is_edit)
                g_node_prepend_data (node, NULL);
        }
    }

    /* Carry out actions for this operation. Does nothing if not edit-config. */
    _perform_actions (_parms, depth, curr_op, new_op, new_xpath);

    for (child = xmlFirstElementChild (xml); child; child = xmlNextElementSibling (child))
    {
        if ((_parms->in_flags & SCH_F_STRIP_KEY) && key &&
            g_strcmp0 ((const char *) child->name, key) == 0)
        {
            /* The only child is the key with value */
            if (xmlChildElementCount (xml) == 1)
            {
                if (xml_node_has_content (child))
                {
                    /* Want all parameters for one entry in list. */
                    GNode *_node = APTERYX_NODE (node, g_strdup ("*"));
                    DEBUG ("%*s%s\n", (depth + 1) * 2, " ", "*");
                    if (!_parms->in_is_edit)
                        g_node_prepend_data (_node, NULL);
                }
                else
                {
                    /* Want one field in list element for one or more entries */
                    APTERYX_NODE (node, g_strdup ((const char *) child->name));
                    DEBUG ("%*s%s\n", (depth + 1) * 2, " ", child->name);
                }
                break;
            }
            /* Multiple children - make sure key appears */
            else if (xmlChildElementCount (xml) > 1 && !sch_is_proxy (schema))
            {
                GNode *_node = APTERYX_NODE (node, g_strdup ((const char *) child->name));
                DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
                if (!_parms->in_is_edit)
                    g_node_prepend_data (_node, NULL);
            }
            ret_tree = true;
        }
        else
        {
            GNode *cn = _sch_xml_to_gnode (_parms, schema, ns, new_xpath, new_op, NULL, child, depth + 1, rschema, edit_op);
            if (_parms->out_error.tag)
            {
                apteryx_free_tree (tree);
                tree = NULL;
                DEBUG ("recursive call failed: depth=%d\n", depth);
                goto exit;
            }
            if (cn)
            {
                if (node)
                    g_node_append (node, cn);
                else
                    tree = cn;
                ret_tree = true;
            }
        }
    }

    /* If no children added, no point in returning anything. */
    if (!ret_tree && _parms->in_is_edit)
    {
        apteryx_free_tree (tree);
        tree = NULL;
        goto exit;
    }

    /* Get everything from here down if a trunk of a subtree */
    if (!xmlFirstElementChild (xml) && sch_node_child_first (schema) &&
        g_strcmp0 (APTERYX_NAME (node), "*") != 0)
    {
        node = APTERYX_NODE (node, g_strdup ("*"));
        DEBUG ("%*s%s\n", (depth + 1) * 2, " ", "*");
    }

    if (!_parms->in_is_edit && !key_valid && node && node->data && !node->children)
        g_node_prepend_data (node, NULL);

exit:
    free (name);
    free (key);
    if (!tree)
    {
        DEBUG ("returning NULL: xpath=%s\n", new_xpath);
    }
    g_free (new_xpath);
    return tree;
}

static _sch_xml_to_gnode_parms *
sch_parms_init (sch_instance * instance, int flags, char * def_op, bool is_edit)
{
    _sch_xml_to_gnode_parms *_parms = g_malloc (sizeof (*_parms));
    _parms->in_instance = instance;
    _parms->in_flags = flags;
    _parms->in_def_op = def_op;
    _parms->in_is_edit = is_edit;
    _parms->out_tree = NULL;
    _parms->out_error = NC_ERROR_PARMS_INIT;
    _parms->out_deletes = NULL;
    _parms->out_removes = NULL;
    _parms->out_creates = NULL;
    _parms->out_replaces = NULL;
    _parms->out_merges = NULL;
    _parms->conditions = NULL;
    return _parms;
}

sch_xml_to_gnode_parms
sch_xml_to_gnode (sch_instance * instance, sch_node * schema, xmlNode * xml, int flags,
                  char * def_op, bool is_edit, sch_node **rschema, char ** edit_op)
{
    _sch_xml_to_gnode_parms *_parms = sch_parms_init(instance, flags, def_op, is_edit);

    if (xml)
        _parms->out_tree = _sch_xml_to_gnode (_parms, schema, NULL, "", def_op, NULL, xml, 0,
                                              rschema, edit_op);
    else
    {
        _parms->out_error.tag = NC_ERR_TAG_INVALID_VAL;
        _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
    }
    return (sch_xml_to_gnode_parms) _parms;
}

GNode *
sch_parm_tree (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;
    GNode *ret;

    if (!_parms)
    {
        return NULL;
    }
    ret = _parms->out_tree;
    _parms->out_tree = NULL;
    return ret;
}

nc_error_parms
sch_parm_error (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;
    return _parms->out_error;
}

GList *
sch_parm_deletes (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return NULL;
    }
    return _parms->out_deletes;
}

GList *
sch_parm_removes (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return NULL;
    }
    return _parms->out_removes;
}

GList *
sch_parm_creates (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return NULL;
    }
    return _parms->out_creates;
}

GList *
sch_parm_replaces (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return NULL;
    }
    return _parms->out_replaces;
}

GList *
sch_parm_merges (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return NULL;
    }
    return _parms->out_merges;
}

GList *
sch_parm_conditions (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return NULL;
    }
    return _parms->conditions;
}

bool
sch_parm_need_tree_set (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (!_parms)
    {
        return false;
    }
    return _parms->out_replaces || _parms->out_merges ||
           _parms->out_creates ? true : false;
}

void
sch_parm_free (sch_xml_to_gnode_parms parms)
{
    _sch_xml_to_gnode_parms *_parms = parms;

    if (_parms)
    {
        g_list_free_full (_parms->out_deletes, g_free);
        g_list_free_full (_parms->out_removes, g_free);
        g_list_free_full (_parms->out_creates, g_free);
        g_list_free_full (_parms->out_replaces, g_free);
        g_list_free_full (_parms->out_merges, g_free);
        g_list_free_full (_parms->conditions, g_free);
        _parms->out_error.tag = 0;
        _parms->out_error.type = 0;
        g_string_free (_parms->out_error.msg, TRUE);
        g_hash_table_destroy (_parms->out_error.info);
        g_free (_parms);
    }
}

static char *
sch_xpath_update_path (char *path, const char *prefix)
{
    char *new_path = NULL;
    char *colon = strchr (path, ':');
    if (!colon && prefix)
    {
        new_path = g_strdup_printf ("%s:%s", prefix, path);
    }
    else if (colon)
    {
        /* Check for XPATH keyword operators */
        if (strlen (colon) > 1 && *(colon + 1) == ':')
            return NULL;
        new_path = g_strdup_printf ("%s:%s",  prefix, colon + 1);
    }
    return new_path;
}

static void
sch_xpath_change_ns (sch_instance * instance, sch_node * schema, sch_ns *ns, xmlNode * xml,
                     int depth, xmlXPathContext *xpath_ctx, gchar **path_split, int count)
{
    char *name = (char *) xml->name;
    const char *href;
    const char *prefix;
    bool slash_slash = false;
    char *new_xpath = NULL;

    sch_ns *nns = sch_lookup_ns (instance, schema, (const char *) xml->ns->href, 0, true);

    if (depth < count && strlen (path_split[depth]) == 0 && strlen (path_split[depth + 1]) == 0)
        slash_slash = true;

    if (nns && !slash_slash)
    {
        href = sch_ns_href (instance, nns);
        prefix = sch_ns_prefix (instance, nns);
        if (!prefix)
            prefix = name;

        xmlXPathRegisterNs (xpath_ctx,  BAD_CAST prefix, BAD_CAST href);
        new_xpath = sch_xpath_update_path (path_split[depth + 1], prefix);
        if (new_xpath)
        {
            g_free (path_split[depth + 1]);
            path_split[depth + 1] = new_xpath;
        }
        ns = nns;
    }
}

static bool
sch_xpath_process_relatives (gchar **path_split, int *count)
{
    int i;
    int k;

    for (i = 0; i < *count; i++)
    {
        if (strlen (path_split[i]) == 2 && g_strcmp0 (path_split[i], "..") == 0)
        {
            if (i == 0 || strlen (path_split[i - 1]) == 0)
                return false;

            /* move up all following entries down two slots */
            g_free (path_split[i - 1]);
            path_split[i - 1] = NULL;
            g_free (path_split[i]);
            path_split[i] = NULL;
            for (k = i; k < *count - 1; k++)
            {
                path_split[k - 1] = path_split[k + 1];
            }
            path_split[k - 1] = NULL;
            path_split[k] = NULL;
            *count = *count - 2;
            i -= 2;
        }
        if (strlen (path_split[i]) == 1 && g_strcmp0 (path_split[i], ".") == 0)
        {
            g_free (path_split[i]);
            path_split[i] = NULL;
            for (k = i; k < *count - 1; k++)
            {
                path_split[k] = path_split[k + 1];
            }
            path_split[k] = NULL;
            *count = *count - 1;
            i -= 1;
        }
    }

    return true;
}

static bool
sch_xpath_is_simple (const char *path, xpath_type *x_type)
{
    if (path[0] == '/')
    {
        path++;
        if (path[0] == '/')
        {
            *x_type = XPATH_EVALUATE;
            return false;
        }
    }

    if (strncmp (path, "node(", 5) == 0)
    {
        *x_type = XPATH_EVALUATE;
        return false;
    }
    return true;
}

static GNode *
_sch_xpath_to_gnode (sch_instance * instance, sch_node ** rschema, sch_node ** vschema, xmlNs *ns,
                     const char *path, int flags, int depth, xpath_type *x_type)
{
    sch_node *schema = rschema && *rschema ? *rschema : sch_get_root_schema (instance);
    const char *next = NULL;
    GNode *node = NULL;
    GNode *rnode = NULL;
    GNode *child = NULL;
    char *query = NULL;
    char *pred = NULL;
    char *equals = NULL;
    char *new_path = NULL;
    char *colon;
    char *name = NULL;
    sch_node *last_good_schema = NULL;
    bool is_proxy = false;


    if (path && path[0] == '/')
    {
        path++;

        /* Parse path element */
        query = strchr (path, '?');
        next = strchr (path, '/');
        if (query && (!next || query < next))
            name = g_strndup (path, query - path);
        else if (next)
            name = g_strndup (path, next - path);
        else
            name = g_strdup (path);
        colon = strchr (name, ':');
        if (colon)
        {
            colon[0] = '\0';
            xmlNs *nns = sch_lookup_ns (instance, schema, name, flags, false);
            if (!nns)
            {
                /* No namespace found assume the node is supposed to have a colon in it */
                colon[0] = ':';
            }
            else
            {
                /* We found a namespace. Remove the prefix */
                char *_name = name;
                name = g_strdup (colon + 1);
                free (_name);
                ns = nns;
            }
        }

        if (query && next && query < next)
            next = NULL;

        pred = strchr (name, '[');
        if (pred)
        {
            char *temp = g_strndup (name, pred - name);
            pred = g_strdup (pred);
            free (name);
            name = temp;

            /* Numeric predicates to a record offset must be evaluated */
            if (isdigit (pred[1]))
                *x_type = XPATH_EVALUATE;
        }

        if (schema && vschema && *vschema == NULL && sch_is_list (schema))
        {
            /* Check for a schema list that has a parent that has skipped down
             * to the next schema level down without a list item selector */
            sch_node *parent = sch_node_parent (schema);
            if (parent)
            {
                GList *path_list = NULL;
                char *__next = g_strdup_printf ("/%s", name);
                bool found = sch_node_find_name (instance, ns, parent, __next, flags, &path_list);
                g_list_free_full (path_list, g_free);
                g_free (__next);

                if (found)
                {
                    *vschema = parent;
                    *x_type = XPATH_EVALUATE;
                    goto exit;
                }
            }
        }

        /* Find schema node */
        if (schema && sch_is_proxy (schema))
        {
            /* The schema containing the proxy node can have children */
            sch_node *child = sch_ns_node_child (ns, schema, name);
            if (!child)
            {
                is_proxy = sch_is_proxy (schema);
            }
        }

        if (!schema || is_proxy)
        {
            schema = sch_get_root_schema (instance);
            /* Detect change in namespace with the new schema */
            colon = strchr (name, ':');
            if (colon)
            {
                colon[0] = '\0';
                xmlNs *nns = sch_lookup_ns (instance, schema, name, flags, false);
                if (!nns)
                {
                    /* No namespace found assume the node is supposed to have a colon in it */
                    colon[0] = ':';
                }
                else
                {
                    /* We found a namespace. Remove the prefix */
                    char *_name = name;
                    name = g_strdup (colon + 1);
                    free (_name);
                    ns = nns;
                }
            }
        }

        last_good_schema = schema;
        schema = sch_ns_node_child (ns, schema, name);
        if (schema == NULL && g_strcmp0 (name, "*") == 0)
        {
            GList *path_list = NULL;
            bool found = sch_node_find_name (instance, ns, last_good_schema, next, flags, &path_list);

            if (found)
            {
                GList *list;
                int len = 0;
                bool first = true;
                for (list = g_list_first (path_list); list; list = g_list_next (list))
                {
                    len += strlen ((char *) list->data);
                }

                if (len)
                {
                    /* Note - the 64 bytes added to the length is to allow for extra slashes being added to the path */
                    len += strlen (path) +  64;
                    new_path = g_malloc0 (len);
                    len = 0;
                    /* Ammend the path with the new information. Note we drop the last list
                     * item as it contains a duplicate star slash already in the path */
                    for (list = g_list_first (path_list); list; list = g_list_next (list))
                    {
                        if (first)
                        {
                            g_free (name);
                            name = (char *) list->data;
                            first = false;
                        }
                        else
                        {
                            if (list->next)
                                len += sprintf (new_path + len, "/%s", (char *) list->data);
                            g_free (list->data);
                        }
                    }
                    sprintf (new_path + len, "/%s", path);
                    next = new_path;
                }
                g_list_free (path_list);
                if (new_path)
                    schema = sch_ns_node_child (ns, last_good_schema, name);
            }
        }

        if (schema == NULL)
        {
            *x_type = XPATH_ERROR;
            DEBUG ("No schema match for %s%s%s\n", ns ? (char *) ns->prefix : "",
                   ns ? ":" : "", name);
            goto exit;
        }

        /* Create node */
        if (depth == 0 || is_proxy)
        {
            if (ns && ns->prefix && !sch_ns_native (instance, ns))
            {
                if (is_proxy)
                    rnode = APTERYX_NODE (NULL, g_strdup_printf ("%s:%s", ns->prefix, name));
                else
                    rnode = APTERYX_NODE (NULL, g_strdup_printf ("/%s:%s", ns->prefix, name));
            }
            else
            {
                if (is_proxy)
                    rnode = APTERYX_NODE (NULL, g_strdup (name));
                else
                    rnode = APTERYX_NODE (NULL, g_strdup_printf ("/%s", name));
            }
        }
        else
        {
            rnode = APTERYX_NODE (NULL, name);
            name = NULL;
        }
        DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (rnode));

        /* XPATH predicates */
        if (pred && sch_is_list (schema))
        {
            char key[128 + 1];
            char value[128 + 1];
            schema = sch_node_child_first (schema);
            if (sscanf (pred, "[%128[^=]='%128[^']']", key, value) == 2 ||
                sscanf (pred, "[%128[^=]=\"%128[^\"]\"]", key, value) == 2) {
                // TODO make sure this key is the list key
                child = APTERYX_NODE (NULL, g_strdup (value));
                g_node_prepend (rnode, child);
                depth++;
                DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (child));
                if (next)
                {
                    if (!sch_xpath_is_simple (next, x_type))
                        next = NULL;
                }

                if (next)
                {
                    if (!sch_is_proxy (schema))
                    {
                        APTERYX_NODE (child, g_strdup (key));
                    }
                    depth++;
                    DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (child));
                }
            }
            g_free (pred);
        }
        else if (equals && sch_is_list (schema))
        {
            child = APTERYX_NODE (NULL, g_strdup (equals));
            g_node_prepend (rnode, child);
            depth++;
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (child));
            g_free (equals);
            schema = sch_node_child_first (schema);
        }

        if (next && !sch_xpath_is_simple (next, x_type))
            next = NULL;

        if (next)
        {
            node = _sch_xpath_to_gnode (instance, &schema, vschema, ns, next, flags, depth + 1, x_type);
            if (!node)
            {
                if (*x_type == XPATH_EVALUATE)
                    goto exit;

                if (!vschema || !*vschema)
                {
                    free ((void *)rnode->data);
                    g_node_destroy (rnode);
                    rnode = NULL;
                }
                goto exit;
            }
            g_node_prepend (child ? : rnode, node);
        }
    }

exit:
    if (rschema)
        *rschema = schema;
    free (name);
    g_free (new_path);
    return rnode;
}

GNode *
sch_xpath_to_gnode (sch_instance * instance, sch_node * schema, const char *path, int flags, sch_node ** rschema, xpath_type *x_type, char *schema_path)
{
    GNode *node = NULL;
    char *ptr;
    int len;
    char *_path = NULL;
    char *sch_path = NULL;
    sch_node *vschema = NULL;
    gchar **path_split;
    int count;

    if (path[0] != '/')
    {
        *x_type = XPATH_ERROR;
        return NULL;
    }
    len = strlen (path);
    if (len == 1)
    {
        sch_path = g_strdup (path);
    }

    /* Check for // syntax */
    if (path[1] == '/' || path[1] == '*')
    {
        if (schema_path)
        {
            *x_type = XPATH_EVALUATE;
        }
        else
        {
            /* Trying to do a // query but we have no namespace. This will not work */
            *x_type = XPATH_ERROR;
            return NULL;
        }
    }

    ptr = strchr (path + 1, '/');
    if (ptr == path + 1 && schema_path && strstr (path, schema_path) != path)
        sch_path = g_strdup_printf ("/%s/%s", schema_path, ptr);
    else
        sch_path = g_strdup (path);

    path_split = g_strsplit (sch_path, "/", 0);
    count = g_strv_length (path_split);
    if (count)
    {
        if (sch_xpath_process_relatives (path_split, &count))
        {
            _path = g_strjoinv ("/", path_split);
            node = _sch_xpath_to_gnode (instance, rschema, &vschema, NULL, _path, flags, 0, x_type);
        }
        else
        {
            *x_type = XPATH_ERROR;
        }
    }
    else
    {
        *x_type = XPATH_ERROR;
    }

    g_strfreev (path_split);
    g_free (_path);
    g_free (sch_path);

    return node;
}

static void
_sch_xpath_set_ns_path (sch_instance * instance, sch_node * schema, sch_ns *ns, xmlNode * xml,
                        int depth, xmlXPathContext *xpath_ctx, gchar **path_split, int count)
{
    char *name = (char *) xml->name;
    xmlNode *child;
    bool is_proxy = false;

    if (depth > count)
        return;

    /* Detect change in namespace */
    if (xml->ns && xml->ns->href)
        sch_xpath_change_ns (instance, schema, ns, xml, depth, xpath_ctx, path_split, count);

    /* Find schema node */
    if (schema && sch_is_proxy (schema))
    {
        /* The schema containing the proxy node can have children */
        sch_node *child = sch_ns_node_child (ns, schema, name);
        if (!child)
            is_proxy = sch_is_proxy (schema);
    }

    if (!schema || is_proxy)
    {
        schema = sch_get_root_schema (instance);
        /* Detect change in namespace with the new schema */
        schema = sch_ns_node_child (ns, schema, name);
        if (schema && is_proxy)
        {
            sch_xpath_change_ns (instance, schema, ns, xml, depth, xpath_ctx, path_split, count);
        }
    }
    else
        schema = sch_ns_node_child (ns, schema, name);

    if (schema == NULL)
        return;

    if (sch_is_leaf_list (schema) || sch_is_list (schema))
        schema = sch_node_child_first (schema);

    for (child = xmlFirstElementChild (xml); child; child = xmlNextElementSibling (child))
    {
        _sch_xpath_set_ns_path (instance, schema, ns, child, depth + 1, xpath_ctx, path_split, count);
    }
}

char *
sch_xpath_set_ns_path (sch_instance * instance, sch_node * schema, xmlNode * xml, xmlXPathContext *xpath_ctx, char *path)
{
    gchar **path_split;
    char *xpath;
    char *colon;
    char *curr_prefix = NULL;
    int count;
    int i;

    path_split = g_strsplit (path, "/", 0);
    count = g_strv_length (path_split);
    if (count)
    {
        /* remove any existing prefixes on path members */
        for (i = 0; i < count; i++)
        {
            colon = strchr (path_split[i], ':');
            if (colon && strlen (colon) > 1)
            {
                if (*(colon + 1) == ':')
                    continue;
                if (g_strcmp0 (curr_prefix, colon + 1))
                {
                    curr_prefix = colon + 1;
                }
                else
                {
                    char *tmp = g_strdup (colon + 1);
                    g_free (path_split[i]);
                    path_split[i] = tmp;
                }
            }
        }
        _sch_xpath_set_ns_path (instance, schema, NULL, xml, 0, xpath_ctx, path_split, count);
    }
    xpath = g_strjoinv ("/", path_split);
    g_strfreev (path_split);
    return xpath;
}
