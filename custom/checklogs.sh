#!/bin/sh

#set -x

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART

usage() {
   echo "Usage: $0 -u <user> -p <password> { -n <run name> | -d <discover run id> }"
   echo "   User and password are required if using run name"
}

while getopts ":u:p:n:d:" o; do
    case "${o}" in
        u)
            u=${OPTARG}
            ;;
        p)
            p=${OPTARG}
            ;;
        n)
            n=${OPTARG}
            ;;
        d)
            d=${OPTARG}
            ;;
        *)
            usage
            exit 1
            ;;
    esac
done

# user and password required
if [ -n "${n}" ] && ([ -z "${u}" ] || [ -z "${p}" ]); then
    usage
    exit 2
fi

# run name or discover run id
if [ -z "${n}" ] && [ -z "${d}" ]; then
    usage
    exit 2
fi

if [ -z "${d}" ]; then
    discoverRunId=`$COLLATION_HOME/sdk/bin/api.sh -u $u -p $p find -d 1 "SELECT discoverRunId FROM DiscoveryRun WHERE runName == '$n'" | awk -F'[<>]' '/discoverRunId/ {print $3}'`
else
    discoverRunId="${d}"
fi

logdir=$COLLATION_HOME/log/sensors/$discoverRunId

for ip in `grep 'Ping failed for IP address .* on all ports' $logdir/PingSensor-* 2> /dev/null | awk '{print $14}'`
do
    echo "Ping failed for $ip"
done

for ip in `grep 'INFO sensor\.PortScanSensor .* found nothing' $logdir/PortSensor* 2> /dev/null | awk '{print $5}' | awk -F- '{print $2}'`
do
    echo "Port sensor found nothing $ip"
done

for ip in `grep -l 'CTJTP1160E The application cannot establish the following SSH session' $logdir/SessionSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "SSH session error for $ip"
done

# This failure is seen when TaddmTool.exe fails to run because the .NET version installed on the gateway is not at the recommended level (as of June 2014 it is .NET 3.5)
for ip in `grep -l 'CTJTP1135E The following text is the exit status: -2146232576' $logdir/SessionSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo ".NET version failure for $ip"
done

for ip in `grep -l 'CTJTP1163E The following WMI session and SSH sessions cannot be established' $logdir/SessionSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "WMI error for $ip"
done

for ip in `grep -l 'CTJTP1161E The application cannot establish the following WMI session' $logdir/SessionSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "WMI error for $ip"
done

for ip in `grep -l 'CTJTD0809W Sensor cannot discover virtual memory configuration' $logdir/AixComputerSystemSensor-* 2> /dev/null | awk -F- '{print $2}' | rev | cut -c 5- | rev`
do
    echo "svmon failure for $ip"
done

for ip in `grep -l 'DISCOVER_SENSOR_CLEANUP' $logdir/WindowsComputerSystemSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "WindowsComputerSystemSensor timeout for $ip"
done

for ip in `grep -l 'DISCOVER_SENSOR_CLEANUP' $logdir/GenericServerSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "GenericServerSensor timeout for $ip"
done

for ip in `grep -l 'CTJTD0312E No Listening Processes Found' $logdir/GenericServerSensor* 2> /dev/null | awk -F- '{print $2}' | rev | cut -c 5- | rev`
do
    echo "lsof/netstat failure for $ip"
done

for ip in `grep -l 'CTJTD0317E' $logdir/GenericServerSensor* 2> /dev/null | awk -F- '{print $2}' | rev | cut -c 5- | rev`
do
    echo "GenericServerSensor Windows CreateProcess failed for $ip"
done

for ip in `grep -l 'WARN processors.LspartitionProcessor - CTJTD0829E Error executing command:lspartition -dlpar' $logdir/HmcSensor-* 2> /dev/null | awk -F- '{print $2}' | rev | cut -c 5- | rev`
do
    echo "lspartition failure in $ip"
done

for ip in `grep -l 'CTJTP0317E' $logdir/IISServerSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "IIS script copy to target failed for $ip"
done

for ip in `grep -l 'ERROR.*The RPC server is unavailable' $logdir/IISServerSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "IIS script execution failed due to network connection for $ip"
done

for ip in `grep -l 'CTJTP0317E' $logdir/IISServerSensor-* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "IIS script execution output on target is empty for $ip"
done

for ip in `grep -l 'CTJTD0074E' $logdir/ApacheServerSensor* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "Apache sensor failed for $ip"
done

for ip in `grep -l 'CTJTD0628W' $logdir/SqlServerSensor* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "MS SQL sensor could not establish db connections for $ip"
done

for ip in `grep -l 'CTJTD0490E' $logdir/OracleAppOpmnSensor* 2> /dev/null | awk -F- '{print $2}' | awk -F"(" '{print $2}' | rev | cut -c 3- | rev`
do
    echo "OracleAppOpmnSensor cannot determine home directory for $ip"
done

for ip in `grep -l 'CTJTP3209E' $logdir/WebSphereScriptSensor* 2> /dev/null | awk -F- '{print $2}'`
do
    echo "WebSphereScriptSensor failed for $ip"
done
