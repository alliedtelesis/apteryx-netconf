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
#include <syslog.h>
#include <apteryx.h>

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
#define ERROR(fmt, args...) \
    { \
        syslog (LOG_CRIT, fmt, ## args); \
        fprintf (stderr, fmt, ## args); \
    }

/* Main loop */
extern GMainLoop *g_loop;

/* Netconf routines */
void netconf_close_open_sessions (void);
gboolean netconf_init (const char *path, const char *supported,
                       const char *cp, const char *rm);
void *netconf_handle_session (int fd);
void netconf_shutdown (void);

#endif /* _INTERNAL_H_ */
