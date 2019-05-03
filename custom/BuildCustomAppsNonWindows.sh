#!/bin/sh
 
# This script generates custom servers from the custom server definitions
# for NON-WINDOWS ASD discovered systems. This script is being used as a 
# workaround because ASD does not support custom servers at this time. Do
# NOT include Windows systems below, the normal Windows discovery will 
# create custom servers.
 
# run background topo group to generate unattached processes
#echo "Running background topology builder group and waiting for completion"
#../support/bin/runtopobuild.sh -g background -w
 
# The following runs the "RSA" custom server definitions against a few hosts
echo "Building RSA custom servers"
./capp.jy -H ibapppxx.ibm.com -t "RSA ClearTrust Authorization Server"
./capp.jy -H ibapppxx.ibm.com -t "RSA ClearTrust Authorization Dispatcher"
./capp.jy -H ibapppxy.ibm.com -t "RSA ClearTrust Authorization Server"
./capp.jy -H ibapppxy.ibm.com -t "RSA ClearTrust Authorization Dispatcher"
./capp.jy -H ibsibpab.ibm.com -t "RSA ClearTrust Entitlement Server"
 