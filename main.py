import ssl
import socket
import threading
import os

# Konfiguracja serwerów Onetu
IMAP_ONET = ("imap.onet.pl", 993)
SMTP_ONET = ("smtp.onet.pl", 587)

def proxy_bridge(source, destination):
    try:
        while True:
            data = source.recv(4096)
            if not data:
                break
            destination.sendall(data)
    except:
        pass
    finally:
        try:
            source.close()
        except:
            pass
        try:
            destination.close()
        except:
            pass

def start_proxy(local_port, remote_host, remote_port):
    # Kluczowe ustawienia dla starej Nokii: SECLEVEL=0 i TLSv1
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.set_ciphers('DEFAULT@SECLEVEL=0')
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    
    try:
        context.minimum_version = ssl.TLSVersion.TLSv1
    except:
        pass

    bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    bind_socket.bind(('0.0.0.0', local_port))
    bind_socket.listen(10)
    
    print(f"Mostek aktywny na porcie {local_port} -> {remote_host}:{remote_port}")

    while True:
        try:
            client_sock, addr = bind_socket.accept()
            # "Ubieramy" połączenie w SSL, który zrozumie Nokia
            secure_client = context.wrap_socket(client_sock, server_side=True)
            
            # Łączymy się z Onetem nowoczesnym SSL/TLS
            remote_sock = socket.create_connection((remote_host, remote_port))
            # Jeśli to SMTP (port 587), używamy zwykłego połączenia, które potem przejdzie w STARTTLS
            # Jeśli to IMAP (port 993), używamy SSL od razu
            if remote_port == 993:
                secure_remote = ssl.create_default_context().wrap_socket(remote_sock, server_hostname=remote_host)
            else:
                secure_remote = remote_sock # Dla SMTP 587
            
            threading.Thread(target=proxy_bridge, args=(secure_client, secure_remote), daemon=True).start()
            threading.Thread(target=proxy_bridge, args=(secure_remote, secure_client), daemon=True).start()
        except Exception as e:
            print(f"Blad: {e}")

if __name__ == "__main__":
    # Render używa zmiennej PORT (zazwyczaj 10000)
    port = int(os.environ.get("PORT", 10000))
    
    # Domyślnie uruchamiamy mostek dla IMAP (poczta przychodząca)
    # Na darmowym Renderze możemy mieć jeden otwarty port zewnętrzny (443)
    start_proxy(port, IMAP_ONET[0], IMAP_ONET[1])
