#!/bin/sh
 
# NOTE this script depends on public key trust to secondary and discovery servers
 
BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom
 
usage() {
   echo "Usage: $0 -s <local src file> -d <remote dir location>"
}
 
while getopts ":s:d:" o; do
    case "${o}" in
        s)
            s=${OPTARG}
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
 
# required
if [ -z "${s}" ] || [ -z "${d}" ]; then
    usage
    exit 2
fi
 
for server in `grep -v '^#' secondary-storage-servers.txt`
do
  echo "Copying to $server"
  scp -q $s $server:$d
done
 
for server in `grep -v '^#' discovery-servers.txt`
do
  echo "Copying to $server"
  scp -q $s $server:$d
done