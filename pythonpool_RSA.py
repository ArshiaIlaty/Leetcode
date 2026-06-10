from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import binascii
 
keyPair = RSA.generate(3072)
 
pubKey = keyPair.publickey()
# pubKey = keyPair.privatekey()
print(f"Public key:  (n={hex(pubKey.n)}, e={hex(pubKey.e)})")
pubKeyPEM = pubKey.exportKey()
print(pubKeyPEM.decode('ascii'))
 
print(f"Private key: (n={hex(pubKey.n)}, d={hex(keyPair.d)})")
privKeyPEM = keyPair.exportKey()
print(privKeyPEM.decode('ascii'))
 
#encryption
msg = 'A message for encryption'
encryptor = PKCS1_OAEP.new(pubKey)
encrypted = encryptor.encrypt(msg)
print("Encrypted:", binascii.hexlify(encrypted))

#decryption
# decryptor = PKCS1_OAEP.new(privKey)
# decrypted = decryptor.encrypt(msg)
# print("Encrypted:", binascii.hexlify(decrypted))


