from string import ascii_letters, ascii_lowercase, ascii_uppercase, digits
from random import randint, choices


N = 1000000

with open('URLs.txt', 'w') as f:
    for _ in range(N):
        host_name, server_name, tld_name, uri = (
            ''.join(choices(ascii_letters, k=randint(1, 4))),
            ''.join(choices(ascii_letters + digits, k=randint(3, 16))),
            ''.join(choices(ascii_letters, k=randint(2, 4))),
            ''.join(choices(ascii_letters + digits, k=randint(10, 200))))
        url = 'http://{}.{}.{}/{}'.format(host_name, server_name,
                                          tld_name, uri)
        f.write(url + '\n')
