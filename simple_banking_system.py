import random
import sqlite3

class Atm:

    def __init__(self, state='menu'):
        self.state = state

    def create_account(self):
        """Generates 16-digit CC number and 4-digit PIN"""
        bank_id = '400000'
        acct_id = '%09d' % random.randint(0, 999999999)
        bank_acct_id = [int(i) for i in list(bank_id + acct_id)]
        checksum = self.get_checksum(bank_acct_id)
        acct_num = bank_id + acct_id + checksum
        pin = '%04d' % random.randint(0, 9999)
        print('\nYour card has been created'
              + f'\nYour card number:\n{acct_num}'
                + f'\nYour card PIN:\n{pin}\n')
        self.state = 'menu'
        return acct_num, pin

    def log_in(self, card_num, pin, acct_rec):
        """Validates credentials"""
        if acct_rec is None:
            print('\nWrong card number or PIN!\n')
            self.state = 'menu'
        elif card_num in acct_rec and pin in acct_rec:
            print('\nYou have successfully logged in!\n')
            self.state = 'logged in'
        else:
            print('\nWrong card number or PIN!\n')
            self.state = 'menu'

    def get_balance(self, bal):
        """Prints available balance"""
        print(f'\nBalance: {bal[0]}\n')

    def log_out(self):
        """Logs out and returns to main menu"""
        print('\nYou have successfully logged out!\n')
        self.state = 'menu'

    def exit(self):
        """Exits program"""
        print('\nBye!\n')
        self.state = 'exiting'

    def get_checksum(self, id_num):
        """Finds checksum of 15-digit bank & account id number using Luhn's
        algorighm. 'id_num' parameter is a list of integers. Returns a string.
        """

        # Copy id_num
        id_num_copy = id_num

        # Multiply odd-indexed numbers by 2
        id_num_copy[::2] = [i * 2 for i in id_num_copy[::2]]

        # Subtract 9 from all numbers greater than 9
        id_num_copy = [i - 9 if i > 9 else i * 1 for i in id_num_copy]

        # Sum all numbers
        id_num_sum = sum(id_num_copy)

        # Calculate & return checksum
        if id_num_sum % 10 == 0:
            return str(0)
        else:
            return str(10 - id_num_sum % 10)

    def add_income(self):
        print('Income was added!\n')


def main():
    conn = sqlite3.connect('card.s3db')
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS card (
                    id INTEGER,
                    number TEXT,
                    pin TEXT,
                    balance INTEGER DEFAULT 0
                    );''')
    conn.commit()
    atm = Atm()
    while atm.state != 'exiting':
        if atm.state == 'menu':
            action = int(input('1. Create an account'
                               + '\n2. Log into account'
                               + '\n0. Exit\n'))
            if action == 1:
                atm.state = 'creating account'
            elif action == 2:
                atm.state = 'logging in'
            elif action == 0:
                atm.exit()
        elif atm.state == 'creating account':
            new_acct_num, new_pin = atm.create_account()
            cur.execute('''INSERT INTO card (number, pin)
                                VALUES (?, ?)''', (new_acct_num, new_pin))
            conn.commit()
        elif atm.state == 'logging in':
            card_num = input('\nEnter your card number:\n')
            pin = input('Enter your PIN:\n')
            cur.execute('SELECT * FROM card WHERE number=?', (card_num,))
            acct_rec = cur.fetchone()
            conn.commit()
            atm.log_in(card_num, pin, acct_rec)
        elif atm.state == 'logged in':
            action = int(input('1. Balance'
                               + '\n2. Add income'
                               + '\n3. Do transfer'
                               + '\n4. Close account'
                               + '\n5. Log out'
                               + '\n0. Exit\n'))
            if action == 1:
                cur.execute(
                    'SELECT balance FROM card WHERE number=?', (card_num,))
                bal = cur.fetchone()
                conn.commit()
                atm.get_balance(bal)
            elif action == 2:
                inc = int(input('\nEnter income:\n'))
                cur.execute(
                    'SELECT balance FROM card WHERE number=?', (card_num,))
                bal = cur.fetchone()
                conn.commit()
                bal = int(bal[0]) + inc
                cur.execute(
                    'UPDATE card SET balance=? WHERE number=?', (bal, card_num))
                conn.commit()
                atm.add_income()
            elif action == 3:
                transfer_to = str(
                    input('\nTransfer\nEnter card number:\n'))
                transfer_id_num = transfer_to[0:15]
                transfer_id_num = [int(i) for i in list(transfer_id_num)]
                checksum = atm.get_checksum(transfer_id_num)
                cur.execute(
                    'SELECT * FROM card WHERE number=?', (transfer_to,))
                record = cur.fetchone()
                conn.commit()
                cur.execute(
                    'SELECT balance FROM card WHERE number=?', (card_num,))
                bal = cur.fetchone()
                conn.commit()
                # Same account?
                if transfer_to == card_num:
                    print("You can't transfer money to the same account!\n")
                # Verify checksum
                elif checksum != transfer_to[-1]:
                    print('Probably you made a mistake in the card number. '
                          'Please try again!\n')
                # Exists in DB?
                elif record is None:
                    print('Such a card does not exist.\n')
                else:
                    transfer_amt = int(input(
                        'Enter how much money you want to transfer:\n'))
                    # Enough money?
                    if transfer_amt > int(bal[0]):
                        print('Not enough money!\n')
                    else:
                        new_bal = int(bal[0]) - transfer_amt
                        cur.execute('''UPDATE card SET balance=? WHERE 
                                        number=?''', (new_bal, card_num))
                        conn.commit()
                        cur.execute('''SELECT balance FROM card WHERE
                                    number=?''', (transfer_to,))
                        transfer_bal = cur.fetchone()
                        new_transfer_bal = int(transfer_bal[0]) + transfer_amt
                        cur.execute('''UPDATE card SET balance=? WHERE 
                                        number=?''', (new_transfer_bal,
                                                      transfer_to))
                        conn.commit()
                        print('Success!\n')
            elif action == 4:
                cur.execute("DELETE FROM card WHERE number=?", (card_num,))
                conn.commit()
                print('\nThis account has been closed!\n')
            elif action == 5:
                atm.log_out()
            elif action == 0:
                atm.exit()


if __name__ == '__main__':
    main()
