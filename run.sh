#!/bin/bash
ROOT=`pwd`
ACTION=$1

# Check required libraries and tools
if ! pkg-config --exists glib-2.0 libxml-2.0 cunit jansson; then
        echo "Please install glib-2.0, libxml-2.0, jansson and cunit"
        echo "(sudo apt-get install build-essential libglib2.0-dev libxml2-dev libcunit1-dev libjansson-dev)"
        exit 1
fi

# Build needed packages
BUILD=$ROOT/.build
mkdir -p $BUILD
cd $BUILD

# Generic cleanup
function quit {
        RC=$1
        # Stop sshd
        if [ -f /tmp/apteryx-netconf-sshd.pid ]; then
                sudo kill -9 `cat /tmp/apteryx-netconf-sshd.pid` &> /dev/null
                sudo rm -f /tmp/apteryx-netconf-sshd.pid
        fi
        # Stop apteryx-netconf
        killall apteryx-netconf &> /dev/null
        kill `pidof valgrind.bin` &> /dev/null
        sudo rm /tmp/apteryx-netconf &> /dev/null
        sudo userdel manager
        # Stop Apteryx
        killall -9 apteryxd &> /dev/null
        rm -f /tmp/apteryx
        if [ -f $BUILD/apteryx-netconf.log ]; then
                echo "=== Apteryx Netconf log ==="
                cat $BUILD/apteryx-netconf.log
        fi
        exit $RC
}

# Check Apteryx install
if [ ! -d apteryx ]; then
        echo "Downloading Apteryx"
        git clone --depth 1 https://github.com/alliedtelesis/apteryx.git
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi
if [ ! -f $BUILD/usr/lib/libapteryx.so ]; then
        echo "Building Apteryx"
        cd apteryx
        make install DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi

# Check Apteryx XML Schema library
if [ ! -d apteryx-xml ]; then
        echo "Downloading apteryx-xml"
        git clone --depth 1 https://github.com/alliedtelesis/apteryx-xml.git
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
fi
if [ ! -f $BUILD/usr/lib/libapteryx-schema.so ]; then
        echo "Building apteryx-xml"
        cd apteryx-xml
        rm -f $BUILD/usr/lib/libapteryx-xml.so
        rm -f $BUILD/usr/lib/libapteryx-schema.so
        make install DESTDIR=$BUILD APTERYX_PATH=$BUILD/apteryx
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi

# Check openssh
if [ ! -d openssh ]; then
        echo "Downloading openssh"
        git clone --depth 1 --branch V_8_8_P1 git://anongit.mindrot.org/openssh.git
        rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
fi
if [ ! -f $BUILD/usr/sbin/sshd ]; then
        echo "Building openssh"
        cd openssh
        autoreconf -fvi
        ./configure --prefix=/usr --with-privsep-path=$BUILD/empty --with-privsep-user=manager
        make install-nokeys DESTDIR=$BUILD
        rc=$?; if [[ $rc != 0 ]]; then exit $rc; fi
        cd $BUILD
fi
if [ ! -f $BUILD/ssh_host_rsa_key ]; then
    $BUILD/usr/bin/ssh-keygen -b 2048 -t rsa -f $BUILD/ssh_host_rsa_key -q -N ""
fi
mkdir -p $BUILD/empty
chmod 755 $BUILD/empty
sudo chown root:sys $BUILD/empty
echo -e "
HostKey $BUILD/ssh_host_rsa_key
HostKeyAlgorithms ssh-rsa,ssh-dss
Port 830
Subsystem netconf /usr/bin/socat STDIO UNIX:$BUILD/apteryx-netconf.sock
PidFile /tmp/apteryx-netconf-sshd.pid
" > $BUILD/sshd_config

if [ $ACTION == "setup" ]; then
        exit 0
fi

# Build
echo "Building apteryx-netconf"
if [ ! -f $BUILD/../Makefile ]; then
        export CFLAGS="-g -Wall -Werror -I$BUILD/usr/include -fprofile-arcs -ftest-coverage"
        export LDFLAGS=-L$BUILD/usr/lib
        export PKG_CONFIG_PATH=$BUILD/usr/lib/pkgconfig
        cd $BUILD/../
        ./autogen.sh
        ./configure \
                APTERYX_CFLAGS=-I$BUILD/usr/include APTERYX_LIBS=-lapteryx \
                APTERYX_XML_CFLAGS=-I$BUILD/usr/include APTERYX_XML_LIBS=-lapteryx-schema
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        cd $BUILD
fi
make -C $BUILD/../
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

# Check tests
echo Checking pytest coding style ...
flake8 --max-line-length=180 ../tests/*.py
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

# Start Apteryx
echo Starting apteryx ...
export LD_LIBRARY_PATH=$BUILD/usr/lib
rm -f /tmp/apteryx
$BUILD/usr/bin/apteryxd -b
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

# Start sshd
echo Starting sshd ...
sudo useradd -M -p $(perl -e 'print crypt($ARGV[0], "password")' 'friend') manager
sudo $BUILD/usr/sbin/sshd -f $BUILD/sshd_config
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi

# Parameters
if [ $ACTION == "test" ]; then
        rm $BUILD/apteryx-netconf.log
        PARAM="-b -v -l $BUILD/apteryx-netconf.log"
else
        PARAM="-v"
fi

# Start netconf
echo Starting apteryx-netconf ...
rm -f $BUILD/apteryx-netconf.sock
# TEST_WRAPPER="gdb -ex run --args"
# TEST_WRAPPER="valgrind --leak-check=full"
# TEST_WRAPPER="valgrind --tool=cachegrind"
G_SLICE=always-malloc LD_LIBRARY_PATH=$BUILD/usr/lib \
        $TEST_WRAPPER ../apteryx-netconf --models $BUILD/../models/ --unix $BUILD/apteryx-netconf.sock $PARAM
rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
sleep 2
cd $BUILD/../

if [ $ACTION == "test" ]; then
        echo Running tests ...
        python3 -m pytest -k test_get_xpath_node_ns_other
        rc=$?; if [[ $rc != 0 ]]; then quit $rc; fi
        echo Tests completed successfully
fi

# Gcov
mkdir -p .gcov
mv -f *.gcno .gcov/ 2>/dev/null || true
mv -f *.gcda .gcov/ 2>/dev/null || true
lcov -q --capture --directory . --output-file .gcov/coverage.info &> /dev/null
genhtml -q .gcov/coverage.info --output-directory .gcov/

# Done - cleanup
quit 0
