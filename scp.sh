#!/usr/bin/expect

set timeout 60
set cmd [lindex $argv 0]
set password [lindex $argv 1]

puts "$cmd"
spawn $cmd
expect {
  "*assword*" {
    puts "send password"
    send "$password\r"
    exp_continue
  }
  "*yes/no*" {
    puts "send yes"
    send "yes\r"
    exp_continue
  }
  "*100%*" {
    puts "cmd end"
    exit 0
  }
  eof {
    puts "cmd end"
    exit 0
  }
}


