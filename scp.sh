#!/usr/bin/expect

set timeout 60
set cmd [lindex $argv 0]
set password [lindex $argv 1]

echo "$cmd"
spawn $cmd
expect {
  "*assword*" {
    echo "send password"
    send "$password\r"
    exp_continue
  }
  "*yes/no*" {
    echo "send yes"
    send "yes\r"
    exp_continue
  }
  "*100%*" {
    echo "cmd end"
    exit 0
  }
  eof {
    echo "cmd end"
    exit 0
  }
}


