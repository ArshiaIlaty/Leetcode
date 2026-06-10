import rsa

def generate_keys():
    (pubKey, privKey) = rsa.newkeys(1024)
    