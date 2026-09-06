CREATE TYPE account_type AS ENUM ('ASSET', 'LIABILITY', 'EQUITY', 'REVENUE', 'EXPENSE');
CREATE TYPE entry_direction AS ENUM ('DEBIT', 'CREDIT');


CREATE TABLE accounts(

   id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
   holder_id UUID NOT NULL,
   currency  VARCHAR(3) NOT NULL,
   type account_type NOT NULL,
   allow_overdraf BOOLEAN DEFAULT FALSE,
   created_at TIMESTAMPTZ DEFAULT NOW()

);


CREATE TABLE transactions(

   id UUID PRIMARY KEY,
   idempotency_key VARCHAR(64) UNIQUE NOT NULL,
   reference  VARCHAR(128) NOT NULL,
   description TEXT NULL,
   posted_at TIMESTAMPTZ DEFAULT NOW()

);


CREATE TABLE ledger_entries(

id	UUID	Primary Key,
transaction_id	UUID references transactions(id) ON DELETE RESTRICT NOT NULL,
account_id	UUID references transactions(id) ON DELETE RESTRICT NOT NULL,
amount	NUMERIC(18, 4)	NOT NULL, CHECK (amount > 0),
direction	entry_direction	NOT NULL,
currency	VARCHAR(3)	NOT NULL,
created_at	TIMESTAMPTZ	DEFAULT NOW()

);

CREATE INDEX accounts_inx
on accounts (holder_id);

CREATE INDEX ledger_entries_inx
on ledger_entries (transaction_id);

CREATE INDEX ledger_entries_composite_idx
on ledger_entries (account_id, created_at);
