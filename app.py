from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from db_config import get_db_connection
import mysql.connector

app = Flask(__name__)
app.secret_key = 'pccoe_bank_secret_key_2026' # Changed to something more secure locally

def handle_db_error(e):
    err_str = str(e)
    # Check if this is an explicit account check failure
    if hasattr(e, 'message') and e.message == 'Account not found':
        return 'Account not found. Please verify the account number.'
    
    if '1452' in err_str:
        return 'Invalid reference. Please ensure the linked ID (like Customer or Loan ID) actually exists.'
    elif '1062' in err_str:
        return 'Duplicate entry. This record already exists in the system.'
    elif '1366' in err_str or '1265' in err_str:
        return 'Data format error. Please check your inputs for invalid numbers or text.'
    
    # Optional: Log the full error to server console for debugging if needed
    print(f"DEBUG DB ERROR: {err_str}")
    return 'An unexpected database error occurred. Please verify your submitted details.'

@app.before_request
def require_login():
    # Only protect dashboard and API routes
    allowed_routes = ['login', 'static']
    if request.endpoint not in allowed_routes and 'user_logged_in' not in session:
        return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == 'pccoe':
            session['user_logged_in'] = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('login.html', error='Invalid Password. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_logged_in', None)
    return redirect(url_for('login'))

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

