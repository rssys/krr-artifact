#!/usr/bin/env python3

import socket
import json
import sys
import argparse

def send_qmp_command(socket_path, command, arguments=None):
    """
    Send a QMP command to QEMU via Unix socket
    
    Args:
        socket_path (str): Path to the Unix socket
        command (str): QMP command to send
        arguments (dict): Optional arguments for the command
    
    Returns:
        dict: Response from QEMU
    """
    # Create a Unix socket connection
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    
    try:
        # Connect to the socket
        sock.connect(socket_path)
        
        # Receive the initial greeting message
        greeting = json.loads(sock.recv(4096).decode('utf-8'))
        print("QMP greeting:", json.dumps(greeting, indent=2))
        
        # Send the capabilities negotiation
        sock.sendall(json.dumps({"execute": "qmp_capabilities"}).encode('utf-8'))
        capabilities_response = json.loads(sock.recv(4096).decode('utf-8'))
        print("Capabilities response:", json.dumps(capabilities_response, indent=2))
        
        # Prepare the command
        cmd = {"execute": command}
        if arguments:
            cmd["arguments"] = arguments
        
        # Send the command
        print(f"Sending command: {json.dumps(cmd, indent=2)}")
        sock.sendall(json.dumps(cmd).encode('utf-8'))
        
        # Receive the response
        response = json.loads(sock.recv(4096).decode('utf-8'))
        print("Response:", json.dumps(response, indent=2))
        
        return response
        
    except socket.error as e:
        print(f"Socket error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return None
    finally:
        sock.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Send a QMP command to QEMU")
    parser.add_argument("--socket", "-s", required=True, help="Path to QEMU QMP socket")
    parser.add_argument("--command", "-c", required=True, help="QMP command to execute")
    parser.add_argument("--args", "-a", help="JSON arguments for the command")
    
    args = parser.parse_args()
    
    # Parse arguments if provided
    command_args = None
    if args.args:
        try:
            command_args = json.loads(args.args)
        except json.JSONDecodeError:
            print("Error: Could not parse command arguments as JSON")
            sys.exit(1)
    
    response = send_qmp_command(args.socket, args.command, command_args)
    if not response:
        sys.exit(1)
