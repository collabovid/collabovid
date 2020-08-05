from .command import Command
import os
import zipfile
import struct

from Crypto import Random
from Crypto.Cipher import AES
from datetime import datetime, timezone


lang_prefix = 'LC_ALL=en_US'

class ShareConfigCommand(Command):
    KEY_FILE_SIZE = 128
    KEY_FILE_TYPE = str(KEY_FILE_SIZE) + 's'

    KEYS_DIRECTORY = ".deployment/.keys"

    def run(self, args):
        if args.collect:
            self._collect('.deployment/config.zip')
        elif args.share:
            self.run_shell_command(f"{lang_prefix} git pull", cwd=".deployment/")
            self._collect('.deployment/config.zip')
            self._encrypt('.deployment/config.zip')
            self.run_shell_command(f"{lang_prefix} git add config.zip.enc", cwd=".deployment/")
            self.run_shell_command(f"{lang_prefix} git commit -m \"New Config\"", cwd=".deployment/")
            self.run_shell_command(f"{lang_prefix} git push", cwd=".deployment/")
            os.remove('.deployment/config.zip')
        elif args.generate_key:
            self._generate_key()
        elif args.load:
            self.run_shell_command(f"{lang_prefix} git pull", cwd=".deployment/")
            now_utc = str(datetime.now(timezone.utc).timestamp())
            self.print_info("Saving current config")
            self._collect('.deployment/.old/' + now_utc + '.zip')
            self._decrypt('.deployment/config.zip.enc')
            os.remove('.deployment/config.zip')

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument('--collect', action="store_true")
        parser.add_argument('--share', action="store_true")
        parser.add_argument('--load', action="store_true")
        parser.add_argument('--generate-key', action="store_true")

    def help(self):
        return "Share release config with others"

    def name(self):
        return "share-config"

    def _get_current_key(self):

        self.print_info("Obtaining key files")
        key_files = sorted(list(os.listdir(ShareConfigCommand.KEYS_DIRECTORY)), reverse=True)
        key_files = [key_file for key_file in key_files if not key_file.startswith('.')]

        self.print_info("Found " + str(len(key_files)) + " key files")

        if len(key_files) == 0:
            return None, None
        else:
            key_file = key_files[0]

            return self._get_key_by_file(key_file), key_file

    def _get_key_by_file(self, key_file):

        full_path = os.path.join(ShareConfigCommand.KEYS_DIRECTORY, key_file)

        if os.path.isfile(full_path):
            with open(full_path, 'rb') as f:
                key = f.read()

            self.print_info("Loaded key " + str(key_file))

            return key

        return None

    def _generate_key(self, size=32):

        self.print_info("Generating key of size" + str(size))

        key = Random.get_random_bytes(size)
        now_utc = str(datetime.now(timezone.utc).timestamp())

        key_file = os.path.join(ShareConfigCommand.KEYS_DIRECTORY, now_utc + ".key")

        with open(key_file, 'wb') as f:
            f.write(key)

        self.print_info("Saved key to " + key_file)

    def _encrypt(self, file_name):

        key, key_file = self._get_current_key()

        if key is None:
            print("Could not load any key.")
            return

        self.print_info("Encrypting " + file_name + "...")

        with open(file_name, 'rb') as fo:
            plaintext = fo.read()
        enc = ShareConfigCommand.encrypt(plaintext, key)

        target_file = file_name + ".enc"
        with open(target_file, 'wb') as fo:
            fo.write(struct.pack(ShareConfigCommand.KEY_FILE_TYPE, str(key_file).encode('ascii')))
            fo.write(enc)

        self.print_info("Encrypted file saved to " + target_file)

    def _decrypt(self, file_name, extract_to = '.deployment/loaded_config'):

        self.print_info("Decrypting " + file_name)
        with open(file_name, 'rb') as f:
            content = f.read()

            key_file = str(
                struct.unpack_from(ShareConfigCommand.KEY_FILE_TYPE, content[:ShareConfigCommand.KEY_FILE_SIZE])[
                    0].partition(b'\0')[0].decode('ascii'))
            ciphertext = content[ShareConfigCommand.KEY_FILE_SIZE:]

        self.print_info("Loaded " + file_name)

        key = self._get_key_by_file(key_file)

        if key:
            dec = ShareConfigCommand.decrypt(ciphertext, key)

            zip_file = file_name[:-4]
            with open(zip_file, 'wb') as fo:
                fo.write(dec)

            self.print_info("Decrypted to " + zip_file)

            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_to)

            self.print_info("Extracted to " + extract_to)

        else:
            self.print_info("Could not find key file " + key_file)

    def _collect(self, target_path):
        self.print_info("Collecting zip file...")

        paths = self.run_shell_command(f"{lang_prefix} git clean -dnx | cut -c 14-", cwd="k8s/",
                                       collect_output=True).stdout.decode('utf-8').rstrip().split('\n')

        cleaned_paths = ['cvid-config.json']
        for path in paths:

            if path.startswith('dist'):
                continue

            cleaned_paths.append(os.path.join('k8s/', path))

        with zipfile.ZipFile(target_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:

            for path in cleaned_paths:
                if os.path.isfile(path):
                    zip_file.write(path)
                    print("+", path)
                else:
                    ShareConfigCommand.zipdir(path, zip_file)

        self.print_info("Zip file saved to " + target_path)

    @staticmethod
    def zipdir(path, ziph):
        """
        Adds a directory to the given zip.
        :param path:
        :param ziph:
        :return:
        """
        for root, dirs, files in os.walk(path):
            for file in files:
                ziph.write(os.path.join(root, file))
                print("+", os.path.join(root, file))

    @staticmethod
    def pad(s):
        padding = (AES.block_size - len(s) % AES.block_size)
        return padding, s + b"\0" * padding

    @staticmethod
    def encrypt(message, key):
        padding, message = ShareConfigCommand.pad(message)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        return struct.pack('i', padding) + iv + cipher.encrypt(message)

    @staticmethod
    def decrypt(ciphertext, key):
        padding = struct.unpack('i', ciphertext[:4])[0]
        iv = ciphertext[4:4 + AES.block_size]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        plaintext = cipher.decrypt(ciphertext[4 + AES.block_size:])
        return plaintext[:len(plaintext) - padding]
