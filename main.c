/**
 * @file main.c
 * Daemon entry point
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
#include <sys/socket.h>
#include <sys/un.h>
#include <netinet/in.h>
#include <sys/stat.h>

gboolean apteryx_netconf_debug = FALSE;
gboolean apteryx_netconf_verbose = FALSE;
static gboolean background = FALSE;
static gchar *models_path = "./";
static gchar *supported = NULL;
static gchar *logging = NULL;
static gchar *unix_path = "/tmp/apteryx-netconf";
static gchar *cp_cmd = NULL;
static gchar *rm_cmd = NULL;
static GThread *g_thread = NULL;
GMainLoop *g_loop = NULL;
static int accept_fd = -1;
static GThreadPool *workers = NULL;

static gboolean
termination_handler (gpointer arg1)
{
    GMainLoop *loop = (GMainLoop *) arg1;
    g_main_loop_quit (loop);
    shutdown(accept_fd, SHUT_RD);
    close (accept_fd);
    netconf_close_open_sessions ();
    g_thread_pool_free (workers, true, true);
    return FALSE;
}

/* Thread for handling client connections */
static gpointer
netconf_accept_thread (gpointer data)
{
    const char *path = (const char *) data;
    struct sockaddr_un addr_un;

    memset (&addr_un, 0, sizeof (addr_un));
    addr_un.sun_family = AF_UNIX;
    strncpy (addr_un.sun_path, path, sizeof (addr_un.sun_path) - 1);

    accept_fd = socket (PF_UNIX, SOCK_STREAM, 0);
    if (accept_fd < 0)
        g_error ("Socket(%s) failed: %s\n", path, strerror (errno));
    if (bind (accept_fd, (struct sockaddr *) &addr_un, sizeof (addr_un)) < 0)
        g_error ("Socket(%s) error binding: %s\n", path, strerror (errno));
    if (listen (accept_fd, 255) < 0)
        g_error ("Socket(%s) listen failed: %s\n", path, strerror (errno));
    chmod (path, 0666);

    usleep (500000);
    VERBOSE ("NETCONF: Accepting client connections\n");
    workers = g_thread_pool_new ((GFunc) netconf_handle_session, NULL, -1, FALSE, NULL);
    while (g_main_loop_is_running (g_loop))
    {
        struct sockaddr addr;
        socklen_t len = sizeof (addr);
        int new_fd = accept (accept_fd, &addr, &len);
        if (new_fd >= 0)
        {
            VERBOSE ("NETCONF: New session\n");
            g_thread_pool_push (workers, GINT_TO_POINTER (new_fd), NULL);
        }
    }
    VERBOSE ("NETCONF: Finished accepting clients\n");
    return NULL;
}

static GOptionEntry entries[] = {
    {"debug", 'd', 0, G_OPTION_ARG_NONE, &apteryx_netconf_debug, "Debug", NULL},
    {"verbose", 'v', 0, G_OPTION_ARG_NONE, &apteryx_netconf_verbose, "Verbose", NULL},
    {"background", 'b', 0, G_OPTION_ARG_NONE, &background, "Background", NULL},
    {"models", 'm', 0, G_OPTION_ARG_STRING, &models_path,
     "Path to models(defaults to \"./\")", NULL},
    {"supported", 's', 0, G_OPTION_ARG_STRING, &supported,
     "Name of a file containing a list of supported models", NULL},
    {"logging", 'l', 0, G_OPTION_ARG_STRING, &logging,
     "Name of a file containing a list of events to log", NULL},
    {"unix", 'u', 0, G_OPTION_ARG_STRING, &unix_path,
     "Listen on unix socket (defaults to /tmp/apteryx-netconf.sock)", NULL},
    {"copy", 'c', 0, G_OPTION_ARG_STRING, &cp_cmd,
     "BASH command to run to copy running->startup", NULL},
    {"remove", 'r', 0, G_OPTION_ARG_STRING, &rm_cmd,
     "BASH command to run to remove startup config", NULL},
    {NULL}
};

int
main (int argc, char *argv[])
{
    GError *error = NULL;
    GOptionContext *context;

    /* Parse options */
    context = g_option_context_new ("- Netconf access to Apteryx");
    g_option_context_add_main_entries (context, entries, NULL);
    if (!g_option_context_parse (context, &argc, &argv, &error))
    {
        g_print ("%s", g_option_context_get_help (context, FALSE, NULL));
        g_error ("%s\n", error->message);
    }
    g_option_context_free (context);

    /* Daemonize */
    if (background && fork () != 0)
    {
        /* Parent */
        return 0;
    }

    /* Initialization */
    apteryx_init (apteryx_netconf_verbose);
    if (!netconf_init (models_path, supported, logging, cp_cmd, rm_cmd))
    {
        g_error ("Failed to load models from \"%s\"\n", models_path);
    }

    /* Listen Socket */
    g_thread = g_thread_new ("netconf-accept", netconf_accept_thread, (gpointer) unix_path);

    /* Main Loop */
    g_loop = g_main_loop_new (NULL, FALSE);
    g_unix_signal_add (SIGINT, termination_handler, g_loop);
    g_unix_signal_add (SIGTERM, termination_handler, g_loop);
    signal (SIGPIPE, SIG_IGN);
    g_main_loop_run (g_loop);

    g_thread_unref (g_thread);

    /* Cleanup Unix socket */
    unlink (unix_path);

    /* Shutdown */
    netconf_shutdown ();
    apteryx_shutdown ();

    return EXIT_SUCCESS;
}
