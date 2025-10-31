#!/usr/bin/env python3
"""
Backup encryption module for SoundHash.

Supports encryption and decryption of backup files using GPG or age.
"""

import logging
import os
import subprocess
from pathlib import Path


class EncryptionError(Exception):
    """Custom exception for encryption errors."""

    pass


class BackupEncryption:
    """Handles backup file encryption and decryption."""

    def __init__(self, method: str = "gpg", key: str | None = None):
        """
        Initialize encryption handler.

        Args:
            method: Encryption method ('gpg' or 'age')
            key: Encryption key (GPG key ID or age public key/password)
        """
        self.logger = logging.getLogger(__name__)
        self.method = method.lower()
        self.key = key

        if self.method not in ["gpg", "age"]:
            raise EncryptionError(f"Unsupported encryption method: {method}")

        # Verify encryption tool is available
        self._verify_encryption_tool()

    def _verify_encryption_tool(self) -> None:
        """Verify that the required encryption tool is installed."""
        tool = "gpg" if self.method == "gpg" else "age"

        try:
            result = subprocess.run(
                [tool, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            self.logger.debug(f"{tool} version: {result.stdout.split()[0]}")
        except FileNotFoundError:
            raise EncryptionError(
                f"{tool} not found. Install with: "
                f"{'apt-get install gnupg' if tool == 'gpg' else 'https://github.com/FiloSottile/age'}"
            ) from None
        except subprocess.CalledProcessError as e:
            raise EncryptionError(f"Failed to verify {tool}: {str(e)}") from e

    def encrypt_file(self, file_path: Path, output_path: Path | None = None) -> Path:
        """
        Encrypt a backup file.

        Args:
            file_path: Path to the file to encrypt
            output_path: Path for encrypted output (default: file_path + .gpg/.age)

        Returns:
            Path to the encrypted file

        Raises:
            EncryptionError: If encryption fails
        """
        if not file_path.exists():
            raise EncryptionError(f"File not found: {file_path}")

        if output_path is None:
            suffix = ".gpg" if self.method == "gpg" else ".age"
            output_path = file_path.with_suffix(file_path.suffix + suffix)

        self.logger.info(f"Encrypting {file_path} to {output_path}")

        try:
            if self.method == "gpg":
                self._encrypt_gpg(file_path, output_path)
            else:
                self._encrypt_age(file_path, output_path)

            # Verify encrypted file was created
            if not output_path.exists():
                raise EncryptionError("Encrypted file was not created")

            file_size = output_path.stat().st_size
            self.logger.info(f"Encryption complete: {output_path} ({file_size / 1024 / 1024:.2f} MB)")

            return output_path

        except Exception as e:
            # Clean up failed encryption
            if output_path and output_path.exists():
                output_path.unlink()
            raise EncryptionError(f"Encryption failed: {str(e)}") from e

    def _encrypt_gpg(self, input_path: Path, output_path: Path) -> None:
        """Encrypt using GPG."""
        if not self.key:
            raise EncryptionError("GPG key ID or recipient required for encryption")

        cmd = [
            "gpg",
            "--encrypt",
            "--recipient", self.key,
            "--output", str(output_path),
            "--trust-model", "always",  # Trust keys without confirmation
            "--batch",
            "--yes",
            str(input_path),
        ]

        self.logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise EncryptionError(f"GPG encryption failed: {result.stderr}")

    def _encrypt_age(self, input_path: Path, output_path: Path) -> None:
        """Encrypt using age."""
        if not self.key:
            raise EncryptionError("Age public key or password required for encryption")

        # Determine if key is a public key or passphrase
        if self.key.startswith("age1"):
            # Public key encryption
            cmd = [
                "age",
                "--encrypt",
                "--recipient", self.key,
                "--output", str(output_path),
                str(input_path),
            ]
        else:
            # Passphrase encryption
            cmd = [
                "age",
                "--encrypt",
                "--passphrase",
                "--output", str(output_path),
                str(input_path),
            ]

        self.logger.debug(f"Running: age --encrypt ...")

        # Use passphrase via stdin if passphrase mode
        input_data = f"{self.key}\n{self.key}\n" if not self.key.startswith("age1") else None

        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise EncryptionError(f"Age encryption failed: {result.stderr}")

    def decrypt_file(self, file_path: Path, output_path: Path | None = None, key: str | None = None) -> Path:
        """
        Decrypt a backup file.

        Args:
            file_path: Path to the encrypted file
            output_path: Path for decrypted output (default: removes .gpg/.age extension)
            key: Decryption key (optional, uses instance key if not provided)

        Returns:
            Path to the decrypted file

        Raises:
            EncryptionError: If decryption fails
        """
        if not file_path.exists():
            raise EncryptionError(f"File not found: {file_path}")

        if output_path is None:
            # Remove encryption extension
            if file_path.suffix in [".gpg", ".age"]:
                output_path = file_path.with_suffix("")
            else:
                output_path = file_path.parent / f"{file_path.stem}_decrypted{file_path.suffix}"

        decryption_key = key or self.key

        self.logger.info(f"Decrypting {file_path} to {output_path}")

        try:
            if self.method == "gpg":
                self._decrypt_gpg(file_path, output_path)
            else:
                self._decrypt_age(file_path, output_path, decryption_key)

            # Verify decrypted file was created
            if not output_path.exists():
                raise EncryptionError("Decrypted file was not created")

            file_size = output_path.stat().st_size
            self.logger.info(f"Decryption complete: {output_path} ({file_size / 1024 / 1024:.2f} MB)")

            return output_path

        except Exception as e:
            # Clean up failed decryption
            if output_path and output_path.exists():
                output_path.unlink()
            raise EncryptionError(f"Decryption failed: {str(e)}") from e

    def _decrypt_gpg(self, input_path: Path, output_path: Path) -> None:
        """Decrypt using GPG."""
        cmd = [
            "gpg",
            "--decrypt",
            "--output", str(output_path),
            "--batch",
            "--yes",
            str(input_path),
        ]

        self.logger.debug(f"Running: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            raise EncryptionError(f"GPG decryption failed: {result.stderr}")

    def _decrypt_age(self, input_path: Path, output_path: Path, key: str | None) -> None:
        """Decrypt using age."""
        if not key:
            raise EncryptionError("Age private key or password required for decryption")

        # Initialize key_file to None
        key_file = None

        # Determine if key is a private key or passphrase
        if key.startswith("AGE-SECRET-KEY-"):
            # Private key decryption
            # Save private key to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
                f.write(key)
                key_file = f.name
            
            # Restrict permissions to owner only
            os.chmod(key_file, 0o600)

            cmd = [
                "age",
                "--decrypt",
                "--identity", key_file,
                "--output", str(output_path),
                str(input_path),
            ]
        else:
            # Passphrase decryption
            cmd = [
                "age",
                "--decrypt",
                "--passphrase",
                "--output", str(output_path),
                str(input_path),
            ]

        self.logger.debug(f"Running: age --decrypt ...")

        # Use passphrase via stdin if passphrase mode
        input_data = f"{key}\n" if not key.startswith("AGE-SECRET-KEY-") else None

        result = subprocess.run(
            cmd,
            input=input_data,
            capture_output=True,
            text=True,
        )

        # Clean up temp key file if it was created
        if key_file is not None:
            try:
                os.unlink(key_file)
            except (OSError, FileNotFoundError) as e:
                self.logger.debug(f"Failed to remove temp key file: {e}")

        if result.returncode != 0:
            raise EncryptionError(f"Age decryption failed: {result.stderr}")


def main():
    """Test encryption/decryption."""
    import argparse
    import sys
    from pathlib import Path

    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.logging_config import setup_logging

    parser = argparse.ArgumentParser(description="Backup file encryption/decryption")
    parser.add_argument("action", choices=["encrypt", "decrypt"], help="Action to perform")
    parser.add_argument("file", type=Path, help="File to encrypt/decrypt")
    parser.add_argument("--method", choices=["gpg", "age"], default="gpg", help="Encryption method")
    parser.add_argument("--key", required=True, help="Encryption/decryption key")
    parser.add_argument("--output", type=Path, help="Output file path")
    parser.add_argument("--log-level", default="INFO", help="Logging level")

    args = parser.parse_args()

    setup_logging(log_level=args.log_level)

    try:
        encryptor = BackupEncryption(method=args.method, key=args.key)

        if args.action == "encrypt":
            output = encryptor.encrypt_file(args.file, args.output)
            print(f"Encrypted: {output}")
        else:
            output = encryptor.decrypt_file(args.file, args.output)
            print(f"Decrypted: {output}")

        sys.exit(0)

    except EncryptionError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
