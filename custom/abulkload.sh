#!/bin/sh
# Filename: abulkload.sh

BINDIR=`dirname $0`/../bin
COMMONPART="$BINDIR/common.sh"
. $COMMONPART
cd $COLLATION_HOME/custom

# Delete content in the archive dir after this many days
# Set it to 0 to never delete
ARCHIVEDELETEAFTER=0

echo "Auto bulkload started on `date`." | tee -a $COLLATION_HOME/log/abulkload.log

# move old results files into an archive directory
mkdir -p $COLLATION_HOME/bulk/archive/results 2> /dev/null
mv $COLLATION_HOME/bulk/results/*.results $COLLATION_HOME/bulk/archive/results 2> /dev/null

# move old books to archive directory
mkdir -p $COLLATION_HOME/bulk/archive/books 2> /dev/null
discolib=`awk -F= '/^abulkload.discolib/ {print $2}' $COLLATION_HOME/custom/abulkload.properties`
echo "Discovery library path is $discolib." | tee -a $COLLATION_HOME/log/abulkload.log
for book in `cd $discolib; ls *.xml 2> /dev/null`
do
    processed=`grep $book $COLLATION_HOME/bulk/processedfiles.list | wc -l`
    if [ "$processed" -gt "0" ]
    then
        mv $discolib/$book $COLLATION_HOME/bulk/archive/books
        echo "$book previously processed, moved to $COLLATION_HOME/bulk/archive/books" | tee -a $COLLATION_HOME/log/abulkload.log
    fi
done

# end script if no new books to load
if [ "`ls $discolib/*.xml 2> /dev/null | wc -l`" -lt "1" ]
then
    echo "No new books found in $discolib to load." | tee -a $COLLATION_HOME/log/abulkload.log
    exit 0
fi

# Check that server is running
c=0
cd $COLLATION_HOME/bin
echo "Checking server status." | tee -a $COLLATION_HOME/log/abulkload.log
tstatus=`./control status | awk -F": " '/TADDM/ {print $2}'`
while [ "$tstatus" != "Running" ]
do
    echo "Server status is '${tstatus}' and count is $c at `date`" | tee -a $COLLATION_HOME/log/abulkload.log
    if [ "$c" -lt "3" ]
    then
        echo "Sleeping 10 minutes" | tee -a $COLLATION_HOME/log/abulkload.log
        c=`expr $c + 1`
        sleep 600
    else
        echo "*** Auto bulkload did not start because server is not running." | tee -a $COLLATION_HOME/log/abulkload.log
        cd $COLLATION_HOME/custom
        exit 1
    fi
    tstatus=`./control status | awk -F": " '/TADDM/ {print $2}'`
done
echo "Server is running." | tee -a $COLLATION_HOME/log/abulkload.log

# sort the timestamps in the book names
suffixes=$(
for book in $(cd $discolib; ls *.xml);
do
    length=`expr length $book`
    position=`echo $book | grep -bo -E '\.20[0-9]{2}-' | awk -F: '{print $1}'`
    if [ "$position" != "" ]; 
    then
        back=`expr $length - $position`
        suffix=`echo $book | tail -c $back`
        echo $suffix
    fi
done | sort -u
)

# get flags from properties file
flags=`awk -F= '/^abulkload.flags/ {print $2}' $COLLATION_HOME/custom/abulkload.properties`

# iterate over books in timestamp order and bulkload each one
cd $COLLATION_HOME/bin
for suffix in $suffixes;
do
    for book in $(cd $discolib; ls *$suffix);
    do
        echo "`date` Loading $book" | tee -a $COLLATION_HOME/log/abulkload.log
        ./loadidml.sh $flags -f $discolib/$book | tee -a $COLLATION_HOME/log/abulkload.log
    done
done

# Load other files without timestamps
for book in $(cd $discolib; ls -1 *.xml | grep -v -E '\.20[0-9]{2}-');
do
    echo "`date` Loading $book" | tee -a $COLLATION_HOME/log/abulkload.log
    ./loadidml.sh $flags -f $discolib/$book | tee -a $COLLATION_HOME/log/abulkload.log
done    

# check results
if [ "$?" -eq "0" ]
then
    echo "Bulkload completed" | tee -a $COLLATION_HOME/log/abulkload.log
    # Check for FAILURE in results file
    cd $COLLATION_HOME/bulk/results
    for rfile in `ls`
    do
        failures=`grep "ObjectId .*: FAILURE classtype " $rfile | wc -l`
        if [[ "$failures" -gt "0" ]]
        then
            echo "*** FAILURE found in result file $rfile" | tee -a $COLLATION_HOME/log/abulkload.log
        else
            failures=`grep "Failure writing/deleting/updating the managed element objects to the database" $rfile | wc -l`
            if [[ "$failures" -gt "0" ]]
            then
                echo "*** FAILURE found in result file $rfile" | tee -a $COLLATION_HOME/log/abulkload.log
            fi
        fi
    done
else
    echo "Error occurred (exit code $?), check logs or results" | tee -a $COLLATION_HOME/log/abulkload.log
fi

# clean up the archive dir
if [ $ARCHIVEDELETEAFTER -ne 0 ]
then
   cd $COLLATION_HOME/bulk/archive
    find * -depth -type f -mtime +$ARCHIVEDELETEAFTER -delete
    cd - >/dev/null
fi

# return to base path
cd $COLLATION_HOME/custom

echo "Auto bulkload completed on `date`." | tee -a $COLLATION_HOME/log/abulkload.log