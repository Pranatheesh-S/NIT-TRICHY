import os
import datetime
import sys
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography import x509
from cryptography.x509.oid import NameOID

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.config import SERVER_CERT, SERVER_KEY, PROXY_CERT, PROXY_KEY, CERTS_DIR
from rich.console import Console

console = Console()

def generate_self_signed_cert(cert_path, key_path, common_name):
    # Generate RSA Private Key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    
    # Generate Certificate
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"Interception System"),
        x509.NameAttribute(NameOID.COMMON_NAME, common_name),
    ])
    
    cert = x509.CertificateBuilder().subject_name(
        subject
    ).issuer_name(
        issuer
    ).public_key(
        private_key.public_key()
    ).serial_number(
        x509.random_serial_number()
    ).not_valid_before(
        datetime.datetime.utcnow()
    ).not_valid_after(
        # Valid for 1 year
        datetime.datetime.utcnow() + datetime.timedelta(days=365)
    ).add_extension(
        x509.SubjectAlternativeName([x509.DNSName(u"localhost")]),
        critical=False,
    ).sign(private_key, hashes.SHA256())
    
    # Write Private Key
    with open(key_path, "wb") as f:
        f.write(private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ))
        
    # Write Certificate
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        
    console.print(f"[green]Generated certificate and key for {common_name}[/green]")

def main():
    os.makedirs(CERTS_DIR, exist_ok=True)
    console.print("[bold blue]Generating SSL Certificates...[/bold blue]")
    
    generate_self_signed_cert(SERVER_CERT, SERVER_KEY, u"localhost_server")
    generate_self_signed_cert(PROXY_CERT, PROXY_KEY, u"localhost_proxy")
    
    console.print("[bold green]All certificates generated successfully![/bold green]")

if __name__ == "__main__":
    main()
