import pytest
import uuid
import time
from decimal import Decimal
from src.wallet import WalletSystem

class TestWalletSystem:
    """Testes unitários para WalletSystem com foco em Design by Contract"""
    
    def setup_method(self):
        """Prepara um novo sistema para cada teste"""
        self.wallet = WalletSystem()
        
    # ------------------ TESTES DE INVARIANTES ------------------
    
    def test_verify_invariants_on_empty_system(self):
        """Testa invariantes em sistema vazio"""
        assert self.wallet.verify_invariants() == True
        
    def test_verify_invariants_negative_balance(self):
        """Testa violação do invariante I2 (saldos não-negativos)"""
        self.wallet.balances["user1"] = -100.0
        assert self.wallet.verify_invariants() == False
        
    def test_verify_invariants_inconsistent_pin(self):
        """Testa violação do invariante I3 (PIN para usuário inexistente)"""
        self.wallet.user_pins["ghost_user"] = "1234"
        assert self.wallet.verify_invariants() == False
        
    def test_verify_invariants_after_valid_operations(self):
        """Testa invariantes após operações válidas"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.set_pin("user1", "1234")
        self.wallet.add_funds("user1", 100.0)
        
        assert self.wallet.verify_invariants() == True
        
    # ------------------ TESTES DE CRIAÇÃO DE CONTA ------------------
    
    def test_create_account_valid(self):
        """Testa criação válida de conta"""
        # Pré-condições
        assert "user1" not in self.wallet.balances
        assert len(self.wallet.balances) == 0
        
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        # Pós-condições
        assert "user1" in self.wallet.balances
        assert self.wallet.balances["user1"] == 0.0
        assert len(self.wallet.balances) == 1
        assert self.wallet.verify_invariants()
        
    def test_create_account_duplicate_user_id(self):
        """Testa criação com user_id duplicado"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R2 violated: User already exists"):
            self.wallet.create_account("user1", "user2@email.com", "password456")
            
    def test_create_account_invalid_user_id(self):
        """Testa criação com user_id inválido"""
        with pytest.raises(AssertionError, match="R1 violated: Invalid user_id"):
            self.wallet.create_account("", "user@email.com", "password123")
            
        with pytest.raises(AssertionError):
            self.wallet.create_account(None, "user@email.com", "password123")
            
    def test_create_account_invalid_email(self):
        """Testa criação com email inválido"""
        with pytest.raises(AssertionError, match="R3 violated: Invalid email"):
            self.wallet.create_account("user1", "invalid-email", "password123")
            
        with pytest.raises(AssertionError):
            self.wallet.create_account("user1", "", "password123")
            
    def test_create_account_weak_password(self):
        """Testa criação com senha fraca"""
        with pytest.raises(AssertionError, match="R4 violated: Password too weak"):
            self.wallet.create_account("user1", "user@email.com", "123")
            
        with pytest.raises(AssertionError):
            self.wallet.create_account("user1", "user@email.com", "")
            
    # ------------------ TESTES DE PIN ------------------
    
    def test_set_pin_valid(self):
        """Testa configuração válida de PIN"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        self.wallet.set_pin("user1", "123456")
        
        assert self.wallet.user_pins["user1"] == "123456"
        assert self.wallet.verify_invariants()
        
    def test_set_pin_user_not_exists(self):
        """Testa configuração de PIN para usuário inexistente"""
        with pytest.raises(AssertionError, match="R1 violated: User must exist"):
            self.wallet.set_pin("ghost", "1234")
            
    def test_set_pin_invalid_length(self):
        """Testa configuração de PIN com tamanho inválido"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R3 violated: PIN length must be 4-8"):
            self.wallet.set_pin("user1", "123")  # Muito curto
            
        with pytest.raises(AssertionError):
            self.wallet.set_pin("user1", "123456789")  # Muito longo
            
    def test_set_pin_non_digit(self):
        """Testa configuração de PIN com caracteres não numéricos"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R4 violated: PIN must contain only digits"):
            self.wallet.set_pin("user1", "12a4")
            
    def test_authenticate_pin_valid(self):
        """Testa autenticação válida"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.set_pin("user1", "1234")
        
        assert self.wallet.authenticate_pin("user1", "1234") == True
        assert self.wallet.authenticate_pin("user1", "0000") == False
        
    def test_authenticate_pin_no_pin_set(self):
        """Testa autenticação quando PIN não foi configurado"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        # PIN não configurado retorna False
        assert self.wallet.authenticate_pin("user1", "1234") == False
        
    def test_authenticate_pin_state_not_modified(self):
        """Testa que autenticação não modifica estado"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.set_pin("user1", "1234")
        
        original_state = {
            "balances": dict(self.wallet.balances),
            "pins": dict(self.wallet.user_pins),
            "transactions": list(self.wallet.transactions)
        }
        
        self.wallet.authenticate_pin("user1", "1234")
        self.wallet.authenticate_pin("user1", "wrong")
        
        assert self.wallet.balances == original_state["balances"]
        assert self.wallet.user_pins == original_state["pins"]
        assert self.wallet.transactions == original_state["transactions"]
        
    # ------------------ TESTES DE ADIÇÃO DE FUNDOS ------------------
    
    def test_add_funds_valid(self):
        """Testa adição válida de fundos"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        initial_balance = self.wallet.balances["user1"]
        initial_total = sum(self.wallet.balances.values())
        initial_tx_count = len(self.wallet.transactions)
        
        amount = 100.50
        self.wallet.add_funds("user1", amount)
        
        # Verifica pós-condições
        assert abs(self.wallet.balances["user1"] - (initial_balance + amount)) < 1e-9
        assert abs(sum(self.wallet.balances.values()) - (initial_total + amount)) < 1e-9
        assert len(self.wallet.transactions) == initial_tx_count + 1
        
        # Verifica transação
        last_tx = self.wallet.transactions[-1]
        assert last_tx["type"] == "deposit"
        assert last_tx["user_id"] == "user1"
        assert abs(last_tx["amount"] - amount) < 1e-9
        assert last_tx["status"] == "completed"
        
        assert self.wallet.verify_invariants()
        
    def test_add_funds_user_not_exists(self):
        """Testa adição para usuário inexistente"""
        with pytest.raises(AssertionError, match="R1 violated: User must exist"):
            self.wallet.add_funds("ghost", 100)
            
    def test_add_funds_non_positive_amount(self):
        """Testa adição com valor não positivo"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R2 violated: Amount must be positive"):
            self.wallet.add_funds("user1", 0)
            
        with pytest.raises(AssertionError):
            self.wallet.add_funds("user1", -100)
            
    def test_add_funds_exceeds_safety_limit(self):
        """Testa adição acima do limite de segurança"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R3 violated: Amount exceeds safety limit"):
            self.wallet.add_funds("user1", 1_000_001)
            
    # ------------------ TESTES DE SAQUE ------------------
    
    def test_withdraw_funds_valid(self):
        """Testa saque válido"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 500.0)
        
        initial_balance = self.wallet.balances["user1"]
        initial_total = sum(self.wallet.balances.values())
        amount = 200.0
        
        self.wallet.withdraw_funds("user1", "PT500123456789", amount)
        
        assert abs(self.wallet.balances["user1"] - (initial_balance - amount)) < 1e-9
        assert abs(sum(self.wallet.balances.values()) - (initial_total - amount)) < 1e-9
        
        last_tx = self.wallet.transactions[-1]
        assert last_tx["type"] == "withdrawal"
        assert last_tx["destination"] == "PT500123456789"
        assert abs(last_tx["amount"] - amount) < 1e-9
        
        assert self.wallet.verify_invariants()
        
    def test_withdraw_funds_insufficient_balance(self):
        """Testa saque com saldo insuficiente"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 100.0)
        
        with pytest.raises(AssertionError, match="R4 violated: Insufficient balance"):
            self.wallet.withdraw_funds("user1", "PT500123456789", 200.0)
            
    def test_withdraw_funds_invalid_bank_account(self):
        """Testa saque com conta bancária inválida"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 100.0)
        
        with pytest.raises(AssertionError, match="R2 violated: Invalid bank account"):
            self.wallet.withdraw_funds("user1", "INVALID", 50.0)
            
        with pytest.raises(AssertionError):
            self.wallet.withdraw_funds("user1", "PT123", 50.0)  # Muito curto
            
    def test_withdraw_funds_exceeds_daily_limit(self):
        """Testa saque acima do limite diário"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 15_000.0)
        
        with pytest.raises(AssertionError, match="R3 violated: Invalid withdrawal amount"):
            self.wallet.withdraw_funds("user1", "PT500123456789", 10_001.0)
            
    # ------------------ TESTES DE TRANSFERÊNCIA ------------------
    
    def test_transfer_valid(self):
        """Testa transferência válida"""
        self.wallet.create_account("sender", "sender@email.com", "password123")
        self.wallet.create_account("receiver", "receiver@email.com", "password456")
        
        self.wallet.add_funds("sender", 300.0)
        
        initial_sender = self.wallet.balances["sender"]
        initial_receiver = self.wallet.balances["receiver"]
        initial_total = sum(self.wallet.balances.values())
        amount = 150.0
        
        self.wallet.transfer("sender", "receiver", amount)
        
        assert abs(self.wallet.balances["sender"] - (initial_sender - amount)) < 1e-9
        assert abs(self.wallet.balances["receiver"] - (initial_receiver + amount)) < 1e-9
        assert abs(sum(self.wallet.balances.values()) - initial_total) < 1e-9
        
        last_tx = self.wallet.transactions[-1]
        assert last_tx["type"] == "transfer"
        assert last_tx["from"] == "sender"
        assert last_tx["to"] == "receiver"
        
        assert self.wallet.verify_invariants()
        
    def test_transfer_sender_not_exists(self):
        """Testa transferência com remetente inexistente"""
        self.wallet.create_account("receiver", "receiver@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R1 violated: Both users must exist"):
            self.wallet.transfer("ghost", "receiver", 100.0)
            
    def test_transfer_receiver_not_exists(self):
        """Testa transferência com destinatário inexistente"""
        self.wallet.create_account("sender", "sender@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R1 violated: Both users must exist"):
            self.wallet.transfer("sender", "ghost", 100.0)
            
    def test_transfer_to_self(self):
        """Testa transferência para si mesmo"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 100.0)
        
        with pytest.raises(AssertionError, match="R2 violated: Sender and receiver must be different"):
            self.wallet.transfer("user1", "user1", 50.0)
            
    def test_transfer_insufficient_funds(self):
        """Testa transferência com saldo insuficiente"""
        self.wallet.create_account("sender", "sender@email.com", "password123")
        self.wallet.create_account("receiver", "receiver@email.com", "password456")
        
        self.wallet.add_funds("sender", 50.0)
        
        with pytest.raises(AssertionError, match="R4 violated: Insufficient funds"):
            self.wallet.transfer("sender", "receiver", 100.0)
            
    # ------------------ TESTES DE JUROS ------------------
    
    def test_apply_interest_valid(self):
        """Testa aplicação de juros válida"""
        # Cria múltiplos usuários
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.create_account("user2", "user2@email.com", "password456")
        
        self.wallet.add_funds("user1", 1000.0)
        self.wallet.add_funds("user2", 2000.0)
        
        initial_balances = dict(self.wallet.balances)
        initial_total = sum(self.wallet.balances.values())
        initial_tx_count = len(self.wallet.transactions)
        rate = 0.05  # 5%
        
        self.wallet.apply_interest(rate)
        
        # Verifica cada usuário
        for user_id in initial_balances:
            expected = initial_balances[user_id] * (1 + rate)
            assert abs(self.wallet.balances[user_id] - expected) < 1e-6
            
        # Verifica total
        expected_total = initial_total * (1 + rate)
        assert abs(sum(self.wallet.balances.values()) - expected_total) < 1e-6
        
        # Verifica transações
        assert len(self.wallet.transactions) == initial_tx_count + len(initial_balances)
        
        # Verifica transações de juros
        interest_txs = [t for t in self.wallet.transactions[-len(initial_balances):] 
                       if t["type"] == "interest"]
        assert len(interest_txs) == len(initial_balances)
        
        for tx in interest_txs:
            assert tx["user_id"] in initial_balances
            expected_interest = initial_balances[tx["user_id"]] * rate
            assert abs(tx["amount"] - expected_interest) < 1e-6
            
        assert self.wallet.verify_invariants()
        
    def test_apply_interest_invalid_rate(self):
        """Testa aplicação com taxa inválida"""
        with pytest.raises(AssertionError, match="R1 violated: Invalid interest rate"):
            self.wallet.apply_interest(0)  # Taxa zero
            
        with pytest.raises(AssertionError):
            self.wallet.apply_interest(-0.05)  # Taxa negativa
            
        with pytest.raises(AssertionError):
            self.wallet.apply_interest(0.21)  # Acima de 20%
            
    # ------------------ TESTES DE LIMITES DE GASTO ------------------
    
    def test_set_spending_limits_valid(self):
        """Testa configuração válida de limites"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        self.wallet.set_spending_limits("user1", daily=100.0, monthly=2000.0)
        
        limits = self.wallet.spending_limits["user1"]
        assert limits["daily"] == 100.0
        assert limits["monthly"] == 2000.0
        assert limits["daily_used"] == 0.0
        assert limits["monthly_used"] == 0.0
        
    def test_set_spending_limits_user_not_exists(self):
        """Testa configuração para usuário inexistente"""
        with pytest.raises(AssertionError, match="R1 violated: User must exist"):
            self.wallet.set_spending_limits("ghost", daily=100.0)
            
    def test_set_spending_limits_invalid_values(self):
        """Testa configuração com valores inválidos"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R2 violated: Limits must be positive or None"):
            self.wallet.set_spending_limits("user1", daily=0)
            
        with pytest.raises(AssertionError):
            self.wallet.set_spending_limits("user1", daily=-100)
            
    def test_set_spending_limits_daily_exceeds_monthly(self):
        """Testa configuração com limite diário maior que mensal"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R3 violated: Daily limit exceeds monthly"):
            self.wallet.set_spending_limits("user1", daily=2000.0, monthly=1000.0)
            
    # ------------------ TESTES DE MÉTODOS DE PAGAMENTO ------------------
    
    def test_add_payment_method_valid(self):
        """Testa adição válida de método de pagamento"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        card_method = {"type": "card", "last4": "1234", "brand": "Visa"}
        self.wallet.add_payment_method("user1", card_method)
        
        assert "user1" in self.wallet.payment_methods
        assert card_method in self.wallet.payment_methods["user1"]
        assert len(self.wallet.payment_methods["user1"]) == 1
        
    def test_add_payment_method_multiple(self):
        """Testa adição de múltiplos métodos"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        card = {"type": "card", "last4": "1234", "brand": "Visa"}
        paypal = {"type": "paypal", "email": "user@paypal.com"}
        bank = {"type": "bank_account", "iban": "PT500123456789"}
        
        self.wallet.add_payment_method("user1", card)
        self.wallet.add_payment_method("user1", paypal)
        self.wallet.add_payment_method("user1", bank)
        
        assert len(self.wallet.payment_methods["user1"]) == 3
        
    def test_add_payment_method_user_not_exists(self):
        """Testa adição para usuário inexistente"""
        with pytest.raises(AssertionError, match="R1 violated: User must exist"):
            self.wallet.add_payment_method("ghost", {"type": "card"})
            
    def test_add_payment_method_invalid_type(self):
        """Testa adição com tipo inválido"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R3 violated: Invalid payment type"):
            self.wallet.add_payment_method("user1", {"type": "invalid"})
            
    def test_get_payment_methods(self):
        """Testa obtenção de métodos de pagamento"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        card = {"type": "card", "last4": "1234"}
        self.wallet.add_payment_method("user1", card)
        
        methods = self.wallet.get_payment_methods("user1")
        assert len(methods) == 1
        assert methods[0] == card
        
    def test_get_payment_methods_user_not_exists(self):
        """Testa obtenção para usuário inexistente"""
        with pytest.raises(AssertionError, match="R1 violated: User must exist"):
            self.wallet.get_payment_methods("ghost")
            
    def test_get_payment_methods_no_methods(self):
        """Testa obtenção quando não há métodos"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        methods = self.wallet.get_payment_methods("user1")
        assert methods == []
        
    # ------------------ TESTES DE RASTREAMENTO DE TRANSAÇÕES ------------------
    
    def test_track_transactions_valid(self):
        """Testa rastreamento válido de transações"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.create_account("user2", "user2@email.com", "password456")
        
        # Adiciona algumas transações
        self.wallet.add_funds("user1", 100.0)
        self.wallet.add_funds("user2", 200.0)
        self.wallet.transfer("user1", "user2", 50.0)
        
        # Obtém transações do user1
        txs = self.wallet.track_transactions("user1")
        
        assert len(txs) <= 25  # Default page_size
        assert all(t.get("user_id") == "user1" or 
                  t.get("from") == "user1" or 
                  t.get("to") == "user1" for t in txs)
        
        # Verifica ordenação (mais recente primeiro)
        timestamps = [t.get("timestamp", 0) for t in txs]
        assert all(timestamps[i] >= timestamps[i+1] for i in range(len(timestamps)-1))
        
    def test_track_transactions_with_filters(self):
        """Testa rastreamento com filtros"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        self.wallet.add_funds("user1", 100.0)
        self.wallet.add_funds("user1", 200.0)
        
        # Filtra por tipo
        deposit_txs = self.wallet.track_transactions("user1", filters={"type": "deposit"})
        assert len(deposit_txs) == 2
        assert all(t["type"] == "deposit" for t in deposit_txs)
        
        # Filtro que não corresponde
        withdrawal_txs = self.wallet.track_transactions("user1", filters={"type": "withdrawal"})
        assert len(withdrawal_txs) == 0
        
    def test_track_transactions_pagination(self):
        """Testa rastreamento com paginação"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        # Cria mais transações que o page_size
        for i in range(30):
            self.wallet.real_time_update("user1", 10.0)
            
        # Página 1
        page1 = self.wallet.track_transactions("user1", page=1, page_size=10)
        assert len(page1) == 10
        
        # Página 2
        page2 = self.wallet.track_transactions("user1", page=2, page_size=10)
        assert len(page2) == 10
        
        # Página 3
        page3 = self.wallet.track_transactions("user1", page=3, page_size=10)
        assert len(page3) == 10
        
        # Página 4 (deve estar vazia ou ter menos)
        page4 = self.wallet.track_transactions("user1", page=4, page_size=10)
        assert len(page4) <= 10
        
    def test_track_transactions_invalid_page(self):
        """Testa rastreamento com página inválida"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R2 violated: Page must be >= 1"):
            self.wallet.track_transactions("user1", page=0)
            
    def test_track_transactions_invalid_page_size(self):
        """Testa rastreamento com tamanho de página inválido"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R3 violated: Invalid page size"):
            self.wallet.track_transactions("user1", page_size=0)
            
        with pytest.raises(AssertionError):
            self.wallet.track_transactions("user1", page_size=101)
            
    # ------------------ TESTES DE ATUALIZAÇÃO EM TEMPO REAL ------------------
    
    def test_real_time_update_credit(self):
        """Testa atualização com crédito"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        initial_balance = self.wallet.balances["user1"]
        amount = 150.75
        
        self.wallet.real_time_update("user1", amount)
        
        assert abs(self.wallet.balances["user1"] - (initial_balance + amount)) < 1e-9
        
        last_tx = self.wallet.transactions[-1]
        assert last_tx["type"] == "credit"
        assert last_tx["user_id"] == "user1"
        assert abs(last_tx["amount"] - amount) < 1e-9
        
        assert self.wallet.verify_invariants()
        
    def test_real_time_update_debit(self):
        """Testa atualização com débito"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 500.0)
        
        initial_balance = self.wallet.balances["user1"]
        amount = -200.25
        
        self.wallet.real_time_update("user1", amount)
        
        assert abs(self.wallet.balances["user1"] - (initial_balance + amount)) < 1e-9
        
        last_tx = self.wallet.transactions[-1]
        assert last_tx["type"] == "debit"
        assert last_tx["user_id"] == "user1"
        assert abs(last_tx["amount"] - amount) < 1e-9
        
    def test_real_time_update_zero_amount(self):
        """Testa atualização com valor zero"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        
        with pytest.raises(AssertionError, match="R2 violated: Amount cannot be zero"):
            self.wallet.real_time_update("user1", 0)
            
    def test_real_time_update_insufficient_balance(self):
        """Testa débito com saldo insuficiente"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 100.0)
        
        with pytest.raises(AssertionError, match="R3 violated: Insufficient balance for debit"):
            self.wallet.real_time_update("user1", -150.0)
            
    def test_real_time_update_negative_balance_result(self):
        """Testa que resulta em saldo negativo"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.add_funds("user1", 50.0)
        
        with pytest.raises(AssertionError, match="R4 violated: Would result in negative balance"):
            self.wallet.real_time_update("user1", -51.0)
            
    # ------------------ TESTES DE INTEGRAÇÃO ------------------
    
    def test_integration_workflow(self):
        """Testa um fluxo completo de integração"""
        # 1. Criação de contas
        self.wallet.create_account("alice", "alice@email.com", "password123")
        self.wallet.create_account("bob", "bob@email.com", "password456")
        
        assert self.wallet.verify_invariants()
        
        # 2. Configuração de PINs
        self.wallet.set_pin("alice", "1234")
        self.wallet.set_pin("bob", "5678")
        
        assert self.wallet.authenticate_pin("alice", "1234")
        assert not self.wallet.authenticate_pin("alice", "wrong")
        
        # 3. Adição de fundos
        self.wallet.add_funds("alice", 1000.0)
        self.wallet.add_funds("bob", 500.0)
        
        assert abs(self.wallet.balances["alice"] - 1000.0) < 1e-9
        assert abs(self.wallet.balances["bob"] - 500.0) < 1e-9
        
        # 4. Transferência
        self.wallet.transfer("alice", "bob", 300.0)
        
        assert abs(self.wallet.balances["alice"] - 700.0) < 1e-9
        assert abs(self.wallet.balances["bob"] - 800.0) < 1e-9
        
        # 5. Saque
        self.wallet.withdraw_funds("bob", "PT500123456789", 200.0)
        assert abs(self.wallet.balances["bob"] - 600.0) < 1e-9
        
        # 6. Aplicação de juros
        self.wallet.apply_interest(0.05)
        
        assert abs(self.wallet.balances["alice"] - 735.0) < 1e-6  # 700 * 1.05
        assert abs(self.wallet.balances["bob"] - 630.0) < 1e-6    # 600 * 1.05
        
        # 7. Configuração de limites
        self.wallet.set_spending_limits("alice", daily=100.0, monthly=1500.0)
        
        limits = self.wallet.spending_limits["alice"]
        assert limits["daily"] == 100.0
        assert limits["monthly"] == 1500.0
        
        # 8. Adição de método de pagamento
        card = {"type": "card", "last4": "4321", "brand": "Mastercard"}
        self.wallet.add_payment_method("alice", card)
        
        methods = self.wallet.get_payment_methods("alice")
        assert len(methods) == 1
        assert methods[0] == card
        
        # 9. Rastreamento de transações
        alice_txs = self.wallet.track_transactions("alice")
        assert len(alice_txs) > 0
        
        # 10. Verificação final de invariantes
        assert self.wallet.verify_invariants()
        
        # Verifica consistência total
        total_balance = sum(self.wallet.balances.values())
        total_transactions = len(self.wallet.transactions)
        
        # Verifica algumas propriedades de segurança
        assert all(b >= 0 for b in self.wallet.balances.values())
        assert all(uid in self.wallet.balances for uid in self.wallet.user_pins.keys())
        assert all(uid in self.wallet.balances for uid in self.wallet.payment_methods.keys())
        
    def test_edge_cases(self):
        """Testa casos de borda"""
        # 1. Usuário com saldo zero
        self.wallet.create_account("zero_user", "zero@email.com", "password123")
        assert self.wallet.balances["zero_user"] == 0.0
        
        # 2. Transação de valor muito pequeno
        self.wallet.create_account("small_user", "small@email.com", "password123")
        self.wallet.add_funds("small_user", 0.01)
        assert abs(self.wallet.balances["small_user"] - 0.01) < 1e-9
        
        # 3. Múltiplas transações rápidas
        self.wallet.create_account("fast_user", "fast@email.com", "password123")
        for i in range(5):
            self.wallet.real_time_update("fast_user", 10.0)
            
        assert abs(self.wallet.balances["fast_user"] - 50.0) < 1e-9
        
        # 4. Verifica que invariantes são mantidos
        assert self.wallet.verify_invariants()
        
    def test_concurrent_operations_simulation(self):
        """Simula operações concorrentes (sem threading real)"""
        self.wallet.create_account("user1", "user1@email.com", "password123")
        self.wallet.create_account("user2", "user2@email.com", "password456")
        
        # Operações sequenciais que simulariam concorrência
        operations = [
            ("add_funds", "user1", 100.0),
            ("add_funds", "user2", 200.0),
            ("transfer", "user1", "user2", 50.0),
            ("real_time_update", "user1", 25.0),
            ("real_time_update", "user2", -10.0),
        ]
        
        for op_name, *args in operations:
            if op_name == "add_funds":
                self.wallet.add_funds