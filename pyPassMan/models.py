import collections
import base64
from Crypto import Random
from Crypto.Cipher import AES
import sqlite3

class AESCipher:

  def __init__(self, key):
      self.bs = 32
      if len(key) >= 32:
          self.key = key[:32]
      else:
          self.key = self._pad(key)

  def encrypt(self, raw):
      raw = self._pad(raw)
      iv = Random.new().read(AES.block_size)
      cipher = AES.new(self.key, AES.MODE_CBC, iv)
      return base64.b64encode(iv + cipher.encrypt(raw))

  def decrypt(self, enc):
      enc = base64.b64decode(enc)
      iv = enc[:AES.block_size]
      cipher = AES.new(self.key, AES.MODE_CBC, iv)
      return self._unpad(cipher.decrypt(enc[AES.block_size:])).decode('utf-8')

  def _pad(self, s):
      return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

  def _unpad(self, s):
      return s[:-ord(s[len(s)-1:])]

class AccountManager:
    _con = None
    _aes = None

    def __init__(self, conn, aes_cipher):
        self._conn = conn
        self._aes = aes_cipher

        # check if db is set
        try:
            self._conn.cursor().execute('SELECT 1 FROM accounts')
        except sqlite3.OperationalError:
            self.setup_db()

    def load_all(self):
        items = []

        for row in self._conn.cursor().execute('SELECT * FROM accounts ORDER BY id'):
            items += [Account(id=int(row[0]), title=row[1], username=row[2], password=self._aes.decrypt(row[3]))]

        return items

    def load(self, id):
        cursor = self._conn.cursor()
        cursor.execute('SELECT * FROM accounts WHERE id=?', (int(id),))
        row = cursor.fetchone()
        return Account(id=int(row[0]), title=row[1], username=row[2], password=self._aes.decrypt(row[3]))

    def save(self, account):
        cursor = self._conn.cursor()
        if account.id is None:
            values = (None, account.title, account.username, self._aes.encrypt(account.password));
            cursor.execute('INSERT INTO accounts VALUES(?, ?, ?, ?)', values)
            account.id = cursor.lastrowid
        else:
            values = (account.title, account.username, self._aes.encrypt(account.password), account.id);
            cursor.execute('UPDATE accounts SET title = ?, username = ?, password = ? WHERE id = ?', values)

        self._conn.commit()

        return True

    def delete(self, id):
        self._conn.cursor().execute('DELETE FROM accounts WHERE id=?', (int(id),))
        self._conn.commit()

    def setup_db(self):
        self._conn.cursor().execute('''CREATE TABLE accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                title VARCHAR(255),
                username VARCHAR(255),
                password VARCHAR(255)
            )''')

class Account:
    title = None
    username = None
    password = None

    def __init__(self, **kwargs):
        self.id = kwargs.get('id', None)
        self.title = kwargs.get('title', '')
        self.username = kwargs.get('username', '')
        self.password = kwargs.get('password', '')


Field = collections.namedtuple('Field', 'label input')
