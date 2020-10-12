#!/usr/bin/expect

set timeout 60
set cmd [lindex $argv 0]
set source [lindex $argv 1]
set dest [lindex $argv 2]
set password [lindex $argv 3]

puts "command : $cmd $source $dest"
spawn $cmd $source $dest
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


