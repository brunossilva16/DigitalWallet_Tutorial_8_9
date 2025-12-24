"""
∀ (for all), ∃ (there exists), ∈ (belongs to / is an element of), ∧ (logical and), ∨ (logical or), ↔ (if and only if), → (implies)
"""

import uuid
import time
from typing import Optional, Dict, List

class WalletSystem:
    def __init__(self):
        self.balances: Dict[str, float] = {}
        self.transactions: List[Dict] = []
        self.user_pins: Dict[str, str] = {}
        self.payment_methods: Dict[str, List[Dict]] = {}
        self.spending_limits: Dict[str, Dict] = {}

    # ------------------ SYSTEM INVARIANTS ------------------
    def verify_invariants(self) -> bool:
        """
        Invariants (sempre devem ser verdadeiros):
            I1: ∀ user_id ∈ balances.keys() → user_id é único
            I2: ∀ balance ∈ balances.values() → balance ≥ 0
            I3: ∀ user_id ∈ user_pins.keys() → user_id ∈ balances.keys()
            I4: ∀ user_id ∈ payment_methods.keys() → user_id ∈ balances.keys()
            I5: ∀ user_id ∈ spending_limits.keys() → user_id ∈ balances.keys()
        
        ensures:
            returns True ↔ todos os invariantes são válidos
        """
        try:
            # I1: Unicidade de user_ids (garantido por dict)
            assert len(self.balances) == len(set(self.balances.keys())), "I1 violated: Duplicate user IDs"
            
            # I2: Saldos não-negativos
            assert all(b >= 0 for b in self.balances.values()), "I2 violated: Negative balance found"
            
            # I3: Consistência de user_pins
            assert all(uid in self.balances for uid in self.user_pins.keys()), "I4 violated: PIN for non-existent user"
            
            # I4: Consistência de payment_methods
            assert all(uid in self.balances for uid in self.payment_methods.keys()), "I5 violated: Payment method for non-existent user"
            
            # I5: Consistência de spending_limits
            assert all(uid in self.balances for uid in self.spending_limits.keys()), "I6 violated: Spending limit for non-existent user"
            
            return True
        except AssertionError as e:
            print(f"Invariant violation: {e}")
            return False

    # ------------------ ACCOUNT CREATION ------------------
    def create_account(self, user_id: str, email: str, password: str) -> None:
        """
        requires:
            R1: user_id ≠ "" ∧ user_id ≠ None
            R2: user_id ∉ balances.keys()
            R3: email ≠ "" ∧ email ≠ None ∧ '@' ∈ email
            R4: password ≠ "" ∧ password ≠ None ∧ len(password) ≥ 6
            R5: verify_invariants() = True (pré-condição do sistema)
        
        ensures:
            E1: user_id ∈ balances.keys()
            E2: balances[user_id] = 0.0
            E3: |balances| = |balances_old| + 1
            E4: ∀ u ∈ balances_old.keys() → balances[u] = balances_old[u]
            E5: verify_invariants() = True (pós-condição do sistema)
        """
        # Verificação de pré-condições
        assert user_id and isinstance(user_id, str), "R1 violated: Invalid user_id"
        assert user_id not in self.balances, "R2 violated: User already exists"
        assert email and isinstance(email, str) and '@' in email, "R3 violated: Invalid email"
        assert password and isinstance(password, str) and len(password) >= 6, "R4 violated: Password too weak"
        
        old_count = len(self.balances)
        old_balances = dict(self.balances)
        
        # Operação
        self.balances[user_id] = 0.0
        
        # Verificação de pós-condições
        assert user_id in self.balances, "E1 violated"
        assert self.balances[user_id] == 0.0, "E2 violated"
        assert len(self.balances) == old_count + 1, "E3 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances), "E4 violated"
        assert self.verify_invariants(), "E5 violated: Invariants broken"

    # ------------------ PIN MANAGEMENT ------------------
    def set_pin(self, user_id: str, pin: str) -> None:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: pin ≠ "" ∧ pin ≠ None
            R3: len(pin) ≥ 4 ∧ len(pin) ≤ 8
            R4: pin contém apenas dígitos
        
        ensures:
            E1: user_pins[user_id] = pin
            E2: ∀ u ∈ balances.keys() → balances[u] = balances_old[u] (saldos inalterados)
            E3: verify_invariants() = True
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert pin and isinstance(pin, str), "R2 violated: Invalid PIN"
        assert 4 <= len(pin) <= 8, "R3 violated: PIN length must be 4-8"
        assert pin.isdigit(), "R4 violated: PIN must contain only digits"
        
        old_balances = dict(self.balances)
        
        self.user_pins[user_id] = pin
        
        assert self.user_pins[user_id] == pin, "E1 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances), "E2 violated"
        assert self.verify_invariants(), "E3 violated"

    def authenticate_pin(self, user_id: str, pin: str) -> bool:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: pin ≠ None ∧ isinstance(pin, str)
        
        ensures:
            E1: returns True ↔ user_pins.get(user_id) = pin
            E2: ∀ u ∈ balances.keys() → balances[u] = balances_old[u] (função pura de leitura)
            E3: user_pins não é modificado
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert pin is not None and isinstance(pin, str), "R2 violated: Invalid PIN format"
        
        old_pins = dict(self.user_pins)
        expected = self.user_pins.get(user_id)
        result = expected == pin
        
        assert self.user_pins == old_pins, "E3 violated: State modified"
        return result

    # ------------------ FUNDS MANAGEMENT ------------------
    def add_funds(self, user_id: str, amount: float) -> None:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: amount > 0
            R3: amount ≤ 1_000_000 (limite de segurança)
            R4: balances[user_id] + amount < float_max (sem overflow)
        
        ensures:
            E1: balances[user_id] = balances_old[user_id] + amount
            E2: ∀ u ∈ balances.keys() ∧ u ≠ user_id → balances[u] = balances_old[u]
            E3: sum(balances.values()) = sum(balances_old.values()) + amount
            E4: ∃ tx ∈ transactions: tx.type = "deposit" ∧ tx.user_id = user_id ∧ tx.amount = amount
            E5: |transactions| = |transactions_old| + 1
            E6: verify_invariants() = True
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert amount > 0, "R2 violated: Amount must be positive"
        assert amount <= 1_000_000, "R3 violated: Amount exceeds safety limit"
        assert self.balances[user_id] + amount < float('inf'), "R4 violated: Overflow risk"
        
        before = self.balances[user_id]
        old_balances = dict(self.balances)
        old_total = sum(self.balances.values())
        old_tx_count = len(self.transactions)
        
        self.balances[user_id] += amount
        tx_id = str(uuid.uuid4())
        self.transactions.append({
            "id": tx_id,
            "type": "deposit",
            "user_id": user_id,
            "amount": amount,
            "timestamp": time.time(),
            "status": "completed"
        })
        
        assert abs(self.balances[user_id] - (before + amount)) < 1e-9, "E1 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances if u != user_id), "E2 violated"
        assert abs(sum(self.balances.values()) - (old_total + amount)) < 1e-9, "E3 violated"
        assert any(t["type"] == "deposit" and t["user_id"] == user_id and abs(t["amount"] - amount) < 1e-9 
                   for t in self.transactions[-1:]), "E4 violated"
        assert len(self.transactions) == old_tx_count + 1, "E5 violated"
        assert self.verify_invariants(), "E6 violated"

    def withdraw_funds(self, user_id: str, bank_account: str, amount: float) -> None:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: bank_account.startswith("PT") ∧ len(bank_account) ≥ 10
            R3: amount > 0 ∧ amount ≤ 10_000 (limite diário de saque)
            R4: balances[user_id] ≥ amount
            R5: balances[user_id] - amount ≥ 0
        
        ensures:
            E1: balances[user_id] = balances_old[user_id] - amount
            E2: ∀ u ∈ balances.keys() ∧ u ≠ user_id → balances[u] = balances_old[u]
            E3: sum(balances.values()) = sum(balances_old.values()) - amount
            E4: ∃ tx ∈ transactions: tx.type = "withdrawal" ∧ tx.destination = bank_account
            E5: verify_invariants() = True
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert bank_account.startswith("PT") and len(bank_account) >= 10, "R2 violated: Invalid bank account"
        assert 0 < amount <= 10_000, "R3 violated: Invalid withdrawal amount"
        assert self.balances[user_id] >= amount, "R4 violated: Insufficient balance"
        assert self.balances[user_id] - amount >= 0, "R5 violated: Would result in negative balance"

        before = self.balances[user_id]
        old_balances = dict(self.balances)
        old_total = sum(self.balances.values())
        
        self.balances[user_id] -= amount
        self.transactions.append({
            "id": str(uuid.uuid4()),
            "type": "withdrawal",
            "user_id": user_id,
            "amount": amount,
            "destination": bank_account,
            "timestamp": time.time(),
            "status": "completed"
        })
        
        assert abs(self.balances[user_id] - (before - amount)) < 1e-9, "E1 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances if u != user_id), "E2 violated"
        assert abs(sum(self.balances.values()) - (old_total - amount)) < 1e-9, "E3 violated"
        assert any(t["type"] == "withdrawal" and t.get("destination") == bank_account 
                   for t in self.transactions[-1:]), "E4 violated"
        assert self.verify_invariants(), "E5 violated"

    # ------------------ TRANSFERS ------------------
    def transfer(self, sender: str, receiver: str, amount: float) -> None:
        """
        requires:
            R1: sender ∈ balances.keys() ∧ receiver ∈ balances.keys()
            R2: sender ≠ receiver
            R3: amount > 0
            R4: balances[sender] ≥ amount
            R5: balances[receiver] + amount < float_max (sem overflow)
        
        ensures:
            E1: balances[sender] = balances_old[sender] - amount
            E2: balances[receiver] = balances_old[receiver] + amount
            E3: ∀ u ∈ balances.keys() ∧ u ∉ {sender, receiver} → balances[u] = balances_old[u]
            E4: sum(balances.values()) = sum(balances_old.values()) (conservação de valor)
            E5: ∃ tx ∈ transactions: tx.type = "transfer" ∧ tx.from = sender ∧ tx.to = receiver
            E6: verify_invariants() = True
        """
        assert sender in self.balances and receiver in self.balances, "R1 violated: Both users must exist"
        assert sender != receiver, "R2 violated: Sender and receiver must be different"
        assert amount > 0, "R3 violated: Amount must be positive"
        assert self.balances[sender] >= amount, "R4 violated: Insufficient funds"
        assert self.balances[receiver] + amount < float('inf'), "R5 violated: Overflow risk"

        old_sender = self.balances[sender]
        old_receiver = self.balances[receiver]
        old_balances = dict(self.balances)
        total_before = sum(self.balances.values())
        
        self.balances[sender] -= amount
        self.balances[receiver] += amount
        self.transactions.append({
            "id": str(uuid.uuid4()),
            "type": "transfer",
            "from": sender,
            "to": receiver,
            "amount": amount,
            "timestamp": time.time(),
            "status": "completed"
        })
        
        total_after = sum(self.balances.values())
        
        assert abs(self.balances[sender] - (old_sender - amount)) < 1e-9, "E1 violated"
        assert abs(self.balances[receiver] - (old_receiver + amount)) < 1e-9, "E2 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances if u not in {sender, receiver}), "E3 violated"
        assert abs(total_before - total_after) < 1e-9, "E4 violated: Total balance changed"
        assert any(t["type"] == "transfer" and t.get("from") == sender and t.get("to") == receiver 
                   for t in self.transactions[-1:]), "E5 violated"
        assert self.verify_invariants(), "E6 violated"

    # ------------------ INTEREST ------------------
    def apply_interest(self, rate: float) -> None:
        """
        requires:
            R1: 0 < rate ≤ 0.2 (máximo 20% para segurança)
            R2: ∀ user_id ∈ balances.keys() → balances[user_id] * (1 + rate) < float_max
        
        ensures:
            E1: ∀ user_id ∈ balances.keys() → balances[user_id] = balances_old[user_id] * (1 + rate)
            E2: sum(balances.values()) = sum(balances_old.values()) * (1 + rate)
            E3: |transactions| = |transactions_old| + |balances.keys()|
            E4: ∀ user_id ∈ balances.keys() → ∃ tx: tx.type = "interest" ∧ tx.user_id = user_id
            E5: verify_invariants() = True
        """
        assert 0 < rate <= 0.2, "R1 violated: Invalid interest rate"
        assert all(b * (1 + rate) < float('inf') for b in self.balances.values()), "R2 violated: Overflow risk"
        
        total_before = sum(self.balances.values())
        old_balances = dict(self.balances)
        old_tx_count = len(self.transactions)

        for user_id in list(self.balances.keys()):
            old = self.balances[user_id]
            interest = old * rate
            self.balances[user_id] = old + interest
            self.transactions.append({
                "id": str(uuid.uuid4()),
                "type": "interest",
                "user_id": user_id,
                "amount": interest,
                "timestamp": time.time(),
                "status": "completed"
            })

        total_after = sum(self.balances.values())
        
        assert all(abs(self.balances[uid] - old_balances[uid] * (1 + rate)) < 1e-9 
                   for uid in old_balances), "E1 violated"
        assert abs(total_after - (total_before * (1 + rate))) < 1e-6, "E2 violated"
        assert len(self.transactions) == old_tx_count + len(old_balances), "E3 violated"
        assert all(any(t["type"] == "interest" and t["user_id"] == uid 
                       for t in self.transactions[-len(old_balances):]) 
                   for uid in old_balances), "E4 violated"
        assert self.verify_invariants(), "E5 violated"

    # ------------------ SPENDING LIMITS ------------------
    def set_spending_limits(self, user_id: str, daily: Optional[float] = None, 
                           monthly: Optional[float] = None) -> None:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: (daily = None ∨ daily > 0) ∧ (monthly = None ∨ monthly > 0)
            R3: (daily ≠ None ∧ monthly ≠ None) → daily ≤ monthly
        
        ensures:
            E1: spending_limits[user_id].daily = daily
            E2: spending_limits[user_id].monthly = monthly
            E3: spending_limits[user_id].daily_used = 0
            E4: spending_limits[user_id].monthly_used = 0
            E5: ∀ u ∈ balances.keys() → balances[u] = balances_old[u]
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert (daily is None or daily > 0) and (monthly is None or monthly > 0), "R2 violated: Limits must be positive or None"
        assert not (daily is not None and monthly is not None and daily > monthly), "R3 violated: Daily limit exceeds monthly"
        
        old_balances = dict(self.balances)
        
        self.spending_limits[user_id] = {
            "daily": daily,
            "monthly": monthly,
            "daily_used": 0.0,
            "monthly_used": 0.0
        }
        
        assert self.spending_limits[user_id]["daily"] == daily, "E1 violated"
        assert self.spending_limits[user_id]["monthly"] == monthly, "E2 violated"
        assert self.spending_limits[user_id]["daily_used"] == 0.0, "E3 violated"
        assert self.spending_limits[user_id]["monthly_used"] == 0.0, "E4 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances), "E5 violated"

    # ------------------ PAYMENT METHODS ------------------
    def add_payment_method(self, user_id: str, method: Dict) -> None:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: isinstance(method, dict) ∧ "type" ∈ method.keys()
            R3: method["type"] ∈ {"card", "bank_account", "paypal"}
        
        ensures:
            E1: user_id ∈ payment_methods.keys()
            E2: method ∈ payment_methods[user_id]
            E3: |payment_methods[user_id]| = |payment_methods_old.get(user_id, [])| + 1
            E4: ∀ u ∈ balances.keys() → balances[u] = balances_old[u]
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert isinstance(method, dict) and "type" in method, "R2 violated: Invalid payment method"
        assert method["type"] in {"card", "bank_account", "paypal"}, "R3 violated: Invalid payment type"
        
        old_count = len(self.payment_methods.get(user_id, []))
        old_balances = dict(self.balances)
        
        if user_id not in self.payment_methods:
            self.payment_methods[user_id] = []
        self.payment_methods[user_id].append(method)
        
        assert user_id in self.payment_methods, "E1 violated"
        assert method in self.payment_methods[user_id], "E2 violated"
        assert len(self.payment_methods[user_id]) == old_count + 1, "E3 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances), "E4 violated"

    def get_payment_methods(self, user_id: str) -> List[Dict]:
        """
        requires:
            R1: user_id ∈ balances.keys()
        
        ensures:
            E1: returns payment_methods.get(user_id, [])
            E2: ∀ u ∈ balances.keys() → balances[u] = balances_old[u] (função pura)
            E3: payment_methods não é modificado
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        
        old_methods = dict(self.payment_methods)
        result = self.payment_methods.get(user_id, [])
        
        assert self.payment_methods == old_methods, "E3 violated: State modified"
        return result

    # ------------------ TRANSACTIONS ------------------
    def track_transactions(self, user_id: str, filters: Optional[Dict] = None, 
                          page: int = 1, page_size: int = 25) -> List[Dict]:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: page ≥ 1
            R3: 1 ≤ page_size ≤ 100
            R4: filters = None ∨ isinstance(filters, dict)
        
        ensures:
            E1: |returns| ≤ page_size
            E2: ∀ tx ∈ returns → (tx.user_id = user_id ∨ tx.from = user_id ∨ tx.to = user_id)
            E3: returns está ordenado por timestamp (decrescente)
            E4: ∀ u ∈ balances.keys() → balances[u] = balances_old[u] (função pura)
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert page >= 1, "R2 violated: Page must be >= 1"
        assert 1 <= page_size <= 100, "R3 violated: Invalid page size"
        assert filters is None or isinstance(filters, dict), "R4 violated: Invalid filters"
        
        old_balances = dict(self.balances)
        
        txs = [t for t in self.transactions 
               if t.get("user_id") == user_id or t.get("from") == user_id or t.get("to") == user_id]

        if filters:
            for k, v in filters.items():
                txs = [t for t in txs if t.get(k) == v]

        txs.sort(key=lambda t: t.get("timestamp", 0), reverse=True)
        start = (page - 1) * page_size
        end = start + page_size
        result = txs[start:end]
        
        assert len(result) <= page_size, "E1 violated"
        assert all(t.get("user_id") == user_id or t.get("from") == user_id or t.get("to") == user_id 
                   for t in result), "E2 violated"
        assert all(result[i].get("timestamp", 0) >= result[i+1].get("timestamp", 0) 
                   for i in range(len(result)-1)), "E3 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances), "E4 violated"
        
        return result

    # ------------------ REAL-TIME UPDATES ------------------
    def real_time_update(self, user_id: str, amount: float) -> None:
        """
        requires:
            R1: user_id ∈ balances.keys()
            R2: amount ≠ 0
            R3: amount > 0 ∨ balances[user_id] ≥ |amount| (saldo suficiente para débitos)
            R4: balances[user_id] + amount ≥ 0
        
        ensures:
            E1: balances[user_id] = balances_old[user_id] + amount
            E2: ∀ u ∈ balances.keys() ∧ u ≠ user_id → balances[u] = balances_old[u]
            E3: ∃ tx ∈ transactions: tx.type ∈ {"credit", "debit"} ∧ tx.user_id = user_id
            E4: verify_invariants() = True
        """
        assert user_id in self.balances, "R1 violated: User must exist"
        assert amount != 0, "R2 violated: Amount cannot be zero"
        assert amount > 0 or self.balances[user_id] >= abs(amount), "R3 violated: Insufficient balance for debit"
        assert self.balances[user_id] + amount >= 0, "R4 violated: Would result in negative balance"
        
        before = self.balances[user_id]
        old_balances = dict(self.balances)
        
        self.balances[user_id] += amount
        tx_type = "credit" if amount > 0 else "debit"
        self.transactions.append({
            "id": str(uuid.uuid4()),
            "type": tx_type,
            "user_id": user_id,
            "amount": amount,
            "timestamp": time.time(),
            "status": "completed"
        })
        
        assert abs(self.balances[user_id] - (before + amount)) < 1e-9, "E1 violated"
        assert all(self.balances[u] == old_balances[u] for u in old_balances if u != user_id), "E2 violated"
        assert any(t["type"] in {"credit", "debit"} and t["user_id"] == user_id 
                   for t in self.transactions[-1:]), "E3 violated"
        assert self.verify_invariants(), "E4 violated"