# ==============================================================
# DASHBOARD STATS
# ==============================================================
@app.route('/api/dashboard_stats', methods=['GET'])
def get_dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM CUSTOMER")
        customers = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM ACCOUNT")
        accounts = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM TRANSACTION")
        transactions = cursor.fetchone()['count']
        
        return jsonify({'success': True, 'customers': customers, 'accounts': accounts, 'transactions': transactions})
    except Exception as e:
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# CUSTOMER MODULE
# ==============================================================
@app.route('/api/customers', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_customers():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("""
                SELECT c.*, GROUP_CONCAT(cp.Customer_Mob_No) as mobile_number 
                FROM CUSTOMER c 
                LEFT JOIN CUSTOMER_PHONE cp ON c.Customer_ID = cp.Customer_ID 
                GROUP BY c.Customer_ID
            """)
            return jsonify({'success': True, 'data': cursor.fetchall()})

        elif request.method == 'POST':
            data = request.json
            email = data.get('email') if data.get('email') and data.get('email').strip() else None
            cursor.execute("""
                INSERT INTO CUSTOMER (F_Name, L_Name, E_mail, city, street, Street_no, street_name) 
                VALUES (%s, %s, %s, %s, %s, %s, '')
            """, (data['first_name'], data['last_name'], email, data.get('city', ''), data.get('street', ''), data.get('street_no', '')))
            customer_id = cursor.lastrowid
            
            if data.get('mobile_number'):
                for phone in data['mobile_number'].split(','):
                    phone = phone.strip()
                    if phone:
                        cursor.execute("INSERT INTO CUSTOMER_PHONE (Customer_ID, Customer_Mob_No) VALUES (%s, %s)", (customer_id, phone))
            conn.commit()
            return jsonify({'success': True, 'message': 'Customer created successfully'})

        elif request.method == 'PUT':
            data = request.json
            cid = data['customer_id']
            email = data.get('email') if data.get('email') and data.get('email').strip() else None
            cursor.execute("""
                UPDATE CUSTOMER SET F_Name=%s, L_Name=%s, E_mail=%s, city=%s, street=%s, Street_no=%s 
                WHERE Customer_ID=%s
            """, (data['first_name'], data['last_name'], email, data.get('city', ''), data.get('street', ''), data.get('street_no', ''), cid))
            
            # Recreate phones
            cursor.execute("DELETE FROM CUSTOMER_PHONE WHERE Customer_ID=%s", (cid,))
            if data.get('mobile_number'):
                for phone in data['mobile_number'].split(','):
                    phone = phone.strip()
                    if phone:
                        cursor.execute("INSERT INTO CUSTOMER_PHONE (Customer_ID, Customer_Mob_No) VALUES (%s, %s)", (cid, phone))
            conn.commit()
            return jsonify({'success': True, 'message': 'Customer updated successfully'})

        elif request.method == 'DELETE':
            data = request.json
            cursor.execute("DELETE FROM CUSTOMER WHERE Customer_ID=%s", (data['customer_id'],))
            conn.commit()
            return jsonify({'success': True, 'message': 'Customer deleted successfully'})

    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# ACCOUNT MODULE
# ==============================================================
@app.route('/api/accounts', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_accounts():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("SELECT * FROM ACCOUNT")
            accounts = cursor.fetchall()
            for acc in accounts:
                # Append correct subtype if needed
                acc['account_type'] = 'Saving' # default marker
            return jsonify({'success': True, 'data': accounts})

        elif request.method == 'POST':
            data = request.json
            acc_type = data.get('account_type', 'Saving')
            
            cursor.execute("""
                INSERT INTO ACCOUNT (Customer_ID, Withdraw, Deposit, Balance, Opening_Date, Nominee_name, Account_Status, E_KYC_Status) 
                VALUES (%s, %s, %s, %s, CURDATE(), %s, %s, 'Pending')
            """, (data['customer_id'], 0, 0, data.get('balance', 0), data.get('nominee_name', ''), data.get('account_status', 'Active')))
            
            new_acc_no = cursor.lastrowid
            
            # Specialization Insertion
            if acc_type == 'Saving':
                # Default Interest 4%, Withdrawal Limit 50,000
                cursor.execute("INSERT INTO SAVING (Account_No, Interest_Rate, Withdrawal_Limit) VALUES (%s, %s, %s)", (new_acc_no, 4.0, 50000.0))
            else:
                # Default Overdraft 10,000, Cheque Book 'Standard'
                cursor.execute("INSERT INTO CURRENT (Account_No, Overdraft_Limit, Cheque_Book_No) VALUES (%s, %s, %s)", (new_acc_no, 10000.0, 'Standard'))
            
            conn.commit()
            return jsonify({'success': True, 'message': f'Account created successfully as {acc_type}'})

        elif request.method == 'PUT':
            data = request.json
            cursor.execute("""
                UPDATE ACCOUNT SET Nominee_name=%s, Account_Status=%s, Balance=%s WHERE Account_No=%s
            """, (data.get('nominee_name', ''), data.get('account_status', ''), data.get('balance', 0), data['account_no']))
            conn.commit()
            return jsonify({'success': True, 'message': 'Account updated successfully'})

        elif request.method == 'DELETE':
            data = request.json
            cursor.execute("DELETE FROM ACCOUNT WHERE Account_No=%s", (data['account_no'],))
            conn.commit()
            return jsonify({'success': True, 'message': 'Account deleted successfully'})

    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# TRANSACTION MODULE
# ==============================================================
@app.route('/api/transactions', methods=['GET', 'POST'])
def manage_transactions():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("SELECT * FROM TRANSACTION ORDER BY Transaction_Date DESC")
            return jsonify({'success': True, 'data': cursor.fetchall()})

        elif request.method == 'POST':
            data = request.json
            acc_no = data['account_no']
            
            # 1. ENFORCEMENT: Check Account Status
            cursor.execute("SELECT Account_Status, Balance FROM ACCOUNT WHERE Account_No = %s", (acc_no,))
            row = cursor.fetchone()
            if not row:
                return jsonify({'success': False, 'error': 'Account not found'})
            
            if row['Account_Status'] == 'Inactive':
                return jsonify({'success': False, 'error': 'Account is Inactive. Transactions are not allowed.'})
            
            t_type = data['transaction_type']
            amount = float(data['amount'])
            t_mode = data.get('transaction_mode', 'Cash')
            utr_no = None

            if t_mode == 'UPI':
                import random
                utr_no = "".join([str(random.randint(0, 9)) for _ in range(12)])

            if t_type == 'Withdrawal':
                if float(row['Balance']) < amount:
                    return jsonify({'success': False, 'error': 'Insufficient balance'})
                
                new_balance = float(row['Balance']) - amount
                cursor.execute("UPDATE ACCOUNT SET Balance = %s, Withdraw = Withdraw + %s WHERE Account_No = %s", (new_balance, amount, acc_no))
            else:
                new_balance = float(row['Balance']) + amount
                cursor.execute("UPDATE ACCOUNT SET Balance = %s, Deposit = Deposit + %s WHERE Account_No = %s", (new_balance, amount, acc_no))

            cursor.execute("""
                INSERT INTO TRANSACTION (Account_No, Transaction_Type, Amount, Transaction_Mode, UTR_No, Post_Balance) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (acc_no, t_type, amount, t_mode, utr_no, new_balance))
            conn.commit()
            return jsonify({'success': True, 'message': f'Transaction successful. Mode: {t_mode}', 'utr': utr_no})

    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# UPI MODULE (SIMPLIFIED)
# ==============================================================
@app.route('/api/upi', methods=['GET', 'POST'])
def manage_upi():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        acc_no = request.args.get('account_no')

        if request.method == 'GET':
            if not acc_no:
                return jsonify({'success': False, 'error': 'Account number required'})
            
            # Verify account exists first
            cursor.execute("SELECT Account_No FROM ACCOUNT WHERE Account_No = %s", (acc_no,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Account not found'})
            
            # Get Linking Status
            cursor.execute("SELECT UPI_Link_Status FROM UPI_APP WHERE Account_No = %s", (acc_no,))
            status_row = cursor.fetchone()
            link_status = status_row['UPI_Link_Status'] if status_row else 'Not Linked'

            # Get UPI Transactions
            cursor.execute("SELECT * FROM TRANSACTION WHERE Account_No = %s AND Transaction_Mode = 'UPI' ORDER BY Transaction_Date DESC", (acc_no,))
            history = cursor.fetchall()
            
            return jsonify({'success': True, 'link_status': link_status, 'data': history})

        elif request.method == 'POST':
            data = request.json
            acc_no = data['account_no']
            new_status = data['upi_link_status']

            # Verify account exists before updating link status
            cursor.execute("SELECT Account_No FROM ACCOUNT WHERE Account_No = %s", (acc_no,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Account not found'})

            cursor.execute("""
                INSERT INTO UPI_APP (Account_No, UPI_Link_Status) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE UPI_Link_Status = %s
            """, (acc_no, new_status, new_status))
            conn.commit()
            return jsonify({'success': True, 'message': 'UPI link status updated'})

    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# LOAN MODULE
# ==============================================================
@app.route('/api/loans', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_loans():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("SELECT * FROM LOAN")
            return jsonify({'success': True, 'data': cursor.fetchall()})

        elif request.method == 'POST':
            data = request.json
            cust_id = data['customer_id']
            
            # 2. ENFORCEMENT: Must have at least one Active account
            cursor.execute("SELECT Account_Status FROM ACCOUNT WHERE Customer_ID = %s", (cust_id,))
            accounts = cursor.fetchall()
            
            if not accounts:
                return jsonify({'success': False, 'error': 'Customer has no accounts. Loan cannot be processed.'})
            
            active_found = any(acc['Account_Status'] == 'Active' for acc in accounts)
            if not active_found:
                return jsonify({'success': False, 'error': 'Customer has no active accounts. Loan processing blocked.'})
            
            cibil = int(data.get('cibil_score', 0))
            if cibil >= 700:
                loan_status = 'Approved'
            elif cibil >= 600:
                loan_status = 'Pending'
            else:
                loan_status = 'Rejected'
                
            cursor.execute("""
                INSERT INTO LOAN (Customer_id, Loan_Amount, Cibil_Score, Interest_Rate, Loan_Status) 
                VALUES (%s, %s, %s, %s, %s)
            """, (data['customer_id'], data['loan_amount'], cibil, data.get('interest_rate', 8.5), loan_status))
            conn.commit()
            return jsonify({'success': True, 'message': 'Loan applied successfully'})

        elif request.method == 'PUT':
            data = request.json
            cursor.execute("UPDATE LOAN SET Loan_Status=%s WHERE Loan_No=%s", (data['loan_status'], data['loan_no']))
            conn.commit()
            return jsonify({'success': True, 'message': 'Loan updated'})

        elif request.method == 'DELETE':
            data = request.json
            cursor.execute("DELETE FROM LOAN WHERE Loan_No=%s", (data['loan_no'],))
            conn.commit()
            return jsonify({'success': True, 'message': 'Loan deleted'})

    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# PAYMENT (EMI) MODULE
# ==============================================================
@app.route('/api/payments', methods=['GET', 'POST', 'DELETE'])
def manage_payments():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'GET':
            cursor.execute("SELECT * FROM PAYMENT")
            return jsonify({'success': True, 'data': cursor.fetchall()})

        elif request.method == 'POST':
            data = request.json
            l_no = data['loan_no']
            paid = float(data['paid_amount'])

            # Verify Loan Status first
            cursor.execute("SELECT Loan_Amount, Loan_Status FROM LOAN WHERE Loan_No = %s", (l_no,))
            loan_row = cursor.fetchone()
            if not loan_row:
                return jsonify({'success': False, 'error': 'Loan record not found'})
            
            if loan_row['Loan_Status'] != 'Approved':
                # User specifically requested: "Customer loan status is Pending ore Rejected"
                return jsonify({'success': False, 'error': f"Customer loan status is {loan_row['Loan_Status']}"})

            loan_amount = float(loan_row['Loan_Amount'])
            cursor.execute("SELECT SUM(paid_amt) as total_paid FROM PAYMENT WHERE Loan_no = %s", (l_no,))
            paid_row = cursor.fetchone()
            total_paid = float(paid_row['total_paid'] or 0)

            pending = loan_amount - total_paid - paid

            cursor.execute("""
                INSERT INTO PAYMENT (Loan_no, paid_amt, pending_amt, Payment_date) 
                VALUES (%s, %s, %s, CURDATE())
            """, (l_no, paid, pending))
            conn.commit()
            return jsonify({'success': True, 'message': 'Payment recorded'})

        elif request.method == 'DELETE':
            data = request.json
            cursor.execute("DELETE FROM PAYMENT WHERE Payment_no=%s", (data['payment_no'],))
            conn.commit()
            return jsonify({'success': True, 'message': 'Payment deleted'})
            
    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected():
            cursor.close()
            conn.close()

# ==============================================================
# ATM MODULE (SIMPLIFIED)
# ==============================================================
@app.route('/api/atms', methods=['GET', 'POST'])
def manage_atms():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        acc_no = request.args.get('account_no')

        if request.method == 'GET':
            if not acc_no:
                return jsonify({'success': False, 'error': 'Account number required'})

            # Verify account exists first
            cursor.execute("SELECT Account_No FROM ACCOUNT WHERE Account_No = %s", (acc_no,))
            if not cursor.fetchone():
                return jsonify({'success': False, 'error': 'Account not found'})

            # Get ATM Status
            cursor.execute("SELECT ATM_Status FROM ATM WHERE Account_No = %s", (acc_no,))
            status_row = cursor.fetchone()
            atm_status = status_row['ATM_Status'] if status_row else 'Inactive'

            # Get ATM Transactions
            cursor.execute("SELECT * FROM TRANSACTION WHERE Account_No = %s AND Transaction_Mode = 'ATM' ORDER BY Transaction_Date DESC", (acc_no,))
            history = cursor.fetchall()

            return jsonify({'success': True, 'atm_status': atm_status, 'data': history})

        elif request.method == 'POST':
            data = request.json
            acc_no = data['account_no']
            new_status = data['atm_status']

            cursor.execute("""
                INSERT INTO ATM (Account_No, ATM_Status) 
                VALUES (%s, %s) 
                ON DUPLICATE KEY UPDATE ATM_Status = %s
            """, (acc_no, new_status, new_status))
            conn.commit()
            return jsonify({'success': True, 'message': 'ATM status updated'})

    except Exception as e:
        if 'conn' in locals() and conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

# ==============================================================
# EMPLOYEE MODULE
# ==============================================================
@app.route('/api/employees', methods=['GET', 'POST', 'PUT', 'DELETE'])
def manage_employees():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if request.method == 'GET':
            cursor.execute("""
                SELECT e.*, GROUP_CONCAT(ep.Emp_Mobile_No) as mobile_number 
                FROM EMPLOYEE e 
                LEFT JOIN EMPLOYEE_PHONE ep ON e.Emp_id = ep.Emp_id 
                GROUP BY e.Emp_id
            """)
            return jsonify({'success': True, 'data': cursor.fetchall()})
        elif request.method == 'POST':
            data = request.json
            full_name = f"{data['first_name']} {data['last_name']}"
            cursor.execute("""INSERT INTO EMPLOYEE (Emp_name, Designation, Salary, city, street, Street_no) 
                              VALUES (%s, %s, %s, %s, %s, %s)""",
                           (full_name, data['designation'], data['salary'], data.get('city',''), data.get('street',''), data.get('street_no','')))
            emp_id = cursor.lastrowid
            
            if data.get('mobile_number'):
                cursor.execute("INSERT INTO EMPLOYEE_PHONE (Emp_id, Emp_Mobile_No) VALUES (%s, %s)", (emp_id, data['mobile_number']))
                
            if data['designation'] == 'Senior Manager':
                cursor.execute("INSERT INTO SENIOR_MANAGER (Emp_id, Annual_Bonus_Plan) VALUES (%s, 'Standard Bonus')", (emp_id,))
            elif data['designation'] == 'Manager':
                cursor.execute("INSERT INTO MANAGER (Emp_id, Budget_Authority) VALUES (%s, 500000)", (emp_id,))
            elif data['designation'] == 'Cashier':
                cursor.execute("INSERT INTO CASHIER (Emp_id, Shift_Code) VALUES (%s, 'Morning')", (emp_id,))

            conn.commit()
            return jsonify({'success': True, 'message': 'Employee added and placed into Subtype automatically'})
        elif request.method == 'PUT':
            data = request.json
            full_name = f"{data['first_name']} {data['last_name']}"
            cursor.execute("""UPDATE EMPLOYEE SET Emp_name=%s, Designation=%s, Salary=%s, city=%s, street=%s, Street_no=%s 
                              WHERE Emp_id=%s""",
                           (full_name, data['designation'], data['salary'], data.get('city',''), data.get('street',''), data.get('street_no',''), data['emp_id']))
                           
            cursor.execute("DELETE FROM EMPLOYEE_PHONE WHERE Emp_id=%s", (data['emp_id'],))
            if data.get('mobile_number'):
                cursor.execute("INSERT INTO EMPLOYEE_PHONE (Emp_id, Emp_Mobile_No) VALUES (%s, %s)", (data['emp_id'], data['mobile_number']))
            
            conn.commit()
            return jsonify({'success': True, 'message': 'Employee updated'})
        elif request.method == 'DELETE':
            data = request.json
            cursor.execute("DELETE FROM EMPLOYEE WHERE Emp_id=%s", (data['emp_id'],))
            conn.commit()
            return jsonify({'success': True, 'message': 'Employee deleted'})
    except Exception as e:
        if conn and conn.is_connected(): conn.rollback()
        return jsonify({'success': False, 'error': handle_db_error(e)})
    finally:
        if conn and conn.is_connected(): cursor.close(); conn.close()

if __name__ == '__main__':
    app.run(debug=True, port=5000)
