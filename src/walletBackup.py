import uuid

class WalletSystem:
	def create_account(self, user_id: str, email: str, password: str):
		"""
		Creates a new user account and wallet.
		Preconditions:
		- user_id not in balances
		- email and password are non-empty
		Postconditions:
		- user_id added to balances with zero balance
		"""
		assert user_id not in self.balances, "User already exists"
		assert email and password, "Email and password required"
		self.balances[user_id] = 0

	def set_spending_limits(self, user_id: str, daily: int = None, monthly: int = None):
		"""
		Sets daily and monthly spending limits for a user.
		Preconditions:
		- user_id exists
		- limits are positive integers or None
		Postconditions:
		- limits stored for user
		"""
		assert user_id in self.balances, "User must exist"
		if not hasattr(self, 'spending_limits'):
			self.spending_limits = {}
		self.spending_limits[user_id] = {
			'daily': daily,
			'monthly': monthly,
			'daily_used': 0,
			'monthly_used': 0
		}

	def withdraw_funds(self, user_id: str, bank_account: str, amount: int):
		"""
		Withdraws funds to a validated bank account.
		Preconditions:
		- user_id exists
		- bank_account is validated (simulate)
		- amount > 0 and user has sufficient balance
		Postconditions:
		- user's balance decreased by amount if successful
		- withdrawal transaction recorded
		"""
		assert user_id in self.balances, "User must exist"
		assert amount > 0, "Amount must be positive"
		assert self.balances[user_id] >= amount, "Insufficient balance"
		# Simulate bank account validation
		assert bank_account.startswith('PT'), "Bank account must be validated"
		before = self.balances[user_id]
		self.balances[user_id] -= amount
		tx = {
			'id': str(uuid.uuid4()),
			'type': 'withdrawal',
			'user_id': user_id,
			'amount': amount,
			'destination': bank_account,
			'status': 'completed'
		}
		self.transactions.append(tx)
		after = self.balances[user_id]
		assert after == before - amount, "Balance not updated correctly"

	def track_transactions(self, user_id: str, filters: dict = None, page: int = 1, page_size: int = 25):
		"""
		Returns paginated, filtered transaction history for a user.
		Preconditions:
		- user_id exists
		Postconditions:
		- returns list of transactions matching filters
		"""
		assert user_id in self.balances, "User must exist"
		txs = [t for t in self.transactions if t.get('user_id') == user_id]
		# Apply filters (date, category, amount, status)
		if filters:
			for k, v in filters.items():
				txs = [t for t in txs if t.get(k) == v]
		# Order by most recent (simulate timestamp field)
		txs.sort(key=lambda t: t.get('timestamp', ''), reverse=True)
		start = (page - 1) * page_size
		end = start + page_size
		return txs[start:end]

	def real_time_update(self, user_id: str, amount: int):
		"""
		Performs a transaction and updates balance instantly.
		Preconditions:
		- user_id exists
		- amount can be positive or negative
		Postconditions:
		- user's balance updated
		- transaction recorded
		"""
		assert user_id in self.balances, "User must exist"
		before = self.balances[user_id]
		self.balances[user_id] += amount
		tx = {
			'id': str(uuid.uuid4()),
			'type': 'debit' if amount < 0 else 'credit',
			'user_id': user_id,
			'amount': amount,
			'status': 'completed'
		}
		self.transactions.append(tx)
		after = self.balances[user_id]
		assert after == before + amount, "Balance not updated correctly"

	def authenticate_pin(self, user_id: str, pin: str):
		"""
		Authenticates user with PIN.
		Preconditions:
		- user_id exists
		- pin is a string
		Postconditions:
		- returns True if PIN matches, False otherwise
		"""
		if not hasattr(self, 'user_pins'):
			self.user_pins = {}
		assert user_id in self.balances, "User must exist"
		expected = self.user_pins.get(user_id, None)
		return expected == pin

	def set_pin(self, user_id: str, pin: str):
		"""
		Sets a PIN for a user.
		Preconditions:
		- user_id exists
		- pin is a string
		Postconditions:
		- PIN stored for user
		"""
		if not hasattr(self, 'user_pins'):
			self.user_pins = {}
		assert user_id in self.balances, "User must exist"
		assert isinstance(pin, str) and pin, "PIN must be a non-empty string"
		self.user_pins[user_id] = pin

	def add_payment_method(self, user_id: str, method: dict):
		"""
		Adds a payment method for a user.
		Preconditions:
		- user_id exists
		- method is a dict with required fields
		Postconditions:
		- payment method stored for user
		"""
		if not hasattr(self, 'payment_methods'):
			self.payment_methods = {}
		assert user_id in self.balances, "User must exist"
		assert isinstance(method, dict) and 'type' in method, "Invalid payment method"
		if user_id not in self.payment_methods:
			self.payment_methods[user_id] = []
		self.payment_methods[user_id].append(method)

	def get_payment_methods(self, user_id: str):
		"""
		Returns all payment methods for a user.
		Preconditions:
		- user_id exists
		Postconditions:
		- returns list of payment methods
		"""
		if not hasattr(self, 'payment_methods'):
			self.payment_methods = {}
		assert user_id in self.balances, "User must exist"
		return self.payment_methods.get(user_id, [])

	def add_funds(self, user_id: str, amount: int):
		"""
		Adds funds to a user's wallet.
		Preconditions:
		- user_id exists in balances
		- amount > 0
		Postconditions:
		- user's balance increased by amount
		- transaction recorded
		"""
		assert user_id in self.balances, "User must exist"
		assert amount > 0, "Amount must be positive"
		before = self.balances[user_id]
		self.balances[user_id] += amount
		tx = {
			'id': str(uuid.uuid4()),
			'type': 'deposit',
			'user_id': user_id,
			'amount': amount,
			'status': 'completed'
		}
		self.transactions.append(tx)
		after = self.balances[user_id]
		assert after == before + amount, "Balance not updated correctly"

	def transfer(self, fromUser: str, toUser: str, amount: int):
		"""
		Transfers funds from one user to another.
		Preconditions:
		- fromUser and toUser are valid, different user IDs in balances
		- amount > 0
		- fromUser has at least 'amount' funds
		Postconditions:
		- fromUser's balance decreased by amount
		- toUser's balance increased by amount
		- total sum of all balances unchanged
		- no other account balances affected
		"""
		assert fromUser in self.balances, "fromUser must exist"
		assert toUser in self.balances, "toUser must exist"
		assert fromUser != toUser, "fromUser and toUser must be different"
		assert amount > 0, "amount must be positive"
		assert self.balances[fromUser] >= amount, "Insufficient funds"

		total_before = sum(self.balances.values())

		self.balances[fromUser] -= amount
		self.balances[toUser] += amount

		tx = {
			'id': str(uuid.uuid4()),
			'type': 'transfer',
			'from': fromUser,
			'to': toUser,
			'amount': amount,
			'status': 'completed'
		}
		self.transactions.append(tx)

		total_after = sum(self.balances.values())
		assert total_before == total_after, "Total balance must remain unchanged"

	def apply_interest(self, rate: int):
		"""
		Applies a constant interest rate to all accounts.
		Preconditions:
		- rate > 0
		Postconditions:
		- Each user's balance updated: new_balance = old_balance * (10000 + rate) // 10000
		- New total sum equals old total sum scaled by interest factor
		- Set of user accounts unchanged
		- Interest transactions recorded
		"""
		assert isinstance(rate, int) and rate > 0, "Rate must be a positive integer"

		total_before = sum(self.balances.values())
		factor = 10000 + rate
		interest_txs = []

		for user in self.balances:
			old_balance = self.balances[user]
			new_balance = old_balance * factor // 10000
			interest = new_balance - old_balance
			self.balances[user] = new_balance
			tx = {
				'id': str(uuid.uuid4()),
				'type': 'interest',
				'user_id': user,
				'amount': interest,
				'status': 'completed'
			}
			interest_txs.append(tx)
		self.transactions.extend(interest_txs)

		total_after = sum(self.balances.values())
		expected_total = total_before * factor // 10000
		assert total_after == expected_total, "Total sum must be scaled by interest factor"
