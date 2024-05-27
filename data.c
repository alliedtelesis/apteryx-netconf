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
} _sch_xml_to_gnode_parms;

static xmlNode *
_sch_gnode_to_xml (sch_instance * instance, sch_node * schema, sch_ns *ns, xmlNode * parent,
                   GNode * node, int flags, int depth)
{
    sch_node *pschema = schema;
    xmlNode *data = NULL;
    char *colon = NULL;
    char *name;

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
    if (!schema)
        schema = sch_get_root_schema (instance);
    schema = sch_ns_node_child (ns, schema, name);
    if (schema == NULL)
    {
        ERROR ("No schema match for gnode %s%s%s\n",
               ns ? sch_ns_prefix (instance, ns) : "", ns ? ":" : "", name);
        free (name);
        return NULL;
    }
    if (!sch_is_readable (schema))
    {
        ERROR ("Ignoring non-readable node %s%s%s\n",
               ns ? sch_ns_prefix (instance, ns) : "", ns ? ":" : "", name);
        free (name);
        return NULL;
    }

    if (sch_is_leaf_list (schema))
    {
        apteryx_sort_children (node, g_strcmp0);
        for (GNode * child = node->children; child; child = child->next)
        {
            GNode *value_node = child->children;
            if (value_node)
            {
                char *leaf_name = APTERYX_NAME (value_node);
                data = xmlNewNode (NULL, BAD_CAST name);
                xmlNodeSetContent (data, (const xmlChar *) leaf_name);
                sch_ns *sns = sch_node_ns (schema);
                if (!pschema || !sch_ns_match (pschema, sns))
                {
                    const xmlChar *href = (const xmlChar *) sch_ns_href (instance, sns);
                    xmlNsPtr nns = xmlNewNs (data, href, NULL);
                    xmlSetNs (data, nns);
                }
                xmlAddChildList (parent, data);
                DEBUG ("%*s%s = %s\n", depth * 2, " ", APTERYX_NAME (node), leaf_name);
            }
        }
    }
    else if (sch_is_list (schema))
    {
        xmlNode *list_data = NULL;
        data = NULL;

        apteryx_sort_children (node, g_strcmp0);
        for (GNode * child = node->children; child; child = child->next)
        {
            gboolean has_child = false;

            DEBUG ("%*s%s[%s]\n", depth * 2, " ", APTERYX_NAME (node),
                   APTERYX_NAME (child));
            list_data = xmlNewNode (NULL, BAD_CAST name);
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
                xmlAddChildList (parent, list_data);
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
            data = xmlNewNode (NULL, BAD_CAST name);
            value = sch_translate_to (schema, value);
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
            g_hash_table_insert (_parms->out_error.info, "bad-attribute", g_strdup (attr));

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
            g_free (attr);
            _parms->out_error.tag = NC_ERR_TAG_UNKNOWN_ATTR;
            _parms->out_error.type = NC_ERR_TYPE_PROTOCOL;
            g_hash_table_insert (_parms->out_error.info, "bad-element", g_strdup ("operation"));
            g_hash_table_insert (_parms->out_error.info, "bad-attribute", g_strdup (attr));
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
                   char * curr_op, GNode * pparent, xmlNode * xml, int depth, sch_node **rschema)
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


    /* Detect change in namespace */
    if (xml->ns && xml->ns->href)
    {
         sch_ns *nns = sch_lookup_ns (instance, schema, (const char *) xml->ns->href, flags, true);
         if (nns)
            ns = nns;
    }

    /* Find schema node */
    if (!schema)
        schema = sch_get_root_schema (instance);
    schema = sch_ns_node_child (ns, schema, name);
    if (schema == NULL)
    {
        ERROR ("No schema match for xml node %s%s%s\n",
               ns ? sch_ns_prefix (instance, ns) : "", ns ? ":" : "", name);
        _parms->out_error.tag = NC_ERR_TAG_MALFORMED_MSG;
        _parms->out_error.type = NC_ERR_TYPE_RPC;
        return NULL;
    }
    if (rschema)
        *rschema = schema;

    /* Prepend non default namespaces to root nodes */
    if (depth == 0 && ns && sch_ns_prefix (instance, ns) && !sch_ns_native (instance, ns))
        name = g_strdup_printf ("%s:%s", sch_ns_prefix (instance, ns), (const char *) xml->name);
    else
        name = g_strdup ((char *) xml->name);

    /* Update xpath. */
    new_xpath = g_strdup_printf ("%s/%s", part_xpath, name);

    /* Check operation, error tag set on exit from routine. */
    if (!_operation_ok (_parms, xml, curr_op, &new_op))
    {
        ERROR ("Invalid operation\n");
        free (new_xpath);
        free (name);
        return NULL;
    }

    /* LIST */
    if (sch_is_leaf_list (schema))
    {
        char *old_xpath = new_xpath;
        char *key_value = NULL;

        DEBUG ("%*s%s%s\n", depth * 2, " ", depth ? "" : "/", name);
        tree = APTERYX_NODE (NULL, g_strdup (name));
        schema = sch_node_child_first (schema);

        if (xml_node_has_content (xml))
        {
            key_value = (char *) xmlNodeGetContent (xml);
            if (g_strcmp0 (new_op, "delete") == 0 || g_strcmp0 (new_op, "remove") == 0 ||
                g_strcmp0 (new_op, "none") == 0)
            {
                new_xpath = g_strdup_printf ("%s/%s", old_xpath, key_value);
            }
            else
            {
                new_xpath = g_strdup_printf ("%s/%s/%s", old_xpath, key_value, key_value);
                node = APTERYX_NODE (tree, g_strdup (key_value));
                node = APTERYX_NODE (node, g_strdup (key_value));
            }
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
        depth++;
        tree = node = APTERYX_NODE (NULL, g_strdup (name));
        attr = (char *) xmlGetProp (xml, BAD_CAST key);
        if (attr)
        {
            node = APTERYX_NODE (node, g_strdup (attr));
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
            if (!(_parms->in_flags & SCH_F_STRIP_KEY) || xmlFirstElementChild (xml))
            {
                GNode *_node = APTERYX_NODE (node, g_strdup (key));
                DEBUG ("%*s%s\n", (depth + 1) * 2, " ", key);
                if (!_parms->in_is_edit)
                    g_node_prepend_data (_node, NULL);
            }
            key_value = attr;
        }
        else if (xmlFirstElementChild (xml) &&
                 g_strcmp0 ((const char *) xmlFirstElementChild (xml)->name, key) == 0 &&
                 xml_node_has_content (xmlFirstElementChild (xml)))
        {
            node =
                APTERYX_NODE (node,
                              (char *) xmlNodeGetContent (xmlFirstElementChild (xml)));
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
            key_value = (char *) xmlNodeGetContent (xmlFirstElementChild (xml));
        }
        else
        {
            node = APTERYX_NODE (node, g_strdup ("*"));
            DEBUG ("%*s%s\n", depth * 2, " ", APTERYX_NAME (node));
            key_value = g_strdup ("*");
        }
        schema = sch_node_child_first (schema);
        if (rschema)
            *rschema = schema;

        new_xpath = g_strdup_printf ("%s/%s", old_xpath, key_value);
        g_free (old_xpath);
        g_free (key_value);
    }
    /* CONTAINER */
    else if (!sch_is_leaf (schema))
    {
        DEBUG ("%*s%s%s\n", depth * 2, " ", depth ? "" : "/", name);
        tree = node = APTERYX_NODE (NULL, g_strdup_printf ("%s%s", depth ? "" : "/", name));
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
            else if (xmlChildElementCount (xml) > 1)
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
            GNode *cn = _sch_xml_to_gnode (_parms, schema, ns, new_xpath, new_op, NULL, child, depth + 1, rschema);
            if (_parms->out_error.tag)
            {
                apteryx_free_tree (tree);
                tree = NULL;
                ERROR ("recursive call failed: depth=%d\n", depth);
                goto exit;
            }
            if (cn)
            {
                g_node_append (node, cn);
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
        ERROR ("returning NULL: xpath=%s\n", new_xpath);
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
    return _parms;
}

sch_xml_to_gnode_parms
sch_xml_to_gnode (sch_instance * instance, sch_node * schema, xmlNode * xml, int flags,
                  char * def_op, bool is_edit, sch_node **rschema)
{
    _sch_xml_to_gnode_parms *_parms = sch_parms_init(instance, flags, def_op, is_edit);

    _parms->out_tree = _sch_xml_to_gnode (_parms, schema, NULL, "", def_op, NULL, xml, 0,
                                          rschema);
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
        _parms->out_error.tag = 0;
        _parms->out_error.type = 0;
        g_string_free (_parms->out_error.msg, TRUE);
        g_hash_table_destroy (_parms->out_error.info);
        g_free (_parms);
    }
}
