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
    # Tworzymy kontekst SSL, który akceptuje TLS 1.0 dla Nokii
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.set_ciphers('DEFAULT@SECLEVEL=1') # Obniżenie poziomu bezpieczeństwa dla Nokii
    context.minimum_version = ssl.TLSVersion.TLSv1 # Włączenie TLS 1.0
    
    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_socket.bind(('0.0.0.0', local_port))
    bind_socket.listen(5)
    
    print(f"Mostek aktywny na porcie {local_port} -> {remote_host}:{remote_port}")

    while True:
        client_sock, addr = bind_socket.accept()
        # "Ubieramy" połączenie z Nokią w stary SSL/TLS 1.0
        secure_client = context.wrap_socket(client_sock, server_side=True)
        
        # Łączymy się z Onetem nowoczesnym SSL/TLS 1.2+
        remote_sock = socket.create_connection((remote_host, remote_port))
        secure_remote = ssl.create_default_context().wrap_socket(remote_sock, server_hostname=remote_host)
        
        # Startujemy dwa wątki do przesyłania danych w obie strony
        threading.Thread(target=proxy_bridge, args=(secure_client, secure_remote)).start()
        threading.Thread(target=proxy_bridge, args=(secure_remote, secure_client)).start()

# Uruchomienie mostka dla IMAP (poczta przychodząca)
if __name__ == "__main__":
    # Render używa zmiennej środowiskowej PORT, zazwyczaj 10000
    import os
    port = int(os.environ.get("PORT", 10000))
    start_proxy(port, IMAP_ONET[0], IMAP_ONET[1])
