CREATE TABLE IF NOT EXISTS users (
  id BIGINT PRIMARY KEY,
  username TEXT,
  trust_score INT DEFAULT 100 NOT NULL,
  preferred_games TEXT[] DEFAULT '{}'::TEXT[] NOT NULL,
  timezone TEXT,
  join_date TIMESTAMP,
  last_seen TIMESTAMP,
  warning_count INT DEFAULT 0 NOT NULL,
  notes TEXT
);

CREATE TABLE IF NOT EXISTS mod_log (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  action TEXT NOT NULL,
  reason TEXT,
  confidence INT,
  message_content TEXT,
  channel_id BIGINT,
  timestamp TIMESTAMP DEFAULT NOW() NOT NULL,
  mod_override BOOLEAN DEFAULT FALSE NOT NULL
);

CREATE TABLE IF NOT EXISTS memory (
  id SERIAL PRIMARY KEY,
  user_id BIGINT NOT NULL,
  key TEXT NOT NULL,
  value TEXT NOT NULL,
  updated_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS autonomous_posts (
  id SERIAL PRIMARY KEY,
  channel_id BIGINT NOT NULL,
  content_hash TEXT UNIQUE NOT NULL,
  source_url TEXT,
  relevance_score INT,
  posted_at TIMESTAMP DEFAULT NOW() NOT NULL
);

CREATE TABLE IF NOT EXISTS server_events (
  id SERIAL PRIMARY KEY,
  event_type TEXT NOT NULL,
  data JSONB NOT NULL,
  nexus_action TEXT,
  timestamp TIMESTAMP DEFAULT NOW() NOT NULL
);
