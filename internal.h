/**
 * @file internal.h
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
#ifndef _INTERNAL_H_
#define _INTERNAL_H_
#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <glib.h>
#include <glib-unix.h>
#include <ctype.h>
#include <syslog.h>
#include <apteryx.h>
#include <libxml/tree.h>

/* Debug */
extern gboolean apteryx_netconf_debug;
extern gboolean apteryx_netconf_verbose;
#define DEBUG(fmt, args...) \
    if (apteryx_netconf_debug || apteryx_netconf_verbose) \
    { \
        syslog (LOG_DEBUG, fmt, ## args); \
        printf (fmt, ## args); \
    }
#define VERBOSE(fmt, args...) \
    if (apteryx_netconf_verbose) \
    { \
        syslog (LOG_DEBUG, fmt, ## args); \
        printf (fmt, ## args); \
    }
#define NOTICE(fmt, args...) \
    { \
        syslog (LOG_NOTICE, fmt, ## args); \
        printf (fmt, ## args); \
    }
#define ERROR(fmt, args...) \
    { \
        syslog (LOG_CRIT, fmt, ## args); \
        fprintf (stderr, fmt, ## args); \
    }

typedef enum
{
    LOG_NONE                    = 0,
    LOG_EDIT_CONFIG             = (1 << 0),  /* Log edit-config requests */
    LOG_GET                     = (1 << 1),  /* Log get requests */
    LOG_GET_CONFIG              = (1 << 2),  /* Log get-config requests */
    LOG_KILL_SESSION            = (1 << 3),  /* Log kill-session requests */
    LOG_LOCK                    = (1 << 4),  /* Log lock requests */
    LOG_UNLOCK                  = (1 << 5),  /* Log unlock requests */
} logging_flags;

/* Define session counters from the RFC 6022 /netconf-state/sessions group
 * An instance of these is also used for global counters
 */
typedef struct
{
    uint32_t in_rpcs;
    uint32_t in_bad_rpcs;
    uint32_t out_rpc_errors;
    uint32_t out_notifications;
} session_counters_t;

/* Define global counters from the RFC 6022 /netconf-state/statistics group */
typedef struct
{
    gchar *netconf_start_time;
    uint32_t in_bad_hellos;
    uint32_t in_sessions;
    uint32_t dropped_sessions;
    session_counters_t session_totals;
} global_statistics_t;

/* Main loop */
extern GMainLoop *g_loop;

/* Netconf routines */
void netconf_close_open_sessions (void);
gboolean netconf_init (const char *path, const char *supported, const char *logging,
                       const char *cp, const char *rm);
void *netconf_handle_session (int fd);
void netconf_shutdown (void);

/* Logging routines */
int netconf_logging_init (const char *path, const char *logging);
void netconf_logging_shutdown (void);
bool netconf_logging_test_flag (int flag);

typedef void * sch_xml_to_gnode_parms;

/*
 * Netconf error handling
 **/

/* Enumeration of <rpc-error> error-type information */
typedef enum _NC_RPC_ERROR_TYPE {
    NC_ERR_TYPE_UNKNOWN = 0,   /* unknown layer */
    NC_ERR_TYPE_TRANSPORT,     /* secure transport layer */
    NC_ERR_TYPE_RPC,           /* rpc layer */
    NC_ERR_TYPE_PROTOCOL,      /* protocol layer */
    NC_ERR_TYPE_APP            /* application layer */
} NC_ERR_TYPE;

/* Enumeration of <rpc-error> error-tag information */
typedef enum _NC_RPC_ERROR_TAG {
    NC_ERR_TAG_UNKNOWN = 0,         /* unknown error */
    NC_ERR_TAG_IN_USE,              /* in-use error */
    NC_ERR_TAG_INVALID_VAL,         /* invalid-value error */
    NC_ERR_TAG_TOO_BIG,             /* too-big error */
    NC_ERR_TAG_MISSING_ATTR,        /* missing-attribute error */
    NC_ERR_TAG_BAD_ATTR,            /* bad-attribute error */
    NC_ERR_TAG_UNKNOWN_ATTR,        /* unknown-attribute error */
    NC_ERR_TAG_MISSING_ELEM,        /* missing-element error */
    NC_ERR_TAG_BAD_ELEM,            /* bad-element error */
    NC_ERR_TAG_UNKNOWN_ELEM,        /* unknown-element error */
    NC_ERR_TAG_UNKNOWN_NS,          /* unknown-namespace error */
    NC_ERR_TAG_ACCESS_DENIED,       /* access-denied error */
    NC_ERR_TAG_LOCK_DENIED,         /* lock-denied error */
    NC_ERR_TAG_RESOURCE_DENIED,     /* resource-denied error */
    NC_ERR_TAG_DATA_EXISTS,         /* data-exists error */
    NC_ERR_TAG_DATA_MISSING,        /* data-missing error */
    NC_ERR_TAG_OPR_NOT_SUPPORTED,   /* operation-not-supported error */
    NC_ERR_TAG_OPR_FAILED,          /* operation-failed error */
    NC_ERR_TAG_MALFORMED_MSG        /* malformed-message error */
} NC_ERR_TAG;

typedef struct _nc_error_parms_s
{
    NC_ERR_TAG tag;
    NC_ERR_TYPE type;
    GHashTable *info;
    GString* msg;
} nc_error_parms;

#define NC_ERROR_PARMS_INIT                                     \
(nc_error_parms)                                                \
{                                                               \
    .tag  = NC_ERR_TAG_UNKNOWN,                                 \
    .type = NC_ERR_TYPE_UNKNOWN,                                \
    .info = g_hash_table_new_full (g_str_hash, g_str_equal,     \
                                   NULL, g_free),               \
    .msg  = g_string_new (NULL)                                 \
};

/* Schema */
typedef struct _sch_instance sch_instance;
typedef void sch_node;
xmlNode *sch_gnode_to_xml (sch_instance * instance, sch_node * schema, GNode * node, int flags);
sch_xml_to_gnode_parms sch_xml_to_gnode (sch_instance * instance, sch_node * schema,
                                         xmlNode * xml, int flags, char * def_op,
                                         bool is_edit, sch_node **rschema);
GNode *sch_parm_tree (sch_xml_to_gnode_parms parms);
nc_error_parms sch_parm_error (sch_xml_to_gnode_parms parms);
GList *sch_parm_deletes (sch_xml_to_gnode_parms parms);
GList *sch_parm_removes (sch_xml_to_gnode_parms parms);
GList *sch_parm_creates (sch_xml_to_gnode_parms parms);
GList *sch_parm_replaces (sch_xml_to_gnode_parms parms);
void sch_parm_free (sch_xml_to_gnode_parms parms);

#endif /* _INTERNAL_H_ */
