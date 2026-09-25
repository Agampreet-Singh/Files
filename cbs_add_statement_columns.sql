-- ============================================
-- Run this on CBS Server via phpMyAdmin > SQL tab
-- Adds two columns needed for detailed mini-statements:
--   txn_type      - 'withdrawal' or 'deposit'
--   balance_after - the account balance right after this transaction
-- Safe to run once. Existing old rows will show txn_type as NULL
-- (the switch code treats NULL as 'withdrawal' automatically) and
-- balance_after as NULL (shown as "N/A" on the ATM screen).
-- ============================================

ALTER TABLE cosmos_bank.transactions
  ADD COLUMN txn_type VARCHAR(20) NULL AFTER atm_id,
  ADD COLUMN balance_after DECIMAL(14,2) NULL AFTER amount;

-- Verify:
-- DESCRIBE cosmos_bank.transactions;
