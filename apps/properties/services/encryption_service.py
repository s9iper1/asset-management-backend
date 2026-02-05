"""
Encryption service for file mode data storage.

Uses AES encryption with PBKDF2 key derivation for secure data export/import.
"""
import json
import base64
import os
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet


class EncryptionService:
    """AES encryption for file mode data"""

    ITERATIONS = 100000  # PBKDF2 iterations for key derivation

    @staticmethod
    def derive_key(password: str, salt: bytes) -> bytes:
        """
        Derive encryption key from password using PBKDF2

        Args:
            password: User's password
            salt: Random salt bytes

        Returns:
            bytes: Derived encryption key
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=EncryptionService.ITERATIONS,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    @staticmethod
    def encrypt_data(data: dict, password: str) -> bytes:
        """
        Encrypt user data with password

        Args:
            data: Dictionary of user data to encrypt
            password: User's encryption password

        Returns:
            bytes: Encrypted data with prepended salt
        """
        # Generate random salt
        salt = os.urandom(16)

        # Derive encryption key
        key = EncryptionService.derive_key(password, salt)

        # Encrypt data
        f = Fernet(key)
        json_data = json.dumps(data, default=str).encode()  # default=str handles datetime/decimal
        encrypted = f.encrypt(json_data)

        # Prepend salt to encrypted data
        return salt + encrypted

    @staticmethod
    def decrypt_data(encrypted_bytes: bytes, password: str) -> dict:
        """
        Decrypt user data with password

        Args:
            encrypted_bytes: Encrypted data (salt + encrypted content)
            password: User's encryption password

        Returns:
            dict: Decrypted data

        Raises:
            ValueError: If password is incorrect or data is corrupted
        """
        # Extract salt from first 16 bytes
        salt = encrypted_bytes[:16]
        encrypted_data = encrypted_bytes[16:]

        # Derive key from password
        key = EncryptionService.derive_key(password, salt)

        # Decrypt
        f = Fernet(key)
        try:
            decrypted = f.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise ValueError("Decryption failed. Invalid password or corrupted data.")
