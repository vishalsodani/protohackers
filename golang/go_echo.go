package main

import (
	"io"
	"net"
)

func main() {
	ln, err := net.Listen("tcp", ":5003")
	if err != nil {
		// handle error
	}
	for {
		conn, err := ln.Accept()
		if err != nil {
			// handle error
		}
		go handleConnection(conn)
	}
}

func handleConnection(conn net.Conn) {
	defer conn.Close()

	io.Copy(conn, conn)
}
