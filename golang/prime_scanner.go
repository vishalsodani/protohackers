package main

import (
	"bufio"
	"encoding/json"
	"fmt"
	"math"
	"net"
	"strings"
)

func IsPrime(num float64) bool {
	// Check if it has decimals, if yes it is not a prime
	inti, frac := math.Modf(num)
	if frac != 0 {
		return false
	}
	if num < 2 {
		return false
	}
	n := int64(num)

	sq_root := int(math.Sqrt(float64(inti)))
	for i := 2; i <= sq_root; i++ {
		if n%int64(i) == 0 {
			return false
		}
	}

	return true
}

func send_malformed_response(conn net.Conn) {
	var response string
	response = `{"error":"isPrime"}`
	resp := append([]byte(response), []byte("\n")...)
	_, werr := conn.Write(resp)
	if werr != nil {
		fmt.Println("write erro")
	}

}

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
	scanner := bufio.NewScanner(conn)
	scanner.Split(bufio.ScanLines)
	for scanner.Scan() {
		data := scanner.Text()

		type Request struct {
			Method    string
			Number    float64
			BigNumber bool
		}
		var req *Request = &Request{}
		data_w := data

		if !strings.Contains(data_w, "method") ||
			!strings.Contains(data_w, "number") {
			send_malformed_response(conn)
		}
		err := json.Unmarshal([]byte(data_w), req)

		if err != nil {
			//fmt.Println("error json")
			fmt.Println(data_w)
			fmt.Println(err)
			send_malformed_response(conn)
		}
		if req.Method != "isPrime" {
			send_malformed_response(conn)
		}
		//fmt.Printf("%+v", req)
		//fmt.Print("found end of line")
		data = ""
		if IsPrime(req.Number) && req.BigNumber == false {
			var response string
			response = `{"method":"isPrime","prime":true}`
			resp := append([]byte(response), []byte("\n")...)
			_, werr := conn.Write(resp)
			if werr != nil {
				fmt.Println(werr)
			}
		} else {
			var response string
			response = `{"method":"isPrime","prime":false}`
			resp := append([]byte(response), []byte("\n")...)
			_, werr := conn.Write(resp)
			if werr != nil {
				fmt.Println(werr)
			}

		}

	}

}
