import mysql.connector

def setup_database():
    try:
        # Connect strictly to my_sql to create the database initially
        # Adjust user/password if necessary depending on your environment. Default WAMP/XAMPP uses 'root' and ''
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="dnyanesh"
        )
        cursor = conn.cursor()

        print("Dropping existing database if it exists...")
        cursor.execute("DROP DATABASE IF EXISTS Bank_system_Web_app")
        
        print("Creating database Bank_system_Web_app...")
        cursor.execute("CREATE DATABASE Bank_system_Web_app")
        cursor.execute("USE Bank_system_Web_app")
        
        # We will create tables in the exact order taking into account Foreign Key dependencies.

        print("Creating RBI table...")
        cursor.execute("""
            CREATE TABLE RBI (
                RBI_id INT PRIMARY KEY AUTO_INCREMENT,
                headquarter VARCHAR(255),
                Repo_rate DECIMAL(5,2),
                Governor_name VARCHAR(255),
                SLR DECIMAL(5,2)
            )
        """)

        print("Creating BANK table...")
        cursor.execute("""
            CREATE TABLE BANK (
                Bank_id INT PRIMARY KEY AUTO_INCREMENT,
                Bank_name VARCHAR(255) NOT NULL,
                city VARCHAR(100),
                street VARCHAR(100),
                Street_no VARCHAR(50),
                street_name VARCHAR(100),
                Established_date DATE,
                Bank_type VARCHAR(100),
                RBI_id INT,
                FOREIGN KEY (RBI_id) REFERENCES RBI(RBI_id) ON DELETE SET NULL
            )
        """)

        print("Creating BRANCH table...")
        cursor.execute("""
            CREATE TABLE BRANCH (
                Branch_code INT PRIMARY KEY AUTO_INCREMENT,
                Branch_name VARCHAR(255) NOT NULL,
                city VARCHAR(100),
                street VARCHAR(100),
                Street_no VARCHAR(50),
                street_name VARCHAR(100),
                IFSC_code VARCHAR(50) UNIQUE,
                Bank_id INT,
                FOREIGN KEY (Bank_id) REFERENCES BANK(Bank_id) ON DELETE CASCADE
            )
        """)

        print("Creating BRANCH_PHONE table...")
        cursor.execute("""
            CREATE TABLE BRANCH_PHONE (
                Branch_code INT,
                Phone_number VARCHAR(20),
                PRIMARY KEY (Branch_code, Phone_number),
                FOREIGN KEY (Branch_code) REFERENCES BRANCH(Branch_code) ON DELETE CASCADE
            )
        """)

        print("Creating EMPLOYEE table...")
        cursor.execute("""
            CREATE TABLE EMPLOYEE (
                Emp_id INT PRIMARY KEY AUTO_INCREMENT,
                Emp_name VARCHAR(255) NOT NULL,
                Designation VARCHAR(100),
                Salary DECIMAL(15,2),
                city VARCHAR(100),
                street VARCHAR(100),
                Street_no VARCHAR(50),
                street_name VARCHAR(100),
                Branch_code INT,
                FOREIGN KEY (Branch_code) REFERENCES BRANCH(Branch_code) ON DELETE SET NULL
            )
        """)

        print("Creating EMPLOYEE_PHONE table...")
        cursor.execute("""
            CREATE TABLE EMPLOYEE_PHONE (
                Emp_id INT,
                Emp_Mobile_No VARCHAR(20),
                PRIMARY KEY (Emp_id, Emp_Mobile_No),
                FOREIGN KEY (Emp_id) REFERENCES EMPLOYEE(Emp_id) ON DELETE CASCADE
            )
        """)

        # Subtypes of EMPLOYEE
        print("Creating SENIOR_MANAGER table...")
        cursor.execute("""
            CREATE TABLE SENIOR_MANAGER (
                S_Manager_ID INT PRIMARY KEY AUTO_INCREMENT,
                Annual_Bonus_Plan VARCHAR(255),
                Emp_id INT UNIQUE,
                FOREIGN KEY (Emp_id) REFERENCES EMPLOYEE(Emp_id) ON DELETE CASCADE
            )
        """)

        print("Creating MANAGER table...")
        cursor.execute("""
            CREATE TABLE MANAGER (
                Manager_ID INT PRIMARY KEY AUTO_INCREMENT,
                Budget_Authority DECIMAL(15,2),
                Emp_id INT UNIQUE,
                FOREIGN KEY (Emp_id) REFERENCES EMPLOYEE(Emp_id) ON DELETE CASCADE
            )
        """)

        print("Creating CASHIER table...")
        cursor.execute("""
            CREATE TABLE CASHIER (
                Cashier_ID INT PRIMARY KEY AUTO_INCREMENT,
                Shift_Code VARCHAR(50),
                Emp_id INT UNIQUE,
                FOREIGN KEY (Emp_id) REFERENCES EMPLOYEE(Emp_id) ON DELETE CASCADE
            )
        """)

        print("Creating CUSTOMER table...")
        cursor.execute("""
            CREATE TABLE CUSTOMER (
                Customer_ID INT PRIMARY KEY AUTO_INCREMENT,
                F_Name VARCHAR(100) NOT NULL,
                L_Name VARCHAR(100) NOT NULL,
                city VARCHAR(100),
                street VARCHAR(100),
                Street_no VARCHAR(50),
                street_name VARCHAR(100),
                E_mail VARCHAR(255) UNIQUE
            )
        """)

        print("Creating CUSTOMER_PHONE table...")
        cursor.execute("""
            CREATE TABLE CUSTOMER_PHONE (
                Customer_ID INT,
                Customer_Mob_No VARCHAR(20),
                PRIMARY KEY (Customer_ID, Customer_Mob_No),
                FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID) ON DELETE CASCADE
            )
        """)

        print("Creating ACCOUNT table...")
        cursor.execute("""
            CREATE TABLE ACCOUNT (
                Account_No INT PRIMARY KEY AUTO_INCREMENT,
                Customer_ID INT,
                Withdraw DECIMAL(15,2) DEFAULT 0.00,
                Deposit DECIMAL(15,2) DEFAULT 0.00,
                Balance DECIMAL(15,2) DEFAULT 0.00,
                Opening_Date DATE,
                Nominee_name VARCHAR(255),
                Account_Status VARCHAR(50),
                E_KYC_Status VARCHAR(50),
                FOREIGN KEY (Customer_ID) REFERENCES CUSTOMER(Customer_ID) ON DELETE CASCADE
            )
        """)

        # Subtypes of Account
        print("Creating SAVING table...")
        cursor.execute("""
            CREATE TABLE SAVING (
                Account_No INT PRIMARY KEY,
                Interest_Rate DECIMAL(5,2),
                Withdrawal_Limit DECIMAL(15,2),
                FOREIGN KEY (Account_No) REFERENCES ACCOUNT(Account_No) ON DELETE CASCADE
            )
        """)

        print("Creating CURRENT table...")
        cursor.execute("""
            CREATE TABLE CURRENT (
                Account_No INT PRIMARY KEY,
                Overdraft_Limit DECIMAL(15,2),
                Cheque_Book_No VARCHAR(100),
                FOREIGN KEY (Account_No) REFERENCES ACCOUNT(Account_No) ON DELETE CASCADE
            )
        """)

        print("Creating LOAN table...")
        cursor.execute("""
            CREATE TABLE LOAN (
                Loan_No INT PRIMARY KEY AUTO_INCREMENT,
                Loan_Amount DECIMAL(15,2),
                Cibil_Score INT,
                Loan_Officer VARCHAR(255),
                Interest_Rate DECIMAL(5,2),
                Loan_Status VARCHAR(50),
                Customer_id INT,
                FOREIGN KEY (Customer_id) REFERENCES CUSTOMER(Customer_ID) ON DELETE CASCADE
            )
        """)

        print("Creating PAYMENT table...")
        cursor.execute("""
            CREATE TABLE PAYMENT (
                Payment_no INT PRIMARY KEY AUTO_INCREMENT,
                paid_amt DECIMAL(15,2),
                pending_amt DECIMAL(15,2),
                Payment_date DATE,
                Loan_no INT,
                FOREIGN KEY (Loan_no) REFERENCES LOAN(Loan_No) ON DELETE CASCADE
            )
        """)

        print("Creating ATM table...")
        cursor.execute("""
            CREATE TABLE ATM (
                Account_No INT PRIMARY KEY,
                ATM_Status ENUM('Active', 'Inactive') DEFAULT 'Inactive',
                FOREIGN KEY (Account_No) REFERENCES ACCOUNT(Account_No) ON DELETE CASCADE
            )
        """)

        print("Creating UPI_APP table...")
        cursor.execute("""
            CREATE TABLE UPI_APP (
                Account_No INT PRIMARY KEY,
                UPI_Link_Status ENUM('Linked', 'Not Linked') DEFAULT 'Not Linked',
                FOREIGN KEY (Account_No) REFERENCES ACCOUNT(Account_No) ON DELETE CASCADE
            )
        """)

        print("Creating TRANSACTION table...")
        cursor.execute("""
            CREATE TABLE TRANSACTION (
                Transaction_ID INT PRIMARY KEY AUTO_INCREMENT,
                Account_No INT,
                Transaction_Type ENUM('Deposit', 'Withdrawal'),
                Amount DECIMAL(15,2),
                Transaction_Mode ENUM('Cash', 'UPI', 'ATM'),
                UTR_No VARCHAR(20) UNIQUE,
                Post_Balance DECIMAL(15,2) DEFAULT 0.00,
                Transaction_Date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (Account_No) REFERENCES ACCOUNT(Account_No) ON DELETE CASCADE
            )
        """)

        conn.commit()

        # Update AUTO_INCREMENT to generate larger, formatted IDs
        print("Setting AUTO_INCREMENT seeds...")
        cursor.execute("ALTER TABLE CUSTOMER AUTO_INCREMENT = 101;")
        cursor.execute("ALTER TABLE EMPLOYEE AUTO_INCREMENT = 201;")
        cursor.execute("ALTER TABLE ACCOUNT AUTO_INCREMENT = 10001;")
        cursor.execute("ALTER TABLE LOAN AUTO_INCREMENT = 5001;")
        conn.commit()
        
        print("Database 'Bank_system_Web_app' and all 19 tables successfully created!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    setup_database()
