# Requirements
# Programming language: Python3
# Libraries Required: mysql.connector, datetime, prettytable

# Password for admin login hardcoded as: admin

import mysql.connector
import getpass
from datetime import date
from prettytable import from_db_cursor


# Customer signup
def signupUtility(dbcursor, db):
    inp_usr = input("Enter username: ")
    # username is unique for each customer
    # username is not same as name of customer
    sql = "SELECT * FROM customers WHERE username=%s"
    dbcursor.execute(sql, (inp_usr,))
    if dbcursor.fetchone():
        print("Username already taken")
    else:
        inp_pwd = input("Create password: ")
        inp_name = input("Enter name: ")
        inp_address = input("Enter address: ")
        inp_phno = int(input("Enter phone no: "))
        inp_email = input("Enter email: ")
        inp_date = date.today()
        sql = "INSERT into customers (name, address, phone_no,email, username, password, date_of_joining) values(%s,%s,%s,%s,%s,%s,%s)"
        dbcursor.execute(sql, (inp_name, inp_address, inp_phno, inp_email, inp_usr, inp_pwd, str(inp_date)))
        db.commit()
        sql = "INSERT INTO accounts (opening_date,balance,username) values(%s,%s,%s)"
        dbcursor.execute(sql, (inp_date, 0, inp_usr))
        db.commit()
        print("Congratulations! You have an account in our bank")
        print()


# Customer Login
def loginUtility(dbcursor, usr, pswd):
    st = "SELECT * FROM customers WHERE username=%s AND password=%s"
    dbcursor.execute(st, (usr, pswd,))
    if dbcursor.fetchone():
        return True
    else:
        print("Wrong username and password combination")
        return False


# Change password
def changepswdUtility(dbcursor, db, usr):
    currentpswd = input("Enter current password: ")
    newpswd = input("Enter new password: ")
    sql = "SELECT * FROM customers WHERE username=%s AND password=%s"
    dbcursor.execute(sql, (usr, currentpswd,))
    if dbcursor.fetchone():
        sql = "UPDATE customers SET password=%s WHERE username=%s and password=%s"
        dbcursor.execute(sql, (newpswd, usr, currentpswd,))
        db.commit()
        return True
    else:
        print("Current password entered is wrong")
        return False


# Calculate amount to be repayed at the end of lending period
def loanrepay(baseamt, interestrate, time):
    amt = baseamt * (pow((1 + interestrate / 100), time))
    return amt


# Admin Interface
def adminInterface(dbcursor, dictcursor, db):
    while True:
        choice = int(input(
            'Query\n1. Total no of Customers\n2. Maximum and minimum amount of money in an account\n3. Total money deposited in the bank\n4. Check out Loan Applications\n5. Logout\n'))
        if choice == 1:
            sql = "SELECT COUNT(username) FROM customers"
            dbcursor.execute(sql)
            print('Total no of customers: ' + str(dbcursor.fetchone()[0]))
        elif choice == 2:
            sql = 'SELECT MAX(balance) FROM accounts'
            dbcursor.execute(sql)
            print('Maximum amount of money in an account: ' + str(dbcursor.fetchone()[0]))
            sql = 'SELECT MIN(balance) FROM accounts'
            dbcursor.execute(sql)
            print('Minimum amount of money in an account: ' + str(dbcursor.fetchone()[0]))
        elif choice == 3:
            sql = 'SELECT SUM(balance) FROM accounts'
            dbcursor.execute(sql)
            print('Total money deposited in the bank: ' + str(dbcursor.fetchone()[0]))
        elif choice == 4:
            checkoutLoanApp(db, dbcursor, dictcursor)
        else:
            return


# Checkout loan appliactions
def checkoutLoanApp(db, dbcursor, dictcursor):
    choice = int(input(
        '1. Checkout all loan applications\n2. Checkout loan applications(pending status)\n3. Approve or reject a loan application\n '))
    if choice == 1:
        sql = 'SELECT * FROM loan'
        dbcursor.execute(sql)
        tabularop = from_db_cursor(dbcursor)
        print(tabularop)
    elif choice == 2:
        sql = 'SELECT * FROM loan WHERE admin_approval_status=%s'
        dbcursor.execute(sql, ('Pending',))
        tabularop = from_db_cursor(dbcursor)
        print(tabularop)
    else:
        loanId = int(input('Enter loan id: '))
        sql = 'SELECT * FROM loan WHERE loan_id=%s'
        dictcursor.execute(sql, (loanId,))
        result = dictcursor.fetchone()
        if result:
            interestrate = float(input('Enter interest rate(compunded annually): '))
            baseamt = result['amount']
            time = result['Time_period']
            repayamt = loanrepay(baseamt, interestrate, time)
            appDate = date.today()
            print('Total amount to be repayed at the end of lending period: ' + str(repayamt))
            chc = int(input("1. Approve\n2. Reject\n3. No action\n"))
            if chc == 1:
                sql = 'UPDATE loan SET admin_approval_status=%s, admin_approval_date=%s, repay_amount=%s, customer_approval_status=%s, Interest_rate=%s WHERE loan_id=%s'
                dictcursor.execute(sql, ('Approved', appDate, repayamt, 'Pending', interestrate, loanId,))
                db.commit()
                print('Successfully approved Loan with ID: ' + str(loanId))
            elif chc == 2:
                sql = 'UPDATE loan SET admin_approval_status=%s WHERE loan_id=%s'
                dictcursor.execute(sql, ('Rejected', loanId,))
                db.commit()
                print('Rejected Loan with ID: ' + str(loanId))
            else:
                return
        else:
            print('Loan ID invalid')
            return


