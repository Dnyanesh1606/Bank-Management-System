document.addEventListener('DOMContentLoaded', () => {
    
    // View Navigation Logic
    const navBtns = document.querySelectorAll('.nav-btn');
    const views = document.querySelectorAll('.view-section');

    function switchView(targetId) {
        navBtns.forEach(b => b.classList.remove('active'));
        views.forEach(v => v.classList.remove('active'));
        
        const btn = document.querySelector(`[data-target="${targetId}"]`);
        if(btn) btn.classList.add('active');
        const view = document.getElementById(targetId);
        if(view) view.classList.add('active');

        // Load data based on view
        if(targetId === 'dashboard-view') window.loadDashboardStats();
        if(targetId === 'customer-view') window.loadCustomers();
        if(targetId === 'account-view') window.loadAccounts();
        if(targetId === 'transaction-view') window.loadTransactions();
        if(targetId === 'upi-view') { /* Handled by manual search */ }
        if(targetId === 'loan-view') window.loadLoans();
        if(targetId === 'payment-view') window.loadPayments();
        if(targetId === 'employee-view') window.loadEmployees();
        if(targetId === 'admin-view') window.loadBranches();
        if(targetId === 'atm-view') { /* Handled by manual search */ }
    }

    navBtns.forEach(btn => {
        btn.addEventListener('click', () => switchView(btn.getAttribute('data-target')));
    });

    // ==========================================
    // generic API Fetcher (Disabled Cache)
    // ==========================================
    window.apiCall = async function(endpoint, method = 'GET', data = null) {
        const options = { 
            method, 
            headers: { 'Content-Type': 'application/json' },
            cache: 'no-store' // Fixes the issue where data updates require manual refresh!
        };
        if (data) options.body = JSON.stringify(data);
        try {
            const res = await fetch(endpoint, options);
            return await res.json();
        } catch (err) {
            showToast('Network error: ' + err.message, 'error');
            return null;
        }
    }

    // ==========================================
    // Fetch and Populate Logic (Made global)
    // ==========================================

    window.loadDashboardStats = async function() {
        const res = await apiCall('/api/dashboard_stats');
        if(res && res.success) {
            document.getElementById('stat-customers').textContent = res.customers;
            document.getElementById('stat-accounts').textContent = res.accounts;
            document.getElementById('stat-transactions').textContent = res.transactions;
        }
    }

    window.loadCustomers = async function() {
        const res = await apiCall('/api/customers');
        const tbody = document.querySelector('#table-customer tbody');
        tbody.innerHTML = '';
        if(res && res.success) {
            res.data.forEach(c => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>CUST${c.Customer_ID}</td>
                    <td>${c.F_Name} ${c.L_Name}</td>
                    <td>${c.mobile_number || '-'}</td>
                    <td>${c.E_mail || ''}</td>
                    <td>${c.city}</td>
                    <td>
                        <button class="btn-edit" onclick='editCustomer(${JSON.stringify(c)})'><i class="fa fa-pen"></i></button>
                        <button class="btn-danger" onclick='deleteRecord("/api/customers", {"customer_id": ${c.Customer_ID}}, window.loadCustomers)'><i class="fa fa-trash"></i></button>
                    </td>`;
                tbody.appendChild(tr);
            });
        }
    }
    
    window.editCustomer = (c) => {
        document.getElementById('cust_id').value = c.Customer_ID;
        document.querySelector('#customerForm [name="first_name"]').value = c.F_Name;
        document.querySelector('#customerForm [name="last_name"]').value = c.L_Name;
        document.querySelector('#customerForm [name="mobile_number"]').value = c.mobile_number || '';
        document.querySelector('#customerForm [name="email"]').value = c.E_mail || '';
        document.querySelector('#customerForm [name="city"]').value = c.city || '';
        document.querySelector('#customerForm [name="street"]').value = c.street || '';
        document.querySelector('#customerForm [name="street_no"]').value = c.Street_no || '';
        document.getElementById('btn-save-cust').innerText = 'Update Customer';
        window.scrollTo(0,0);
    };

    window.loadAccounts = async function() {
        const res = await apiCall('/api/accounts');
        const tbody = document.querySelector('#table-account tbody');
        tbody.innerHTML = '';
        if(res && res.success) {
            res.data.forEach(a => {
                const tr = document.createElement('tr');
                // Pad account to 5 digits visually
                const accFormatted = String(a.Account_No).padStart(5, '0');
                tr.innerHTML = `
                    <td>${accFormatted}</td>
                    <td>CUST${a.Customer_ID}</td>
                    <td>₹${a.Balance}</td>
                    <td>${a.Account_Status}</td>
                    <td>
                        <button class="btn-edit" onclick='editAccount(${JSON.stringify(a)})'><i class="fa fa-pen"></i></button>
                        <button class="btn-danger" onclick='deleteRecord("/api/accounts", {"account_no": ${a.Account_No}}, window.loadAccounts)'><i class="fa fa-trash"></i></button>
                    </td>`;
                tbody.appendChild(tr);
            });
        }
    }

    window.editAccount = (a) => {
        document.getElementById('acc_id').value = a.Account_No;
        document.querySelector('#accountForm [name="customer_id"]').value = a.Customer_ID;
        document.querySelector('#accountForm [name="customer_id"]').disabled = true; // Can't change ID easily
        document.querySelector('#accountForm [name="balance"]').value = a.Balance;
        document.querySelector('#accountForm [name="nominee_name"]').value = a.Nominee_name || '';
        document.querySelector('#accountForm [name="account_status"]').value = a.Account_Status;
        document.getElementById('btn-save-acc').innerText = 'Update Account';
        window.scrollTo(0,0);
    };

    window.loadTransactions = async function() {
        const res = await apiCall('/api/transactions');
        window._allTransactions = res && res.success ? res.data : [];
        applyTransactionFilters();
    }

    window.applyTransactionFilters = function() {
        const typeFilter = document.getElementById('filter-transaction-type').value;
        const tbody = document.querySelector('#table-transaction tbody');
        tbody.innerHTML = '';
        
        const filtered = (window._allTransactions || []).filter(t => {
            if (typeFilter !== 'All' && t.Transaction_Type !== typeFilter) return false;
            return true;
        });

        filtered.forEach(t => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>TXN${t.Transaction_ID}</td>
                <td>${String(t.Account_No).padStart(5, '0')}</td>
                <td>${t.Transaction_Type}</td>
                <td>₹${t.Amount}</td>
                <td>₹${t.Post_Balance || '-'}</td>
                <td><span class="badge badge-${t.Transaction_Mode.toLowerCase()}">${t.Transaction_Mode}</span></td>
                <td style="font-family: monospace;">${t.UTR_No || '-'}</td>
                <td>${new Date(t.Transaction_Date).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'short' })}</td>
            `;
            tbody.appendChild(tr);
        });
    }

    // ==========================================
    // UPI Logic (Simplified)
    // ==========================================
    window.fetchUPIStatus = async function() {
        const accNo = document.getElementById('upi-search-acc').value;
        if(!accNo) return showToast('Please enter account number', 'error');

        const res = await apiCall(`/api/upi?account_no=${accNo}`);
        const statusEl = document.getElementById('upi-current-status');
        const tbody = document.querySelector('#table-upi tbody');
        tbody.innerHTML = '';

        if(res && res.success) {
            document.getElementById('upi-status-group').style.display = 'block';
            statusEl.textContent = res.link_status;
            statusEl.className = `badge ${res.link_status === 'Linked' ? 'badge-active' : 'badge-inactive'}`;
            
            const typeFilter = document.getElementById('filter-upi-type').value;
            const filtered = res.data.filter(t => {
                if (typeFilter !== 'All' && t.Transaction_Type !== typeFilter) return false;
                return true;
            });

            filtered.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>TXN${u.Transaction_ID}</td>
                    <td>${String(u.Account_No).padStart(5, '0')}</td>
                    <td>${u.Transaction_Type}</td>
                    <td>₹${u.Amount}</td>
                    <td style="font-family: monospace;">${u.UTR_No}</td>
                    <td>${new Date(u.Transaction_Date).toLocaleDateString()}</td>
                `;
                tbody.appendChild(tr);
            });
            if(filtered.length === 0) tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;">No matching UPI transactions found</td></tr>';
        } else {
            document.getElementById('upi-status-group').style.display = 'none';
            showToast(res ? res.error : 'Failed to fetch UPI status', 'error');
        }
    }

    window.toggleUPILink = async function() {
        const accNo = document.getElementById('upi-search-acc').value;
        if(!accNo) return showToast('Please search for an account first', 'error');

        const currentStatus = document.getElementById('upi-current-status').textContent;
        const newStatus = (currentStatus === 'Linked') ? 'Not Linked' : 'Linked';

        const res = await apiCall('/api/upi', 'POST', { account_no: accNo, upi_link_status: newStatus });
        if(res && res.success) {
            showToast(res.message, 'success');
            fetchUPIStatus();
        }
    }

    window.loadLoans = async function() {
        const res = await apiCall('/api/loans');
        const tbody = document.querySelector('#table-loan tbody');
        tbody.innerHTML = '';
        if(res && res.success) {
            res.data.forEach(l => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>LN${l.Loan_No}</td>
                    <td>CUST${l.Customer_id}</td>
                    <td>₹${l.Loan_Amount}</td>
                    <td>${l.Interest_Rate}%</td>
                    <td>${l.Loan_Status}</td>
                    <td>
                        <button class="btn-edit" onclick='editLoan(${JSON.stringify(l)})'><i class="fa fa-pen"></i></button>
                        <button class="btn-danger" onclick='deleteRecord("/api/loans", {"loan_no": ${l.Loan_No}}, window.loadLoans)'><i class="fa fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
    
    window.editLoan = (l) => {
        document.getElementById('ln_id').value = l.Loan_No;
        document.querySelector('#loanForm [name="customer_id"]').value = l.Customer_id;
        document.querySelector('#loanForm [name="loan_amount"]').value = l.Loan_Amount;
        document.querySelector('#loanForm [name="cibil_score"]').value = l.Cibil_Score || '';
        document.querySelector('#loanForm [name="interest_rate"]').value = l.Interest_Rate;
        document.getElementById('btn-save-loan').innerText = 'Update Loan';
        window.scrollTo(0,0);
    }

    window.loadPayments = async function() {
        const res = await apiCall('/api/payments');
        const tbody = document.querySelector('#table-payment tbody');
        tbody.innerHTML = '';
        if(res && res.success) {
            res.data.forEach(p => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>PMT${p.Payment_no}</td>
                    <td>LN${p.Loan_no}</td>
                    <td>₹${p.paid_amt}</td>
                    <td>₹${p.pending_amt}</td>
                    <td>${new Date(p.Payment_date).toLocaleDateString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium' })}</td>
                    <td>
                        <button class="btn-danger" onclick='deleteRecord("/api/payments", {"payment_no": ${p.Payment_no}}, window.loadPayments)'><i class="fa fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    }

    window.loadEmployees = async function() {
        const res = await apiCall('/api/employees');
        const tbody = document.querySelector('#table-employee tbody');
        tbody.innerHTML = '';
        if(res && res.success) {
            res.data.forEach(e => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>EMP${e.Emp_id}</td>
                    <td>${e.Emp_name}</td>
                    <td>${e.Designation || 'N/A'}</td>
                    <td>₹${e.Salary}</td>
                    <td>${e.mobile_number || 'N/A'}</td>
                    <td>
                        <button class="btn-edit" onclick='editEmployee(${JSON.stringify(e)})'><i class="fa fa-pen"></i></button>
                        <button class="btn-danger" onclick='deleteRecord("/api/employees", {"emp_id": ${e.Emp_id}}, window.loadEmployees)'><i class="fa fa-trash"></i></button>
                    </td>
                `;
                tbody.appendChild(tr);
            });
        }
    }
    
    window.editEmployee = (emp) => {
        document.getElementById('emp_id').value = emp.Emp_id;
        let names = emp.Emp_name.split(' ');
        document.querySelector('#employeeForm [name="first_name"]').value = names[0];
        document.querySelector('#employeeForm [name="last_name"]').value = names.slice(1).join(' ');
        document.querySelector('#employeeForm [name="designation"]').value = emp.Designation || 'Manager';
        document.querySelector('#employeeForm [name="salary"]').value = emp.Salary;
        document.querySelector('#employeeForm [name="mobile_number"]').value = emp.mobile_number ? emp.mobile_number.split(',')[0] : '';
        document.querySelector('#employeeForm [name="city"]').value = emp.city || '';
        document.querySelector('#employeeForm [name="street"]').value = emp.street || '';
        document.querySelector('#employeeForm [name="street_no"]').value = emp.Street_no || '';
        document.getElementById('btn-save-emp').innerText = 'Update Employee';
        window.scrollTo(0,0);
    }
    
    // ==========================================
    // ATM Logic (Simplified)
    // ==========================================
    window.fetchATMStatus = async function() {
        const accNo = document.getElementById('atm-search-acc').value;
        const typeFilter = document.getElementById('filter-atm-type').value;
        if(!accNo) return showToast('Please enter account number', 'error');

        const res = await apiCall(`/api/atms?account_no=${accNo}`);
        const statusEl = document.getElementById('atm-current-status');
        const tbody = document.querySelector('#table-atm tbody');
        tbody.innerHTML = '';

        if(res && res.success) {
            document.getElementById('atm-status-group').style.display = 'block';
            statusEl.textContent = res.atm_status;
            statusEl.className = `badge ${res.atm_status === 'Active' ? 'badge-active' : 'badge-inactive'}`;
            
            const filtered = res.data.filter(t => {
                if (typeFilter !== 'All' && t.Transaction_Type !== typeFilter) return false;
                return true;
            });

            filtered.forEach(u => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td>TXN${u.Transaction_ID}</td>
                    <td>${String(u.Account_No).padStart(5, '0')}</td>
                    <td>${u.Transaction_Type}</td>
                    <td>₹${u.Amount}</td>
                    <td>${new Date(u.Transaction_Date).toLocaleDateString()}</td>
                `;
                tbody.appendChild(tr);
            });
            if(filtered.length === 0) tbody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No ATM transactions found for this account</td></tr>';
        } else {
            document.getElementById('atm-status-group').style.display = 'none';
            showToast(res ? res.error : 'Failed to fetch ATM status', 'error');
        }
    }

    window.toggleATMStatus = async function() {
        const accNo = document.getElementById('atm-search-acc').value;
        if(!accNo) return showToast('Please search for an account first', 'error');

        const currentStatus = document.getElementById('atm-current-status').textContent;
        const newStatus = (currentStatus === 'Active') ? 'Inactive' : 'Active';

        const res = await apiCall('/api/atms', 'POST', { account_no: accNo, atm_status: newStatus });
        if(res && res.success) {
            showToast(res.message, 'success');
            fetchATMStatus();
        }
    }

    // ==========================================
    // Delete Handler
    // ==========================================
    window.deleteRecord = async (endpoint, data, reloadCallback) => {
        if(!confirm("Are you sure you want to delete this record?")) return;
        const res = await apiCall(endpoint, 'DELETE', data);
        if(res && res.success) {
            showToast(res.message, 'success');
            reloadCallback();
        } else {
            showToast(res ? res.error : 'Deletion failed', 'error');
        }
    }

    // ==========================================
    // Submit Handlers
    // ==========================================
    function setupForm(formId, endpoint, reloadCallback, idField = null) {
        const form = document.getElementById(formId);
        if(!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            const data = Object.fromEntries(formData.entries());
            
            // Check if it's update (PUT) or create (POST)
            let method = 'POST';
            if(idField && data[idField]) {
                method = 'PUT';
            }

            const res = await apiCall(endpoint, method, data);
            if(res && res.success) {
                showToast(res.message, 'success');
                form.reset();
                if(idField && form.elements[idField]) form.elements[idField].value = '';
                
                // Form specific resets
                if(formId === 'customerForm') document.getElementById('btn-save-cust').innerText = 'Save Customer';
                if(formId === 'accountForm') {
                    document.getElementById('btn-save-acc').innerText = 'Open Account';
                    document.querySelector('#accountForm [name="customer_id"]').disabled = false;
                }
                if(formId === 'loanForm') document.getElementById('btn-save-loan').innerText = 'Save Loan';
                if(formId === 'employeeForm') document.getElementById('btn-save-emp').innerText = 'Save Employee';

                reloadCallback();
            } else {
                showToast(res ? res.error : 'Operation failed', 'error');
            }
        });
    }

    setupForm('customerForm', '/api/customers', window.loadCustomers, 'customer_id');
    setupForm('accountForm', '/api/accounts', window.loadAccounts, 'account_no');
    setupForm('transactionForm', '/api/transactions', window.loadTransactions);
    setupForm('loanForm', '/api/loans', window.loadLoans, 'loan_no');
    setupForm('paymentForm', '/api/payments', window.loadPayments);
    setupForm('employeeForm', '/api/employees', window.loadEmployees, 'emp_id');

    // ==========================================
    // Table Search Helper
    // ==========================================
    window.filterTable = (tableId, query) => {
        const lowerQ = query.toLowerCase();
        const trs = document.querySelectorAll(`#${tableId} tbody tr`);
        trs.forEach(tr => {
            const text = tr.innerText.toLowerCase();
            tr.style.display = text.includes(lowerQ) ? '' : 'none';
        });
    }

    // Toast Notification
    window.showToast = function(message, type = 'success') {
        const toast = document.getElementById('toast');
        toast.textContent = message;
        toast.className = 'toast show ' + type;
        setTimeout(() => toast.className = 'toast', 3000);
    }
    
    // Live Clock setup
    setInterval(() => {
        const clock = document.getElementById('live-clock');
        if(clock) {
            clock.innerText = new Date().toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', dateStyle: 'medium', timeStyle: 'medium' }) + ' (IST)';
        }
    }, 1000);

    // Initialize first view
    window.loadDashboardStats();
});
