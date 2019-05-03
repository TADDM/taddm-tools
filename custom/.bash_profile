# .bash_profile

# This is a helpful .bash_profile for TADDM servers

# Get the aliases and functions
if [ -f ~/.bashrc ]; then
    . ~/.bashrc
fi

# User specific environment and startup programs
COLLATION_HOME=/opt/IBM/taddm/dist

. $COLLATION_HOME/bin/common.sh

# include /opt/IBM/taddm/dist/nmap-5.21 at beginning if nmap installed
PATH=$PATH:/sbin:$HOME/bin:$COLLATION_HOME/bin:$COLLATION_HOME/sdk/bin:$JAVA_HOME/bin

export PATH
export COLLATION_HOME

# bash (won't work on ksh) go to last sensor log directory on discovery server
alias cdll="cd $COLLATION_HOME/log/sensors/\`ls -1 $COLLATION_HOME/log/sensors | tail -1\`"

set -o vi

cd $COLLATION_HOME
