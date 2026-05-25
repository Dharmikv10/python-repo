import json
import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from tabulate import tabulate


DATA_FILE = "data.json"


class SplitwisePremium:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ Splitwise Premium - Group Expense Tracker")
        self.root.geometry("1200x800")
        self.root.configure(bg='#0f172a')
        self.root.resizable(True, True)
        
        self.data = self.load_data()
        self.setup_modern_ui()
        self.refresh_dashboard()
    
    def load_data(self):
        default = {"group": [], "expenses": [], "settlements": []}
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    return json.load(f)
            except:
                pass
        return default
    
    def save_data(self):
        with open(DATA_FILE, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def setup_modern_ui(self):
        # Title bar
        header_frame = tk.Frame(self.root, bg='#1e293b', height=80)
        header_frame.pack(fill='x', pady=(0, 20))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="✨ SPLITWISE", font=('Segoe UI', 28, 'bold'), 
                bg='#1e293b', fg='#60a5fa').pack(side='left', padx=30, pady=20)
        tk.Label(header_frame, text="Track expenses with friends 👥💸", 
                font=('Segoe UI', 14), bg='#1e293b', fg='#94a3b8').pack(side='left', padx=(0, 50), pady=25)
        
        # Stats bar
        self.stats_frame = tk.Frame(self.root, bg='#1e40af', height=60)
        self.stats_frame.pack(fill='x', pady=(0, 20))
        self.stats_frame.pack_propagate(False)
        
        # Main container
        main_frame = tk.Frame(self.root, bg='#0f172a')
        main_frame.pack(fill='both', expand=True, padx=30, pady=10)
        
        # Left buttons
        left_panel = tk.Frame(main_frame, bg='#111827', relief='flat', bd=0, width=280)
        left_panel.pack(side='left', fill='y', padx=(0, 25))
        left_panel.pack_propagate(False)
        
        self.setup_buttons(left_panel)
        
        # Right dashboard
        right_panel = tk.Frame(main_frame, bg='#1e293b', relief='flat', bd=1)
        right_panel.pack(side='right', fill='both', expand=True)
        
        tk.Label(right_panel, text="📊 Dashboard", font=('Segoe UI', 20, 'bold'), 
                bg='#1e293b', fg='#f1f5f9').pack(pady=25)
        
        # Scrollable text area
        text_frame = tk.Frame(right_panel, bg='#1e293b')
        text_frame.pack(fill='both', expand=True, padx=25, pady=(0, 25))
        
        self.dashboard_text = tk.Text(text_frame, bg='#0f172a', fg='#f1f5f9',
                                     font=('Consolas', 11), relief='flat', bd=0, wrap='word',
                                     insertbackground='#60a5fa', selectbackground='#3b82f6')
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=self.dashboard_text.yview)
        self.dashboard_text.configure(yscrollcommand=scrollbar.set)
        
        self.dashboard_text.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def setup_buttons(self, parent):
        buttons = [
            ("👥 Manage Group", self.manage_group),
            ("💸 Add Expense", self.add_expense),
            ("📊 Refresh Dashboard", self.refresh_dashboard),
            ("🔄 Settle Up", self.settle_up),
            ("📋 History", self.view_history),
            ("🗑️ Reset Data", self.reset_all)
        ]
        
        for text, cmd in buttons:
            btn = tk.Button(parent, text=text, command=cmd,
                           font=('Segoe UI', 12, 'bold'), bg='#3b82f6', fg='white',
                           activebackground='#2563eb', relief='flat', bd=0,
                           width=18, height=2, cursor='hand2')
            btn.pack(pady=12, padx=25, fill='x')
            
            # Hover effects
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg='#2563eb'))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg='#3b82f6'))
    
    def update_stats(self):
        balances = self.calculate_balances()
        # FIXED: Positive balance = gets money, negative = owes money
        total_due = sum(max(0, b) for b in balances.values())  # Gets money (positive)
        total_owe = sum(max(0, -b) for b in balances.values())  # Owes money (negative)
        
        for widget in self.stats_frame.winfo_children():
            widget.destroy()
        
        tk.Label(self.stats_frame, text=f"💳 Total Owed: ₹{total_owe:.0f}", 
                font=('Segoe UI', 14, 'bold'), bg='#1e40af', fg='white').pack(side='left', padx=50, pady=15)
        tk.Label(self.stats_frame, text=f"💰 Total Due: ₹{total_due:.0f}", 
                font=('Segoe UI', 14, 'bold'), bg='#1e40af', fg='white').pack(side='left', padx=50, pady=15)
        tk.Label(self.stats_frame, text=f"👥 {len(self.data['group'])} Members", 
                font=('Segoe UI', 14, 'bold'), bg='#1e40af', fg='white').pack(side='right', padx=50, pady=15)
    
    def calculate_balances(self):
        balances = {member: 0.0 for member in self.data['group']}
        
        for exp in self.data['expenses']:
            total = float(exp['total'])
            shares = {k: float(v) for k, v in exp['shares'].items()}
            total_share = sum(shares.values())
            
            # Payer credited full amount
            if exp['payer'] in balances:
                balances[exp['payer']] += total
            
            # Participants owe their share
            for member, share in shares.items():
                if member in balances:
                    balances[member] -= total * (share / total_share if total_share > 0 else 0)
        
        # Settlements
        for sett in self.data['settlements']:
            fr, to = sett['from'], sett['to']
            amt = float(sett['amount'])
            if fr in balances:
                balances[fr] += amt
            if to in balances:
                balances[to] -= amt
        
        return {k: round(v, 2) for k, v in balances.items()}
    
    def refresh_dashboard(self):
        self.update_stats()
        balances = self.calculate_balances()
        
        table_data = []
        for name, balance in sorted(balances.items(), key=lambda x: x[1], reverse=True):
            # FIXED: Positive = GETS money, Negative = OWES money
            if balance > 0.01:
                status = f"🟢 GETS ₹{balance:.0f}"
                emoji = "🟢"
            elif balance < -0.01:
                status = f"🔴 OWES ₹{-balance:.0f}"
                emoji = "🔴"
            else:
                status = "⚪ SETTLED"
                emoji = "⚪"
            table_data.append([emoji, name, f"₹{balance:+.0f}", status])
        
        table_str = "📊 GROUP BALANCES\n\n" + tabulate(
            table_data, headers=[" ", "👤 Name", "💰 Balance", "📈 Status"], tablefmt="grid"
        )
        
        self.dashboard_text.delete('1.0', tk.END)
        self.dashboard_text.insert('1.0', table_str)
    
    def create_modal(self, title, width, height):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(f"{width}x{height}")
        win.configure(bg='#0f172a')
        win.transient(self.root)
        win.grab_set()
        win.resizable(False, False)
        return win
    
    def manage_group(self):
        win = self.create_modal("👥 Manage Group", 500, 600)
        tk.Label(win, text="👥 Your Group Members", font=('Segoe UI', 18, 'bold'), 
                bg='#0f172a', fg='#60a5fa').pack(pady=25)
        
        # Listbox
        list_frame = tk.Frame(win, bg='#0f172a')
        list_frame.pack(pady=20, padx=40, fill='both', expand=True)
        
        listbox = tk.Listbox(list_frame, font=('Segoe UI', 12), bg='#1e293b', fg='white',
                            selectbackground='#3b82f6', height=15)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        for member in sorted(self.data['group']):
            listbox.insert(tk.END, member)
        
        btn_frame = tk.Frame(win, bg='#0f172a')
        btn_frame.pack(pady=30)
        
        def add_member():
            name = simpledialog.askstring("➕ Add Member", "Enter name:", parent=win)
            if name:
                name = name.strip().title()
                if name and name not in self.data['group']:
                    self.data['group'].append(name)
                    self.save_data()
                    listbox.insert(tk.END, name)
                    messagebox.showinfo("✅ Added", f"{name} joined!", parent=win)
        
        def remove_member():
            sel = listbox.curselection()
            if sel:
                name = listbox.get(sel[0])
                self.data['group'].remove(name)
                self.save_data()
                listbox.delete(sel[0])
                messagebox.showinfo("✅ Removed", f"{name} left!", parent=win)
                self.refresh_dashboard()
        
        tk.Button(btn_frame, text="➕ ADD", command=add_member, bg='#10b981', fg='white',
                 font=('Segoe UI', 12, 'bold'), width=12).pack(side='left', padx=15)
        tk.Button(btn_frame, text="➖ REMOVE", command=remove_member, bg='#ef4444', fg='white',
                 font=('Segoe UI', 12, 'bold'), width=12).pack(side='left', padx=15)
    
    def add_expense(self):
        if not self.data['group']:
            messagebox.showwarning("⚠️", "👥 Add group members first!", parent=self.root)
            return
        
        win = self.create_modal("💸 Add Expense", 550, 750)
        tk.Label(win, text="💸 Record New Expense", font=('Segoe UI', 20, 'bold'), 
                bg='#0f172a', fg='#60a5fa').pack(pady=30)
        
        # Total
        tk.Label(win, text="💰 Total Amount (₹)", font=('Segoe UI', 12, 'bold'), 
                bg='#0f172a', fg='#f1f5f9').pack(pady=(0,5))
        total_var = tk.StringVar(value="1200")
        total_entry = tk.Entry(win, textvariable=total_var, font=('Segoe UI', 14), width=20, 
                              bg='#1e293b', fg='white', relief='flat', insertbackground='#60a5fa')
        total_entry.pack(pady=(0,25))
        
        # Payer
        tk.Label(win, text="👤 Paid By", font=('Segoe UI', 12, 'bold'), 
                bg='#0f172a', fg='#f1f5f9').pack(pady=(0,5))
        payer_var = tk.StringVar()
        payer_combo = ttk.Combobox(win, textvariable=payer_var, values=self.data['group'], 
                                  font=('Segoe UI', 12), width=17, state='readonly')
        payer_combo.pack(pady=(0,25))
        
        # Split type
        tk.Label(win, text="📊 Split Type", font=('Segoe UI', 12, 'bold'), 
                bg='#0f172a', fg='#f1f5f9').pack(pady=(0,5))
        split_var = tk.StringVar(value="equal")
        tk.Radiobutton(win, text="🔄 Equal Split", variable=split_var, value="equal", 
                      bg='#0f172a', fg='white', selectcolor='#1e293b', font=('Segoe UI', 11)).pack()
        tk.Radiobutton(win, text="⚖️ Unequal (%)", variable=split_var, value="unequal", 
                      bg='#0f172a', fg='white', selectcolor='#1e293b', font=('Segoe UI', 11)).pack(pady=(0,20))
        
        # Shares
        shares_frame = tk.LabelFrame(win, text="📈 Shares (leave blank to skip)", font=('Segoe UI', 10, 'bold'),
                                   bg='#0f172a', fg='#94a3b8', bd=1, relief='flat')
        shares_frame.pack(pady=10, padx=40, fill='x')
        self.share_vars = {}
        
        def update_shares(*args):
            for w in shares_frame.winfo_children()[1:]:  # Skip label frame title
                w.destroy()
            payer = payer_var.get()
            for member in self.data['group']:
                if member == payer: continue
                frame = tk.Frame(shares_frame, bg='#0f172a')
                frame.pack(fill='x', pady=3, padx=10)
                tk.Label(frame, text=f"{member}:", width=12, bg='#0f172a', fg='white').pack(side='left')
                var = tk.StringVar()
                entry = tk.Entry(frame, textvariable=var, width=10, bg='#1e293b', fg='white', 
                                relief='flat', font=('Segoe UI', 10))
                entry.pack(side='right', padx=(0,20))
                self.share_vars[member] = var
        
        payer_var.trace('w', update_shares)
        update_shares()
        
        def submit_expense():
            try:
                total = float(total_var.get())
                payer = payer_var.get()
                if total <= 0 or not payer:
                    raise ValueError("Invalid amount or payer!")
                
                shares = {}
                total_share_pct = 0
                for member, var in self.share_vars.items():
                    pct_str = var.get().strip()
                    if pct_str:
                        pct = float(pct_str)
                        if pct <= 0:
                            continue
                        shares[member] = pct / 100
                        total_share_pct += pct
                
                if not shares:
                    raise ValueError("Add at least one share!")
                
                if split_var.get() == 'equal':
                    n = len(shares)
                    shares = {m: 1.0/n for m in shares}
                elif total_share_pct != 100:
                    raise ValueError("Unequal shares must sum to 100%!")
                
                expense = {
                    'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                    'total': total,
                    'payer': payer,
                    'shares': shares,
                    'desc': f"₹{total:.0f} - {payer} paid"
                }
                self.data['expenses'].append(expense)
                self.save_data()
                messagebox.showinfo("✅ Success!", "Expense added! 📊 Refresh dashboard.", parent=win)
                win.destroy()
            except ValueError as e:
                messagebox.showerror("❌ Error", str(e), parent=win)
            except Exception as e:
                messagebox.showerror("❌ Error", f"Unexpected: {e}", parent=win)
        
        tk.Button(win, text="💾 SAVE EXPENSE", command=submit_expense,
                 bg='#10b981', fg='white', font=('Segoe UI', 14, 'bold'), 
                 width=20, height=2, relief='flat').pack(pady=30)
    
    def settle_up(self):
        balances = self.calculate_balances()
        # FIXED: Positive balance = gets money, Negative balance = owes money
        gets = {k: v for k, v in balances.items() if v > 0.01}  # Positive: gets money
        owes = {k: -v for k, v in balances.items() if v < -0.01}  # Negative: owes money (convert to positive)
        
        if not owes or not gets:
            messagebox.showinfo("📊 All Settled", "Everyone is square! 🎉", parent=self.root)
            return
        
        # Minimal transactions (simplified greedy)
        settlements = []
        owe_list = sorted(owes.items(), key=lambda x: x[1], reverse=True)
        get_list = sorted(gets.items(), key=lambda x: x[1], reverse=True)
        
        i = j = 0
        while i < len(owe_list) and j < len(get_list):
            payer, p_amt = owe_list[i]  # Person who owes
            receiver, r_amt = get_list[j]  # Person who gets
            transfer = min(p_amt, r_amt)
            
            settlements.append((payer, receiver, transfer))
            owe_list[i] = (payer, p_amt - transfer)
            get_list[j] = (receiver, r_amt - transfer)
            
            if owe_list[i][1] < 0.01: i += 1
            if get_list[j][1] < 0.01: j += 1
        
        # Save settlements
        for payer, receiver, amt in settlements:
            self.data['settlements'].append({
                'date': datetime.now().strftime("%Y-%m-%d %H:%M"),
                'from': payer,
                'to': receiver,
                'amount': round(amt, 2)
            })
        self.save_data()
        
        # FIXED: Show correct direction (payer pays receiver)
        table_data = [[f"{fr}", f"➡️ {to}", f"₹{amt:.0f}"] for fr, to, amt in settlements]
        msg = tabulate(table_data, headers=["From", "To", "Amount"], tablefmt="grid")
        messagebox.showinfo("✅ Settled!", f"🔄 Minimal Payments:\n\n{msg}", parent=self.root)
        self.refresh_dashboard()
    
    def view_history(self):
        if not self.data['expenses'] and not self.data['settlements']:
            messagebox.showinfo("📋 Empty", "No transactions yet!", parent=self.root)
            return
        
        win = self.create_modal("📋 Transaction History", 900, 700)
        text = tk.Text(win, bg='#0f172a', fg='#f1f5f9', font=('Consolas', 10), wrap='word')
        scrollbar = ttk.Scrollbar(win, orient="vertical", command=text.yview)
        text.configure(yscrollcommand=scrollbar.set)
        text.pack(side='left', fill='both', expand=True, padx=(25,0), pady=25)
        scrollbar.pack(side='right', fill='y')
        
        history = "📋 RECENT EXPENSES\n" + "-"*60 + "\n"
        for exp in self.data['expenses'][-15:]:
            history += f"{exp['date']} | {exp['desc']}\n"
            history += f"   Payer: {exp['payer']} | Shares: { {k: f'{v:.1%}' for k,v in exp['shares'].items()} }\n\n"
        
        history += "\n📋 SETTLEMENTS\n" + "-"*60 + "\n"
        for sett in self.data['settlements'][-15:]:
            history += f"{sett['date']} | {sett['from']} ➡️ {sett['to']}: ₹{sett['amount']}\n"
        
        text.insert('1.0', history)
        text.config(state='disabled')
    
    def reset_all(self):
        if messagebox.askyesno("⚠️ Reset", "Delete ALL data? Cannot undo!", parent=self.root):
            self.data = {"group": [], "expenses": [], "settlements": []}
            self.save_data()
            self.refresh_dashboard()
            messagebox.showinfo("🗑️ Reset", "Data cleared! Fresh start.", parent=self.root)


if __name__ == "__main__":
    root = tk.Tk()
    app = SplitwisePremium(root)
    root.mainloop()
