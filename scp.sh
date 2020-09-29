#!/usr/bin/expect

set timeout 60
set cmd [lindex $argv 0]
set param [lindex $argv 1]
set password [lindex $argv 2]

puts "command : $cmd"
spawn $cmd $param
expect {
  "*assword*" {
    send "$password\r"
    puts "send password"
    exp_continue
  }
  "*yes/no*" {
    send "yes\r"
    puts "send yes"
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


