use std::{
    fs,
    io::{prelude::*, BufReader},
    net::{TcpListener, TcpStream},
    thread,
    time::Duration,
};

fn main() {
    let listener = TcpListener::bind("127.0.0.1:5003").unwrap();
    

    for stream in listener.incoming() {
        let mut stream = stream.unwrap();
        let mut buffer = Vec::new();

        stream.read_to_end(&mut buffer);
        stream.write(&buffer);
    }

    println!("Shutting down.");
}