# Customer Interface
def customerInterface(dbcursor, dictcursor, db):
    while True:
        choice = int(input(
            "1. Account Details\n2. Deposit Money\n3. Withdraw Money\n4. Transfer Money to another account\n5. Change password\n6. Request Loan\n7. Loan status\n8. Accept terms(amount to be repayed and interest rate) and approve a loan \n9. Logout\n"))
        if choice == 1:
            displayAccDetails(dictcursor, usr)
        elif choice == 2:
            deposit(dictcursor, usr, db)
        elif choice == 3:
            withdraw(dictcursor, usr)
        elif choice == 4:
            transfer(dictcursor, usr)
        elif choice == 5:
            if changepswdUtility(dbcursor, db, usr):
                print("Password updated Successfully!!")
            else:
                print("Password could not be updated.")
        elif choice == 6:
            loanUtility(db, dbcursor, usr)
        elif choice == 7:
            loanStatus(dictcursor, usr)
        elif choice == 8:
            customerApproval(db, dictcursor, usr)
        else:
            return


# Loan requesting utility for customer
def loanUtility(db, dbcursor, usr):
    amt = float(input('Enter amount for loan: '))
    period = float(input('Enter time period for requesting loan: '))
    sql = 'INSERT INTO loan (username,amount,Time_period,admin_approval_status) values (%s,%s,%s,%s)'
    dbcursor.execute(sql, (usr, amt, period, 'Pending',))
    db.commit()


# Check loan status for customer
def loanStatus(dbcursor, usr):
    sql = 'SELECT * FROM loan WHERE username=%s'
    dbcursor.execute(sql, (usr,))
    result = dbcursor.fetchall()
    print('Total no of loan applications: ' + str(len(result)))
    for itr in result:
        print('------------------------------------------------------------------------------------------')
        print('Loan ID: ' + str(itr['loan_id']))
        print('Requested amount: ' + str(itr['amount']))
        print('Requested time period(in years): ' + str(itr['Time_period']))
        print('Admin Approval status: ' + str(itr['admin_approval_status']))
        print('User/customer Approval status: ' + str(itr['customer_approval_status']))
        if str(itr['admin_approval_status']) == 'Approved':
            print('Amount to be repayed at the end of lending period (starting from approval date): ' + str(
                itr['repay_amount']))

        print('------------------------------------------------------------------------------------------')

    # Customer acceptance of terms of loan and approval


def customerApproval(db, dbcursor, usr):
    loanId = int(input('Enter loan id: '))
    sql = 'SELECT * FROM loan WHERE loan_id=%s AND username=%s'
    dbcursor.execute(sql, (loanId, usr,))
    result = dbcursor.fetchone()
    if result:
        if result['admin_approval_status'] != 'Approved':
            print('Loan not approved by Admin yet')
        else:
            chc = int(input('1. Approve\n2. Reject\n3. Take no action\n'))
            if chc == 1:
                sql = 'UPDATE loan SET customer_approval_status=%s WHERE loan_id=%s'
                dbcursor.execute(sql, ('Approved', loanId,))
                db.commit()
            elif chc == 2:
                sql = 'UPDATE loan SET customer_approval_status=%s WHERE loan_id=%s'
                dbcursor.execute(sql, ('Rejected', loanId,))
                db.commit()
            else:
                return
    else:
        print('Invalid Loan ID')
        return

    # Display Account details


def displayAccDetails(dbcursor, usr):
    sql = "SELECT * FROM customers NATURAL JOIN accounts WHERE username=%s"
    dbcursor.execute(sql, (usr,))
    result = dbcursor.fetchall()
    for x in result:
        print('------------------------------------------------------------------------------------------')
        print('-----Personal Details-----')
        print("Account holder name: " + str(x['name']))
        print("Account holder address: " + str(x['address']))
        print("Account holder phone number: " + str(x['name']))
        print("Account holder email: " + str(x['email']))
        print("Date of joining as customer: " + str(x['date_of_joining']))
        print('-----Account specific Information-----')
        print("Account ID: " + str(x['acc_id']))
        print("Account balance: " + str(x['balance']))
        print("Account creation date: " + str(x['opening_date']))
        print('------------------------------------------------------------------------------------------')


