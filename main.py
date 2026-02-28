import ssl
import socket
import threading

# Konfiguracja - tu wpisujesz serwery Onetu
IMAP_ONET = ("imap.onet.pl", 993)
SMTP_ONET = ("smtp.onet.pl", 587)

# Funkcja obsługująca tunelowanie danych
def proxy_bridge(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data: break
            destination.sendall(data)
    except:
        pass
    finally:
        source.close()
        destination.close()
def start_proxy(local_port, remote_host, remote_port):
    # Tworzymy luźniejszy kontekst, by nie wywalało błędu na starcie
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.set_ciphers('DEFAULT@SECLEVEL=0') # Najniższy poziom zabezpieczeń dla Nokii
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    # Próbujemy włączyć TLS 1.0, ale nie blokujemy skryptu jeśli system się stawia
    try:
        context.minimum_version = ssl.TLSVersion.TLSv1
    except:
        pass 

    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bind_socket.bind(('0.0.0.0', local_port))
    bind_socket.listen(5)
    
    print(f"Mostek aktywny na porcie {local_port}")

    while True:
        try:
            client_sock, addr = bind_socket.accept()
            # Wrapujemy tylko jeśli Nokia faktycznie o to poprosi
            secure_client = context.wrap_socket(client_sock, server_side=True)
            
            remote_sock = socket.create_connection((remote_host, remote_port))
            secure_remote = ssl.create_default_context().wrap_socket(remote_sock, server_hostname=remote_host)
            
            threading.Thread(target=proxy_bridge, args=(secure_client, secure_remote)).start()
            threading.Thread(target=proxy_bridge, args=(secure_remote, secure_client)).start()
        except Exception as e:
            print(f"Błąd połączenia: {e}")