# Deposit Money
def deposit(dbcursor, usr, db):
    amt = float(input("Enter amount: "))
    sql = "SELECT * FROM accounts WHERE username=%s"
    dbcursor.execute(sql, (usr,))
    result = dbcursor.fetchone()
    newamt = result['balance'] + amt
    sql = "UPDATE accounts SET balance=%s WHERE username=%s"
    dbcursor.execute(sql, (newamt, usr,))
    db.commit()


# Withdraw Money
def withdraw(dbcursor, usr):
    amt = float(input("Enter amount: "))
    sql = "SELECT * FROM accounts WHERE username=%s"
    dbcursor.execute(sql, (usr,))
    result = dbcursor.fetchone()
    currentBal = result['balance']
    if amt > currentBal:
        print("Insufficient Funds to process withdrawal")
    else:
        newBal = currentBal - amt
        sql = "UPDATE accounts SET balance=%s WHERE username=%s"
        dbcursor.execute(sql, (newBal, usr,))
        db.commit()


# Transfer Money
def transfer(dbcursor, usr):
    accId = int(input("Enter recepient account id: "))
    amt = float(input("Enter amount: "))
    sql = "SELECT * FROM accounts WHERE username=%s"
    dbcursor.execute(sql, (usr,))
    result = dbcursor.fetchone()
    currentBal = result['balance']
    sql = "SELECT * FROM accounts WHERE acc_id=%s"
    dbcursor.execute(sql, (accId,))
    recepInfo = dbcursor.fetchone()
    if recepInfo:
        if amt > currentBal:
            print("Insufficient Funds to process fund transfer")
        else:
            debBal = currentBal - amt
            credBal = recepInfo['balance'] + amt
            sql = "UPDATE accounts SET balance=%s WHERE username=%s"
            dbcursor.execute(sql, (debBal, usr,))
            sql = "UPDATE accounts SET balance=%s WHERE acc_id=%s"
            dbcursor.execute(sql, (credBal, accId,))
            db.commit()
    else:
        print("Recepient account ID not valid")


if __name__ == '__main__':
    user = input(
        "Enter username for connecting to MySQL on this computer(Eg enter 'root' for connecting as root user): ")
    password = input("Enter password for connecting to MySQL on this computer: ")
    try:
        db = mysql.connector.connect(
            host="localhost",
            user=user,
            password=password)
        # db is the connenction obeject
    except:
        print("Could not connect with MySQL on this computer.")
        exit()
    dbcursor = db.cursor()
    # dbcursor is the cursor object
    dictcursor = db.cursor(dictionary=True)
    # returns each row as a dictionary

    dbcursor.execute("CREATE DATABASE IF NOT EXISTS bankingdb")

    dbcursor.execute("USE bankingdb")

    dbcursor.execute(
        "CREATE TABLE IF NOT EXISTS customers (name VARCHAR(30), address VARCHAR(100), phone_no BIGINT,email VARCHAR(50), username VARCHAR(50) PRIMARY KEY, password VARCHAR(50), date_of_joining DATE)")

    dbcursor.execute(
        "CREATE TABLE IF NOT EXISTS accounts  (acc_id INT AUTO_INCREMENT PRIMARY KEY, opening_date DATE, balance DOUBLE, username VARCHAR(50), FOREIGN KEY (username) REFERENCES customers(username))")

    dbcursor.execute(
        "CREATE TABLE IF NOT EXISTS loan (loan_id INT AUTO_INCREMENT PRIMARY KEY,username VARCHAR(50), amount DOUBLE, admin_approval_status VARCHAR(50), customer_approval_status VARCHAR(50), admin_approval_date DATE, Time_period DOUBLE, repay_amount DOUBLE, Interest_rate DOUBLE, FOREIGN KEY (username) REFERENCES customers(username))")

    print()

    print("--------Welcome to Banking  Management System--------")

    loginReq = True
    while loginReq:
        choice = int(input("1. Login as customer\n2. Signup\n3. Admin login\n4. Exit\n"))
        if choice == 1:
            usr = input("username: ")
            pswd = int(input(("Enter password: ")))
            if loginUtility(dbcursor, usr, pswd):
                customerInterface(dbcursor, dictcursor, db)
        elif choice == 2:
            signupUtility(dbcursor, db)
        elif choice == 3:
            adminpswd = 'admin'
            pswd = input("Enter password: ")
            if pswd == adminpswd:
                adminInterface(dbcursor, dictcursor, db)
            else:
                print('Admin login failed\n')
        else:
            exit()